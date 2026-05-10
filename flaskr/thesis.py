import os
import uuid
from datetime import datetime
from flask import Blueprint, flash, g, redirect, render_template, request, url_for, session
from werkzeug.utils import secure_filename
from werkzeug.exceptions import abort
from .db import get_db

bp = Blueprint("thesis", __name__)

@bp.route("/", methods=["GET", "POST"])
def index():
    """Show all the theses"""
    db = get_db()

    departments = db.execute(
        "SELECT id, name, icon, description FROM department"
    ).fetchall()

    return render_template("thesis/index.html", departments=departments)

@bp.route("/search", methods=["GET"])
@bp.route("/search/<int:dept_id>", methods=["GET", "POST"])
def search(dept_id=None):
    """Handles global searches, department filtering, and sorting."""
    db = get_db()

    search_term = request.args.get("q", "").strip()
    sort = request.args.get('sort', 'newest')
    year = request.args.get('year', '')

    query = """
        SELECT thesis.id, thesis.title, thesis.date_published, thesis.file_path,
               department.name AS department_name, department.icon, department.description,
               GROUP_CONCAT(author.first_name || ' ' || author.last_name, ', ') AS authors 
        FROM thesis 
        JOIN thesis_author ON thesis.id = thesis_author.thesis_id 
        JOIN author ON thesis_author.author_id = author.id 
        JOIN department ON thesis.department_id = department.id 
        WHERE 1=1
    """
    params = []
    department_info = None

    if dept_id is not None:
        query += " AND thesis.department_id = ?"
        params.append(dept_id)
        
        department_info = db.execute(
            "SELECT id, name, description, icon FROM department WHERE id = ?", 
            (dept_id,)
        ).fetchone()
        
        if department_info is None:
            abort(404, f"Department ID {dept_id} doesn't exist.")
            
    else:
        department_info = {
            "id": None,
            "name": "All Collections", 
            "icon": "fa-globe", 
            "description": f"Showing global search results for '{search_term}'" if search_term else "All Collections"
        }

    if search_term:
        query += """ 
            AND (thesis.title LIKE '%' || ? || '%' 
            OR thesis.abstract LIKE '%' || ? || '%' 
            OR author.first_name LIKE '%' || ? || '%' 
            OR author.last_name LIKE '%' || ? || '%')
        """
        params.extend([search_term, search_term, search_term, search_term])

    if year:
        query += " AND strftime('%Y', thesis.date_published) = ?"
        params.append(year)

    query += " GROUP BY thesis.id"

    if sort == 'az':
        query += " ORDER BY thesis.title ASC"
    elif sort == 'za':
        query += " ORDER BY thesis.title DESC"
    elif sort == 'oldest':
        query += " ORDER BY thesis.date_published ASC"
    else:
        query += " ORDER BY thesis.date_published DESC"

    theses = db.execute(query, params).fetchall()
    count = len(theses)

    return render_template(
        "thesis/result.html", 
        theses=theses, 
        departments=department_info, 
        count=count, 
        current_sort=sort, 
        current_year=year,
        search=search_term
    )

@bp.route("/dashboard")
def dashboard():
    db = get_db()
    current_user_id = session['user_id']
    theses = db.execute("""
        SELECT thesis.id, title, status, strftime('%Y', thesis.date_published) as year, department.icon 
        FROM thesis 
        JOIN department ON thesis.department_id = department.id
        WHERE uploader_id = ?
        ORDER BY thesis.date_published DESC
    """, (current_user_id,)).fetchall()

    total_projects = len(theses)
    under_review = sum(1 for t in theses if t['status'] == 'pending')
    approved = sum(1 for t in theses if t['status'] == 'approved')
    return render_template("thesis/dashboard.html", 
        theses=theses,
        total_projects=total_projects,
        under_review=under_review,
        approved=approved
        )

@bp.route("/form")
def form():
    db = get_db()
    programs = db.execute("SELECT id, name FROM department").fetchall()
    formats = db.execute("SELECT id, format FROM format").fetchall()
    branches = db.execute("SELECT id, name FROM branch").fetchall()
    return render_template("thesis/form.html", programs=programs, formats=formats, branches=branches)

@bp.route("/submit-thesis", methods=["POST"])
def submit_thesis():
    db = get_db()

    date_published = request.form.get('date')

    if date_published:
        upload_year = str(date_published)[:4]
    else:
        upload_year = str(datetime.now().year)


    file = request.files['file']
    save_directory = os.path.join(bp.root_path, 'static', 'uploads',upload_year)
    os.makedirs(save_directory, exist_ok=True) 
    
    actual_save_path = os.path.join(save_directory, file.filename)
    file.save(actual_save_path) 
    file_path = f"/static/uploads/{upload_year}/{file.filename}"

    first_name = request.form.get('author_first_name')
    middle_name = request.form.get('author_middle_name')
    last_name = request.form.get('author_last_name')
    student_no = request.form.get('student_number')
    title = request.form.get('title')
    abstract = request.form.get('abstract')
    keywords = request.form.get('keywords')
    department_id = request.form.get('program')
    format_id = request.form.get('format')
    branch_id = request.form.get('branch')
    uploader_id = session.get('user_id')

    temp_barcode = f"PENDING-BC-{uuid.uuid4().hex[:8].upper()}"
    temp_call_num = f"PENDING-CN-{uuid.uuid4().hex[:8].upper()}"

    try:
        author = db.execute("SELECT id FROM author WHERE student_no = ?", (student_no,)).fetchone()
        if author:
            author_id = author['id']
        else:
            query = db.execute(
                    "INSERT INTO author (first_name, middle_name, last_name, student_no) VALUES (?, ?, ?, ?)",
                    (first_name, middle_name, last_name, student_no)
                    )
            author_id = query.lastrowid

        query = db.execute("""
            INSERT INTO thesis (
                title, abstract, keywords, file_path, status, barcode, call_number, 
                department_id, branch_id, format_id, uploader_id, date_published
            ) VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?)
        """, (title, abstract, keywords, file_path, temp_barcode, temp_call_num, 
              department_id, branch_id, format_id, uploader_id, date_published))

        thesis_id = query.lastrowid

        db.execute(
                "INSERT INTO thesis_author (thesis_id, author_id) VALUES (?, ?)",
                (thesis_id, author_id)
                )

        db.commit()
        flash('Thesis submitted successfully and is pending approval!', 'success')
        print("SUCCESS")

    except Exception as e:
            db.rollback() 
            flash(f"An error occurred while saving: {str(e)}", 'error')
            if os.path.exists(file_path):
                os.remove(file_path)
            print("FAILED")

    return redirect(url_for('thesis.dashboard'))

@bp.route("/view/<int:id>")
def view(id):
    db = get_db()

    query = """
        SELECT 
            t.id, t.title, t.abstract, t.keywords, t.file_path, t.call_number, t.barcode,
            strftime('%Y', t.date_published) AS year,
            d.name AS department_name, d.description AS program_name, d.id as department_id, d.icon,
            f.format AS document_type,
            GROUP_CONCAT(a.first_name || ' ' || a.last_name, ', ') AS authors,
            GROUP_CONCAT(a.last_name || ', ' || SUBSTR(a.first_name, 1, 1) || '.', ', ') AS citation_authors
        FROM thesis t
        JOIN department d ON t.department_id = d.id
        LEFT JOIN format f ON t.format_id = f.id
        LEFT JOIN thesis_author ta ON t.id = ta.thesis_id
        LEFT JOIN author a ON ta.author_id = a.id
        WHERE t.id = ?
        GROUP BY t.id
    """
    
    thesis = db.execute(query, (id,)).fetchone()

    if thesis is None:
        abort(404, f"Thesis ID {id} doesn't exist.")

    citation = f"{thesis['citation_authors']} ({thesis['year']}). {thesis['title']}."

    return render_template("thesis/view.html", thesis=thesis, citation=citation)
