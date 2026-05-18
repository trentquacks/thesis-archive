from flask import Blueprint, render_template, g, redirect, url_for, flash
import functools

bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        if g.user['role'] != 'admin':
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for("thesis.index"))
        return view(**kwargs)
    return wrapped_view

@bp.route("/dashboard")
@admin_required
def dashboard():
    return render_template("admin/dashboard.html")
