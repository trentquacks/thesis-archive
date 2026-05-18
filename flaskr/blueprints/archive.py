import math 
from flask import Blueprint, render_template, request, session 
from werkzeug.exceptions import abort
from flaskr.db import get_db

bp = Blueprint("archive", __name__)

@bp.route("/", methods=["GET", "POST"])
def index():
    """Show all the theses"""
    db = get_db()

    departments = db.execute(
        "SELECT id, name, icon, description FROM department"
    ).fetchall()

    return render_template("archive/index.html", departments=departments)

@bp.route("/search", methods=["GET"])
@bp.route("/search/<int:dept_id>", methods=["GET", "POST"])
def search(dept_id=None):
    """Handles global searches, department filtering, sorting, and pagination."""
    db = get_db()
    user_id = session.get('user_id')

    search_term = request.args.get("q", "").strip()
    sort = request.args.get('sort', 'newest')
    year = request.args.get('year', '')
    
    # Pagination setup
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    conditions = ""
    cond_params = []
    department_info = None

    if dept_id is not None:
        conditions += " AND thesis.department_id = ?"
        cond_params.append(dept_id)
        
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
            "description": f"Searching global archive for '{search_term}'" if search_term else "All Collections"
        }

    if search_term:
        conditions += """ 
            AND (thesis.title LIKE '%' || ? || '%' 
            OR thesis.abstract LIKE '%' || ? || '%' 
            OR author.first_name LIKE '%' || ? || '%' 
            OR author.last_name LIKE '%' || ? || '%')
        """
        cond_params.extend([search_term, search_term, search_term, search_term])

    if year:
        conditions += " AND strftime('%Y', thesis.date_published) = ?"
        cond_params.append(year)

    # 1. Count Total Results for Pagination
    count_sql = """
        SELECT COUNT(DISTINCT thesis.id) 
        FROM thesis 
        JOIN thesis_author ON thesis.id = thesis_author.thesis_id 
        JOIN author ON thesis_author.author_id = author.id 
        WHERE 1=1
    """ + conditions
    total_results = db.execute(count_sql, cond_params).fetchone()[0]

    # 2. Build the main query (Now checks for bookmarks dynamically)
    select_sql = f"""
        SELECT thesis.id, thesis.title, thesis.date_published, thesis.file_path,
               department.name AS department_name, department.icon, department.description,
               GROUP_CONCAT(author.first_name || ' ' || author.last_name, ', ') AS authors,
               {'EXISTS(SELECT 1 FROM bookmark WHERE thesis_id = thesis.id AND user_id = ?)' if user_id else '0'} AS is_bookmarked
    """
    
    from_sql = """
        FROM thesis 
        JOIN thesis_author ON thesis.id = thesis_author.thesis_id 
        JOIN author ON thesis_author.author_id = author.id 
        JOIN department ON thesis.department_id = department.id 
        WHERE 1=1
    """
    
    group_sql = " GROUP BY thesis.id"

    order_sql = ""
    if sort == 'az': order_sql = " ORDER BY thesis.title ASC"
    elif sort == 'za': order_sql = " ORDER BY thesis.title DESC"
    elif sort == 'oldest': order_sql = " ORDER BY thesis.date_published ASC"
    else: order_sql = " ORDER BY thesis.date_published DESC"

    limit_sql = " LIMIT ? OFFSET ?"

    main_sql = select_sql + from_sql + conditions + group_sql + order_sql + limit_sql
    
    main_params = []
    if user_id: main_params.append(user_id) # Required for the EXISTS bookmark subquery
    main_params.extend(cond_params)
    main_params.extend([per_page, offset])

    theses = db.execute(main_sql, main_params).fetchall()
    total_pages = math.ceil(total_results / per_page) if total_results > 0 else 1

    return render_template(
        "archive/result.html", 
        theses=theses, 
        departments=department_info, 
        count=total_results, 
        current_sort=sort, 
        current_year=year,
        search=search_term,
        current_page=page,
        total_pages=total_pages
    )

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

    is_bookmarked = False
    if 'user_id' in session:
        bookmark = db.execute(
            'SELECT 1 FROM bookmark WHERE user_id = ? AND thesis_id = ?', 
            (session['user_id'], id)
        ).fetchone()
        
        if bookmark:
            is_bookmarked = True

    return render_template("archive/view.html", thesis=thesis, citation=citation, is_bookmarked=is_bookmarked)
