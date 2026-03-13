import os

from flask import Flask, render_template, request, redirect, session
from werkzeug.security import check_password_hash
from config import db, cursor

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-in-production")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("FLASK_SECURE_COOKIE", "0") == "1",
)

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

# Gallery
@app.route("/gallery")
def gallery():
    return render_template("gallery.html", active_page="gallery")

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

    if "admin_id" not in session:
        return redirect("/admin")

    cursor.execute("SELECT * FROM admissions")

    data = cursor.fetchall()

    return render_template("dashboard.html", data=data, active_page="admin")


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