from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort
from .db import get_db

bp = Blueprint("thesis", __name__)

@bp.route("/", methods=["GET", "POST"])
def index():
    """Show all the theses"""
    db = get_db()
    
    search = request.form.get("search") or request.args.get("search", "")
    sort = request.args.get('sort', 'newest')
    year = request.args.get('year', '')

    if search or request.method == "POST":
        category = "All"
        
        query = """
            SELECT thesis.id, thesis.title, thesis.date_published, 
                   department.name AS department_name, 
                   GROUP_CONCAT(author.first_name || ' ' || author.last_name, ', ') AS authors 
            FROM thesis 
            JOIN thesis_author ON thesis.id = thesis_author.thesis_id 
            JOIN author ON thesis_author.author_id = author.id 
            JOIN department ON thesis.department_id = department.id 
            WHERE (thesis.title LIKE '%' || ? || '%' 
               OR thesis.abstract LIKE '%' || ? || '%' 
               OR author.first_name LIKE '%' || ? || '%' 
               OR author.last_name LIKE '%' || ? || '%')
        """
        params = [search, search, search, search]

        if year:
            query += " AND strftime('%Y', thesis.date_published) = ?"
            params.append(year)

        query += " GROUP BY thesis.id"

        if sort == 'az':
            query += " ORDER BY thesis.title ASC;"
        else:
            query += " ORDER BY thesis.date_published DESC;" # Default to newest

        theses = db.execute(query, params).fetchall()
        count = len(theses)
        
        return render_template("thesis/result.html", theses=theses, search=search, category=category, count=count, current_sort=sort, current_year=year)
    
    return render_template("thesis/index.html")

@bp.route("/department/<int:dept_id>")
def department_theses(dept_id):
    db = get_db()
    
    # Grab URL parameters
    sort = request.args.get('sort', 'newest')
    year = request.args.get('year', '')
    
    department = db.execute(
        "SELECT name, description FROM department WHERE id = ?", 
        (dept_id,)
    ).fetchone()

    if department is None:
        abort(404, f"Department ID {dept_id} doesn't exist.")

    # Base Query
    query = """
        SELECT thesis.id, thesis.title, thesis.date_published, 
               department.name AS department_name, department.description, 
               GROUP_CONCAT(author.first_name || ' ' || author.last_name, ', ') AS authors 
        FROM thesis 
        JOIN thesis_author ON thesis.id = thesis_author.thesis_id 
        JOIN author ON thesis_author.author_id = author.id 
        JOIN department ON thesis.department_id = department.id 
        WHERE thesis.department_id = ?
    """
    params = [dept_id]

    # Apply Year Filter if selected
    if year:
        query += " AND strftime('%Y', thesis.date_published) = ?"
        params.append(year)

    query += " GROUP BY thesis.id"

    # Apply Sorting
    if sort == 'az':
        query += " ORDER BY thesis.title ASC;"
    else:
        query += " ORDER BY thesis.date_published DESC;"

    theses = db.execute(query, params).fetchall()
    count = len(theses)

    return render_template(
        "thesis/result.html", 
        theses=theses, 
        category=department['name'], 
        description=department['description'], 
        count=count, 
        current_sort=sort, 
        current_year=year
    )
