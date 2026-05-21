import functools

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from flaskr.db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = (
            get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        )

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        
        student_no = request.form['student_no']
        course = request.form['course']
        email = request.form['email']
        password = request.form['password']
        
        db = get_db()
        error = None

        if not first_name:
            error = 'First name is required.'
        elif not last_name:
            error = 'Last name is required.'
        elif not student_no:
            error = 'Student number is required.'
        elif not course:
            error = 'Course is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (first_name, last_name, email, password, student_no, course) VALUES (?, ?, ?, ?, ?, ?)",
                    (first_name, last_name, email, generate_password_hash(password), student_no, course),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {email} is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Log in a registered user by adding the user id to the session."""
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        db = get_db()
        error = None
        user = db.execute(
            "SELECT * FROM user WHERE email = ?", (email,)
        ).fetchone()

        if user is None:
            error = "Incorrect email."
        elif not check_password_hash(user["password"], password):
            error = "Incorrect password."

        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            
            db.execute('''
                UPDATE active_borrow 
                SET last_tick = CURRENT_TIMESTAMP, is_paused = 0 
                WHERE user_id = ? AND is_paused = 1
            ''', (user["id"],))
            db.commit()
            
            return redirect(url_for("index"))

        flash(error, "error")

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    user_id = session.get("user_id")
    
    if user_id:
        db = get_db()
        db.execute('''
            UPDATE active_borrow 
            SET time_left = MAX(0, time_left - CAST((strftime('%s', 'now') - strftime('%s', last_tick)) AS INTEGER)),
                is_paused = 1 
            WHERE user_id = ? AND is_paused = 0
        ''', (user_id,))
        db.commit()
        
    session.clear()
    return redirect(url_for("index"))
