from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

from .auth import login_required
from .db import get_db

bp = Blueprint("thesis", __name__)


@bp.route("/", methods=["GET", "POST"])
def index():
    """Show all the theses"""
    if request.method == "POST":
        db = get_db()
        search = request.form["search"]
        # theses = db.execute(
        #     "SELECT " 
        #         "thesis.title," 
        #         "author.first_name," 
        #         "author.last_name,"
        #         "author.student_no "
        #     "FROM thesis "
        #     "JOIN thesis_author ON thesis.id = thesis_author.thesis_id "
        #     "JOIN author ON thesis_author.author_id = author.id "
        #     "WHERE thesis.title LIKE '%' || ? || '%';"
        #     , (search,)).fetchall()
        theses = db.execute(
        "SELECT "
            "thesis.id, "
            "thesis.title, "
            "thesis.date_published, "
            "department.name AS department_name, "
        "GROUP_CONCAT(author.first_name || ' ' || author.last_name, ', ') AS authors "
        "FROM thesis "
            "JOIN thesis_author ON thesis.id = thesis_author.thesis_id "
            "JOIN author ON thesis_author.author_id = author.id "
            "JOIN department ON thesis.department_id = department.id "
        "WHERE thesis.title LIKE '%' || ? || '%' "
            "OR thesis.abstract LIKE '%' || ? || '%' "
            "OR author.first_name LIKE '%' || ? || '%' "
            "OR author.last_name LIKE '%' || ? || '%' "
        "GROUP BY thesis.id;",
        (search, search, search, search)
        ).fetchall()
        return render_template("thesis/result.html", theses=theses, search=search)
    return render_template("thesis/index.html")

@bp.route("/department/<int:dept_id>")
def department_theses(dept_id):
    db = get_db()
    
    department = db.execute(
        "SELECT name FROM department WHERE id = ?", 
        (dept_id,)
    ).fetchone()

    if department is None:
        abort(404, f"Department ID {dept_id} doesn't exist.")

    theses = db.execute(
        "SELECT "
            "thesis.id, "
            "thesis.title, "
            "thesis.date_published, "
            "department.name AS department_name, "
            "GROUP_CONCAT(author.first_name || ' ' || author.last_name, ', ') AS authors "
        "FROM thesis "
        "JOIN thesis_author ON thesis.id = thesis_author.thesis_id "
        "JOIN author ON thesis_author.author_id = author.id "
        "JOIN department ON thesis.department_id = department.id "
        "WHERE thesis.department_id = ? "
        "GROUP BY thesis.id "
        "ORDER BY thesis.date_added DESC;", # Show the newest submissions first
        (dept_id,)
    ).fetchall()

    # Pass both the list of theses and the specific department name to the template
    return render_template("thesis/result.html", theses=theses, department_name=department['name'])

#
# def get_post(id, check_author=True):
#     """Get a post and its author by id.
#
#     Checks that the id exists and optionally that the current user is
#     the author.
#
#     :param id: id of post to get
#     :param check_author: require the current user to be the author
#     :return: the post with author information
#     :raise 404: if a post with the given id doesn't exist
#     :raise 403: if the current user isn't the author
#     """
#     post = (
#         get_db()
#         .execute(
#             "SELECT p.id, title, body, created, author_id, email"
#             " FROM post p JOIN user u ON p.author_id = u.id"
#             " WHERE p.id = ?",
#             (id,),
#         )
#         .fetchone()
#     )
#
#     if post is None:
#         abort(404, f"Post id {id} doesn't exist.")
#
#     if check_author and post["author_id"] != g.user["id"]:
#         abort(403)
#
#     return post
#
#
# @bp.route("/create", methods=("GET", "POST"))
# @login_required
# def create():
#     """Create a new post for the current user."""
#     if request.method == "POST":
#         title = request.form["title"]
#         body = request.form["body"]
#         error = None
#
#         if not title:
#             error = "Title is required."
#
#         if error is not None:
#             flash(error)
#         else:
#             db = get_db()
#             db.execute(
#                 "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
#                 (title, body, g.user["id"]),
#             )
#             db.commit()
#             return redirect(url_for("thesis.index"))
#
#     return render_template("thesis/create.html")


# @bp.route("/<int:id>/update", methods=("GET", "POST"))
# @login_required
# def update(id):
#     """Update a post if the current user is the author."""
#     post = get_post(id)
#
#     if request.method == "POST":
#         title = request.form["title"]
#         body = request.form["body"]
#         error = None
#
#         if not title:
#             error = "Title is required."
#
#         if error is not None:
#             flash(error)
#         else:
#             db = get_db()
#             db.execute(
#                 "UPDATE post SET title = ?, body = ? WHERE id = ?", (title, body, id)
#             )
#             db.commit()
#             return redirect(url_for("thesis.index"))
#
#     return render_template("thesis/update.html", post=post)
#
#
# @bp.route("/<int:id>/delete", methods=("POST",))
# @login_required
# def delete(id):
#     """Delete a post.
#
#     Ensures that the post exists and that the logged in user is the
#     author of the post.
#     """
#     get_post(id)
#     db = get_db()
#     db.execute("DELETE FROM post WHERE id = ?", (id,))
#     db.commit()
#     return redirect(url_for("thesis.index"))
