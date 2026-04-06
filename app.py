import os
from uuid import uuid4

from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from config import db, cursor

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-in-production")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("FLASK_SECURE_COOKIE", "0") == "1",
)

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
GALLERY_UPLOAD_DIR = os.path.join(app.static_folder, "uploads", "gallery")
GALLERY_CATEGORIES = [
    ("computer_labs", "Computer Labs"),
    ("classroom_sessions", "Classroom Sessions"),
    ("cultural_events", "Cultural & Farewell Events"),
    ("national_occasions", "National Occasions"),
    ("parent_teacher_meets", "Parent-Teacher Meets"),
    ("campus_infrastructure", "Campus & Infrastructure"),
]
GALLERY_CATEGORY_LABELS = dict(GALLERY_CATEGORIES)


def _is_admin_logged_in():
    return "admin_id" in session


def _is_allowed_image(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS

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

    cursor.execute(
        """
        SELECT id, title, description, filename, category
        FROM gallery_images
        ORDER BY id DESC
        """
    )
    gallery_images = cursor.fetchall()

    for row in gallery_images:
        category = row[4] or ""
        if category in category_images:
            image_url = url_for("static", filename=f"uploads/gallery/{row[3]}")
            category_images[category].insert(0, image_url)

    return render_template(
        "gallery.html",
        active_page="gallery",
        gallery_images=gallery_images,
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

    query = """
    INSERT INTO admissions
    (name,email,phone,course,message)
    VALUES (?,?,?,?,?)
    """

    cursor.execute(query,(name,email,phone,course,message))
    db.commit()

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

    query = "SELECT id, username, password FROM admin WHERE username=?"

    cursor.execute(query,(username,))

    admin = cursor.fetchone()

    if admin and check_password_hash(admin[2], password):
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

    cursor.execute("SELECT * FROM admissions")

    data = cursor.fetchall()

    cursor.execute(
        """
        SELECT id, title, description, filename, category
        FROM gallery_images
        ORDER BY id DESC
        """
    )
    gallery_images = cursor.fetchall()

    message = request.args.get("msg", "")
    error = request.args.get("err", "")

    return render_template(
        "dashboard.html",
        data=data,
        gallery_images=gallery_images,
        gallery_categories=GALLERY_CATEGORIES,
        category_labels=GALLERY_CATEGORY_LABELS,
        message=message,
        error=error,
        active_page="admin",
    )


@app.route("/admin/gallery/upload", methods=["POST"])
def upload_gallery_image():
    if not _is_admin_logged_in():
        return redirect("/admin")

    images = request.files.getlist("images")  # Get multiple files
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "").strip()

    if category not in GALLERY_CATEGORY_LABELS:
        return redirect(url_for("dashboard", err="Please choose a valid category."))

    if not images or not images[0].filename:
        return redirect(url_for("dashboard", err="Please choose at least one image file."))

    uploaded_count = 0
    for image in images:
        if not image or not image.filename:
            continue

        if not _is_allowed_image(image.filename):
            continue

        try:
            original_name = secure_filename(image.filename)
            ext = os.path.splitext(original_name)[1].lower()
            stored_name = f"{uuid4().hex}{ext}"

            os.makedirs(GALLERY_UPLOAD_DIR, exist_ok=True)
            save_path = os.path.join(GALLERY_UPLOAD_DIR, stored_name)
            image.save(save_path)

            cursor.execute(
                """
                INSERT INTO gallery_images (title, description, filename, category)
                VALUES (?, ?, ?, ?)
                """,
                (title, description, stored_name, category),
            )
            db.commit()
            uploaded_count += 1
        except Exception:
            continue

    if uploaded_count == 0:
        return redirect(url_for("dashboard", err="No valid image files uploaded."))
    
    msg = f"{uploaded_count} image(s) uploaded successfully." if uploaded_count > 1 else "1 image uploaded successfully."
    return redirect(url_for("dashboard", msg=msg))


@app.route("/admin/gallery/delete/<int:image_id>", methods=["POST"])
def delete_gallery_image(image_id):
    if not _is_admin_logged_in():
        return redirect("/admin")

    cursor.execute("SELECT filename FROM gallery_images WHERE id=?", (image_id,))
    row = cursor.fetchone()

    if not row:
        return redirect(url_for("dashboard", err="Image record not found."))

    filename = row[0]
    cursor.execute("DELETE FROM gallery_images WHERE id=?", (image_id,))
    db.commit()

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
            cursor.execute("SELECT filename FROM gallery_images WHERE id=?", (image_id,))
            row = cursor.fetchone()
            
            if row:
                filename = row[0]
                cursor.execute("DELETE FROM gallery_images WHERE id=?", (image_id,))
                db.commit()
                
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

    cursor.execute("SELECT id FROM admissions WHERE id=?", (admission_id,))
    row = cursor.fetchone()

    if not row:
        return redirect(url_for("dashboard", err="Admission record not found."))

    cursor.execute("DELETE FROM admissions WHERE id=?", (admission_id,))
    db.commit()

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