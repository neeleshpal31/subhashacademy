import os
import mimetypes
import traceback
from io import BytesIO
from uuid import uuid4

from flask import Flask, Response, jsonify, render_template, request, redirect, session, url_for
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.security import check_password_hash
from PIL import Image, ImageOps, UnidentifiedImageError
import config

db = config.db
cursor = config.cursor

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-in-production")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("FLASK_SECURE_COOKIE", "0") == "1",
)

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
GALLERY_UPLOAD_DIR = os.path.join(app.static_folder, "uploads", "gallery")
MAX_GALLERY_FILES_PER_REQUEST = int(os.getenv("MAX_GALLERY_FILES_PER_REQUEST", "100"))
MAX_GALLERY_TOTAL_BYTES = int(os.getenv("MAX_GALLERY_TOTAL_BYTES", str(20 * 1024 * 1024)))
MAX_GALLERY_FILE_BYTES = int(os.getenv("MAX_GALLERY_FILE_BYTES", str(15 * 1024 * 1024)))
# Keep hosted uploads stable by using conservative batch defaults.
MAX_GALLERY_BATCH_FILES = int(os.getenv("MAX_GALLERY_BATCH_FILES", "1"))
MAX_GALLERY_BATCH_MB = int(os.getenv("MAX_GALLERY_BATCH_MB", "6"))
MAX_GALLERY_IMAGE_DIMENSION = int(os.getenv("MAX_GALLERY_IMAGE_DIMENSION", "1920"))
MAX_GALLERY_IMAGE_PIXELS = int(os.getenv("MAX_GALLERY_IMAGE_PIXELS", str(80 * 1000 * 1000)))
MAX_GALLERY_JPEG_QUALITY = max(40, min(95, int(os.getenv("MAX_GALLERY_JPEG_QUALITY", "78"))))
MAX_GALLERY_WEBP_QUALITY = max(40, min(95, int(os.getenv("MAX_GALLERY_WEBP_QUALITY", "76"))))
MAX_GALLERY_TOTAL_MB = max(1, MAX_GALLERY_TOTAL_BYTES // (1024 * 1024))
MAX_GALLERY_FILE_MB = max(1, MAX_GALLERY_FILE_BYTES // (1024 * 1024))
GALLERY_CATEGORIES = [
    ("computer_labs", "Computer Labs"),
    ("classroom_sessions", "Classroom Sessions"),
    ("cultural_events", "Cultural & Farewell Events"),
    ("national_occasions", "National Occasions"),
    ("parent_teacher_meets", "Parent-Teacher Meets"),
    ("campus_infrastructure", "Campus & Infrastructure"),
]
GALLERY_CATEGORY_LABELS = dict(GALLERY_CATEGORIES)
app.config["MAX_CONTENT_LENGTH"] = MAX_GALLERY_TOTAL_BYTES
os.makedirs(GALLERY_UPLOAD_DIR, exist_ok=True)


def _is_remote_gallery_ref(value):
    if not value:
        return False
    return value.startswith("http://") or value.startswith("https://")


def _build_gallery_image_url(image_id, filename, has_blob):
    if has_blob:
        return url_for("gallery_image_blob", image_id=image_id)
    if _is_remote_gallery_ref(filename):
        return filename
    local_path = os.path.join(GALLERY_UPLOAD_DIR, filename or "")
    if filename and os.path.exists(local_path):
        return url_for("static", filename=f"uploads/gallery/{filename}")
    # Fallback for legacy rows where file path exists in DB but file is unavailable on server disk.
    return url_for("static", filename="college-bg1.jpeg")


def _is_admin_logged_in():
    return "admin_id" in session


def _is_allowed_image(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


def _get_uploaded_file_size(file_storage):
    try:
        file_storage.stream.seek(0, os.SEEK_END)
        size = file_storage.stream.tell()
        file_storage.stream.seek(0)
        return size
    except Exception:
        return 0


def _get_lanczos_filter():
    if hasattr(Image, "Resampling"):
        return Image.Resampling.LANCZOS
    return Image.LANCZOS


def _optimize_gallery_image(raw_bytes, original_filename):
    try:
        with Image.open(BytesIO(raw_bytes)) as source_image:
            width, height = source_image.size
            if width <= 0 or height <= 0:
                return None, None, None, "invalid"
            if (width * height) > MAX_GALLERY_IMAGE_PIXELS:
                return None, None, None, "pixels"

            image = ImageOps.exif_transpose(source_image)
            max_dimension = max(image.size)
            if max_dimension > MAX_GALLERY_IMAGE_DIMENSION:
                image.thumbnail((MAX_GALLERY_IMAGE_DIMENSION, MAX_GALLERY_IMAGE_DIMENSION), _get_lanczos_filter())

            ext = os.path.splitext(original_filename or "")[1].lower()
            has_alpha = "A" in image.getbands()
            out_stream = BytesIO()

            if ext == ".png" and has_alpha:
                # Transparent PNGs can remain very heavy; WEBP keeps alpha with much smaller payload.
                image.convert("RGBA").save(out_stream, format="WEBP", quality=MAX_GALLERY_WEBP_QUALITY, method=6)
                return out_stream.getvalue(), "image/webp", ".webp", "ok"

            if ext == ".webp":
                target = image.convert("RGBA") if has_alpha else image.convert("RGB")
                target.save(out_stream, format="WEBP", quality=MAX_GALLERY_WEBP_QUALITY, method=6)
                return out_stream.getvalue(), "image/webp", ".webp", "ok"

            # Default to JPEG for smaller file sizes and broad compatibility.
            image.convert("RGB").save(
                out_stream,
                format="JPEG",
                quality=MAX_GALLERY_JPEG_QUALITY,
                optimize=True,
                progressive=True,
            )
            return out_stream.getvalue(), "image/jpeg", ".jpg", "ok"
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        return None, None, None, "invalid"


def _ensure_db_connection():
    global db, cursor

    try:
        if db is None or getattr(db, "closed", 1) != 0:
            config.db = config._connect()
            db = config.db
            cursor = db.cursor()
            config.cursor = cursor
        return db
    except Exception as exc:
        print(f"Database reconnect failed: {exc}")
        raise


def _safe_rollback(connection):
    try:
        if connection is not None and getattr(connection, "closed", 1) == 0:
            connection.rollback()
    except Exception:
        pass


def _fetch_all_safe(query, params=None):
    connection = None
    try:
        connection = _ensure_db_connection()
        with connection.cursor() as local_cursor:
            local_cursor.execute(query, params or ())
            return local_cursor.fetchall()
    except Exception as exc:
        _safe_rollback(connection)
        print(f"Database query failed: {exc}")
        return []


def _fetch_one_safe(query, params=None):
    connection = None
    try:
        connection = _ensure_db_connection()
        with connection.cursor() as local_cursor:
            local_cursor.execute(query, params or ())
            return local_cursor.fetchone()
    except Exception as exc:
        _safe_rollback(connection)
        print(f"Database query failed: {exc}")
        return None


def _execute_write_safe(query, params=None):
    connection = None
    try:
        connection = _ensure_db_connection()
        with connection.cursor() as local_cursor:
            local_cursor.execute(query, params or ())
        connection.commit()
        return True
    except Exception as exc:
        _safe_rollback(connection)
        print(f"Database write failed: {exc}")
        return False


def _verify_admin_password(admin_id, stored_password, raw_password):
    if not stored_password:
        return False

    is_valid = False
    try:
        is_valid = check_password_hash(stored_password, raw_password)
    except ValueError:
        # Supports legacy plain-text or non-werkzeug hash values without crashing login.
        is_valid = stored_password == raw_password

    if (not is_valid) and stored_password == raw_password:
        is_valid = True

    return is_valid


@app.errorhandler(RequestEntityTooLarge)
def handle_large_upload(_error):
    if _is_admin_logged_in():
        return redirect(url_for("dashboard", err="Upload size is too large. Please upload smaller batches."))
    return "Upload payload too large", 413


@app.route("/media/gallery/<int:image_id>")
def gallery_image_blob(image_id):
    row = _fetch_one_safe(
        """
        SELECT filename, mime_type, image_data
        FROM gallery_images
        WHERE id=%s
        """,
        (image_id,)
    )
    if not row or row[2] is None:
        return "Image not found", 404

    image_data = row[2].tobytes() if isinstance(row[2], memoryview) else row[2]
    mime_type = row[1] or mimetypes.guess_type(row[0] or "")[0] or "application/octet-stream"
    return Response(image_data, mimetype=mime_type)


@app.route("/health")
@app.route("/healthz")
def health_check():
    return jsonify(status="ok"), 200

# Home
@app.route("/")
def home():
    return render_template("index.html", active_page="home")

# About
@app.route("/about")
def about():
    return render_template("about.html", active_page="about")

# Courses
@app.route("/courses")
def courses():
    return render_template("courses.html", active_page="courses")

# Library
@app.route("/library")
@app.route("/library/")
@app.route("/library.html")
@app.route("/lab")
@app.route("/lab/")
@app.route("/lab.html")
def library():
    return render_template("library.html", active_page="library")

# Faculty & Staff
@app.route("/faculty")
def faculty():
    return render_template("faculty.html", active_page="faculty")

# Gallery
@app.route("/gallery")
def gallery():
    default_category_images = {
        "computer_labs": [
            url_for("static", filename="lab.jpeg"),
            url_for("static", filename="college-bg1.jpeg"),
            url_for("static", filename="library.jpg.jpeg"),
        ],
        "classroom_sessions": [
            url_for("static", filename="college-bg1.jpeg"),
            url_for("static", filename="lab.jpeg"),
            url_for("static", filename="director sir.jpeg"),
        ],
        "cultural_events": [
            url_for("static", filename="uploads/gallery/a9edcdcda31144d59248349cc8ef819f.jpg"),
            url_for("static", filename="college-bg1.jpeg"),
            url_for("static", filename="director.jpeg"),
        ],
        "national_occasions": [
            url_for("static", filename="college-bg1.jpeg"),
            url_for("static", filename="logo.jpg"),
            url_for("static", filename="AICTE LOGO.png"),
        ],
        "parent_teacher_meets": [
            url_for("static", filename="director sir.jpeg"),
            url_for("static", filename="khan sir.jpeg"),
            url_for("static", filename="mayank sir.jpeg"),
        ],
        "campus_infrastructure": [
            url_for("static", filename="college-bg1.jpeg"),
            url_for("static", filename="library.jpg.jpeg"),
            url_for("static", filename="lab.jpeg"),
        ],
    }

    category_images = {k: list(v) for k, v in default_category_images.items()}

    gallery_images = _fetch_all_safe(
        """
        SELECT id, title, description, filename, category, (image_data IS NOT NULL) AS has_blob
        FROM gallery_images
        ORDER BY id DESC
        """
    )
    image_urls = {}

    for row in gallery_images:
        category = row[4] or ""
        image_url = _build_gallery_image_url(row[0], row[3], row[5])
        image_urls[row[0]] = image_url
        if category in category_images:
            category_images[category].insert(0, image_url)

    return render_template(
        "gallery.html",
        active_page="gallery",
        gallery_images=gallery_images,
        image_urls=image_urls,
        category_images=category_images,
    )

# Contact
@app.route("/contact")
def contact():
    return render_template("contact.html", active_page="contact")

# Admission Page
@app.route("/admission")
def admission():
    return render_template("admission.html", active_page="admission")


# Admission Form Submit
@app.route("/submit", methods=["POST"])
def submit():

    name = request.form["name"].strip()
    email = request.form["email"].strip()
    phone = request.form["phone"].strip()
    course = request.form["course"].strip()
    message = request.form["message"].strip()

    if not name or not email or not phone or not course:
        return render_template(
            "admission.html",
            error="Please fill all required fields.",
            active_page="admission",
        )

    saved = _execute_write_safe(
        """
        INSERT INTO admissions
        (name,email,phone,course,message)
        VALUES (%s,%s,%s,%s,%s)
        """,
        (name, email, phone, course, message),
    )

    if not saved:
        return render_template(
            "admission.html",
            error="Submission failed due to a temporary server issue. Please try again.",
            active_page="admission",
        )

    return render_template("success.html", active_page="admission")


# Admin Login Page
@app.route("/admin")
def admin():
    return render_template("admin_login.html", active_page="admin")


# Admin Login
@app.route("/adminlogin", methods=["POST"])
def adminlogin():

    username = request.form["username"].strip()
    password = request.form["password"]

    admin = _fetch_one_safe(
        "SELECT id, username, password FROM admin WHERE username=%s",
        (username,),
    )

    if admin and _verify_admin_password(admin[0], admin[2], password):
        session["admin_id"] = admin[0]
        session["admin_username"] = admin[1]
        return redirect("/dashboard")
    else:
        return render_template("admin_login.html", error="Invalid username or password", active_page="admin")


# Admin Dashboard
@app.route("/dashboard")
def dashboard():

    if not _is_admin_logged_in():
        return redirect("/admin")

    data = _fetch_all_safe("SELECT * FROM admissions")

    gallery_images = _fetch_all_safe(
        """
        SELECT id, title, description, filename, category, (image_data IS NOT NULL) AS has_blob
        FROM gallery_images
        ORDER BY id DESC
        """
    )
    image_urls = {
        row[0]: _build_gallery_image_url(row[0], row[3], row[5]) for row in gallery_images
    }

    message = request.args.get("msg", "")
    error = request.args.get("err", "")

    return render_template(
        "dashboard.html",
        data=data,
        gallery_images=gallery_images,
        image_urls=image_urls,
        gallery_categories=GALLERY_CATEGORIES,
        category_labels=GALLERY_CATEGORY_LABELS,
        gallery_limit_count=MAX_GALLERY_FILES_PER_REQUEST,
        gallery_batch_size=MAX_GALLERY_BATCH_FILES,
        gallery_batch_target_mb=MAX_GALLERY_BATCH_MB,
        gallery_limit_total_mb=MAX_GALLERY_TOTAL_MB,
        gallery_limit_file_mb=MAX_GALLERY_FILE_MB,
        gallery_limit_file_bytes=MAX_GALLERY_FILE_BYTES,
        message=message,
        error=error,
        active_page="admin",
    )


def _process_gallery_upload(images, title, description, category):
    if category not in GALLERY_CATEGORY_LABELS:
        return {
            "ok": False,
            "error": "Please choose a valid category.",
            "status": 400,
        }

    if not images or not images[0].filename:
        return {
            "ok": False,
            "error": "Please choose at least one image file.",
            "status": 400,
        }

    uploaded_count = 0
    invalid_files = 0
    skipped_pixel_limit = 0
    skipped_size_limit = 0
    for image in images:
        if not image or not image.filename:
            continue

        if not _is_allowed_image(image.filename):
            invalid_files += 1
            continue

        try:
            image_bytes = image.read()
            if not image_bytes:
                invalid_files += 1
                continue

            optimized_bytes, mime_type, optimized_ext, optimize_state = _optimize_gallery_image(image_bytes, image.filename)
            if not optimized_bytes:
                if optimize_state == "pixels":
                    skipped_pixel_limit += 1
                invalid_files += 1
                continue

            if MAX_GALLERY_FILE_BYTES > 0 and len(optimized_bytes) > MAX_GALLERY_FILE_BYTES:
                skipped_size_limit += 1
                invalid_files += 1
                continue

            stored_name = f"{uuid4().hex}{optimized_ext}"
            mime_type = mime_type or (image.mimetype or "").strip() or mimetypes.guess_type(stored_name)[0] or "application/octet-stream"

            saved = _execute_write_safe(
                """
                INSERT INTO gallery_images (title, description, filename, category, image_data, mime_type)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (title, description, stored_name, category, optimized_bytes, mime_type),
            )
            if saved:
                uploaded_count += 1
        except Exception as file_exc:
            print(f"Gallery upload failed for file '{getattr(image, 'filename', 'unknown')}': {file_exc}")
            print(traceback.format_exc())
            continue

    if uploaded_count == 0:
        reason_parts = []
        if skipped_size_limit > 0:
            reason_parts.append(f"{skipped_size_limit} file(s) are still too large after compression")
        if skipped_pixel_limit > 0:
            reason_parts.append(f"{skipped_pixel_limit} file(s) exceed allowed resolution")
        reason_hint = f" ({'; '.join(reason_parts)})" if reason_parts else ""
        return {
            "ok": False,
            "error": f"No valid image files uploaded{reason_hint}. Please upload clear JPG/PNG/WEBP images.",
            "status": 400,
        }

    msg = f"{uploaded_count} image(s) uploaded successfully." if uploaded_count > 1 else "1 image uploaded successfully."
    if invalid_files > 0:
        msg = f"{msg} {invalid_files} file(s) were skipped (invalid/corrupt/unsupported)."

    return {
        "ok": True,
        "message": msg,
        "uploaded_count": uploaded_count,
        "invalid_files": invalid_files,
        "status": 200,
    }


@app.route("/admin/gallery/upload", methods=["POST"])
def upload_gallery_image():
    if not _is_admin_logged_in():
        return redirect("/admin")

    try:
        images = request.files.getlist("images")
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        result = _process_gallery_upload(images, title, description, category)
        if result["ok"]:
            return redirect(url_for("dashboard", msg=result["message"]))
        return redirect(url_for("dashboard", err=result["error"]))
    except RequestEntityTooLarge:
        return redirect(
            url_for(
                "dashboard",
                err=f"Upload payload exceeded server limit (~{MAX_GALLERY_TOTAL_MB}MB per request). Please retry; batching will continue automatically.",
            )
        )
    except Exception as exc:
        print(f"Gallery upload route error: {exc}")
        print(traceback.format_exc())
        return redirect(url_for("dashboard", err="Upload failed due to a server issue. Please try again."))


@app.route("/admin/gallery/upload-json", methods=["POST"])
def upload_gallery_image_json():
    if not _is_admin_logged_in():
        return jsonify(ok=False, error="Unauthorized"), 401

    try:
        images = request.files.getlist("images")
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()

        result = _process_gallery_upload(images, title, description, category)
        status_code = result.pop("status", 200)
        return jsonify(result), status_code
    except RequestEntityTooLarge:
        return (
            jsonify(
                ok=False,
                error=f"Upload payload exceeded server limit (~{MAX_GALLERY_TOTAL_MB}MB per request).",
            ),
            413,
        )
    except Exception as exc:
        print(f"Gallery JSON upload route error: {exc}")
        print(traceback.format_exc())
        return jsonify(ok=False, error="Upload failed due to a server issue. Please try again."), 500


@app.route("/admin/gallery/delete/<int:image_id>", methods=["POST"])
def delete_gallery_image(image_id):
    if not _is_admin_logged_in():
        return redirect("/admin")

    row = _fetch_one_safe(
        "SELECT filename, (image_data IS NOT NULL) FROM gallery_images WHERE id=%s",
        (image_id,),
    )

    if not row:
        return redirect(url_for("dashboard", err="Image record not found."))

    filename = row[0]
    has_blob = bool(row[1])
    deleted = _execute_write_safe("DELETE FROM gallery_images WHERE id=%s", (image_id,))
    if not deleted:
        return redirect(url_for("dashboard", err="Unable to delete image right now."))

    if (not has_blob) and (not _is_remote_gallery_ref(filename)):
        image_path = os.path.join(GALLERY_UPLOAD_DIR, filename)
        if os.path.exists(image_path):
            os.remove(image_path)

    return redirect(url_for("dashboard", msg="Image deleted successfully."))


@app.route("/admin/gallery/bulk-delete", methods=["POST"])
def bulk_delete_gallery_images():
    if not _is_admin_logged_in():
        return redirect("/admin")

    image_ids = request.form.getlist("image_ids")
    
    if not image_ids:
        return redirect(url_for("dashboard", err="No images selected for deletion."))

    deleted_count = 0
    for image_id in image_ids:
        try:
            row = _fetch_one_safe(
                "SELECT filename, (image_data IS NOT NULL) FROM gallery_images WHERE id=%s",
                (image_id,),
            )
            
            if row:
                filename = row[0]
                has_blob = bool(row[1])
                deleted = _execute_write_safe("DELETE FROM gallery_images WHERE id=%s", (image_id,))
                if not deleted:
                    continue

                if (not has_blob) and (not _is_remote_gallery_ref(filename)):
                    image_path = os.path.join(GALLERY_UPLOAD_DIR, filename)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                
                deleted_count += 1
        except Exception as e:
            print(f"Error deleting image {image_id}: {str(e)}")
            continue

    msg = f"{deleted_count} image(s) deleted successfully." if deleted_count > 1 else f"{deleted_count} image deleted successfully."
    return redirect(url_for("dashboard", msg=msg))


@app.route("/admin/admissions/delete/<int:admission_id>", methods=["POST"])
def delete_admission(admission_id):
    if not _is_admin_logged_in():
        return redirect("/admin")

    row = _fetch_one_safe("SELECT id FROM admissions WHERE id=%s", (admission_id,))

    if not row:
        return redirect(url_for("dashboard", err="Admission record not found."))

    deleted = _execute_write_safe("DELETE FROM admissions WHERE id=%s", (admission_id,))
    if not deleted:
        return redirect(url_for("dashboard", err="Unable to delete admission right now."))

    return redirect(url_for("dashboard", msg="Admission record deleted successfully."))


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/admin")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )