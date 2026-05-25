from flask import Blueprint, render_template, request, session, redirect, url_for, flash, g 
from werkzeug.exceptions import abort
from flaskr.db import get_db
from flaskr.queries.archive_queries import (
    get_all_departments, get_search_results, get_thesis_details, 
    get_thesis_advisors_string, check_user_bookmark, get_active_borrow_record, 
    get_daily_borrow_count, process_borrow_logic, remove_expired_borrow,
    increment_thesis_views
)

bp = Blueprint("archive", __name__)

@bp.route("/", methods=["GET", "POST"])
def index():
    departments = get_all_departments(get_db())
    return render_template("archive/index.html", departments=departments)

@bp.route("/search", methods=["GET"])
@bp.route("/search/<int:dept_id>", methods=["GET", "POST"])
def search(dept_id=None):
    search_term = request.args.get("q", "").strip()
    sort = request.args.get('sort', 'newest')
    year = request.args.get('year', '')
    page = request.args.get('page', 1, type=int)

    theses, department_info, count, total_pages = get_search_results(
        get_db(), session.get('user_id'), dept_id, search_term, sort, year, page
    )

    if dept_id is not None and department_info["id"] is None:
        abort(404, f"Department ID {dept_id} doesn't exist.")

    return render_template(
        "archive/result.html", 
        theses=theses, departments=department_info, count=count, 
        current_sort=sort, current_year=year, search=search_term,
        current_page=page, total_pages=total_pages
    )

@bp.route("/view/<int:id>")
def view(id):
    db = get_db()
    thesis = get_thesis_details(db, id)

    if thesis is None:
        abort(404, f"Thesis ID {id} doesn't exist.")

    if thesis['status'] != 'approved':
        if g.user is None:
            flash("You do not have permission to view this thesis.", "error")
            return redirect(url_for('archive.index'))
        
        # check permissions
        is_uploader = (g.user['id'] == thesis['uploader_id'])
        is_admin = (g.user['role'] == 'admin')
        
        if not (is_uploader or is_admin):
            flash("This thesis is currently pending approval or rejected.", "error")
            return redirect(url_for('archive.index'))

    advisor_names = get_thesis_advisors_string(db, id)
    citation = f"{thesis['citation_authors']} ({thesis['year']}). {thesis['title']}."
    
    user_id = session.get('user_id')
    is_bookmarked = check_user_bookmark(db, user_id, id)
    
    borrow_record = get_active_borrow_record(db, user_id, id)
    actual_time_left = borrow_record['actual_time_left'] if borrow_record and borrow_record['actual_time_left'] > 0 else 0
    active_borrow = actual_time_left > 0
    
    daily_borrows_count = get_daily_borrow_count(db, user_id)
    increment_thesis_views(db, id)

    return render_template(
        "archive/view.html", thesis=thesis, citation=citation, is_bookmarked=is_bookmarked,
        advisor_names=advisor_names, active_borrow=active_borrow,
        actual_time_left=actual_time_left, daily_borrows_count=daily_borrows_count
    )

@bp.route("/borrow/<int:id>", methods=["POST"])
def borrow(id):
    if 'user_id' not in session:
        flash("You must be logged in to borrow a thesis.", "error")
        return redirect(url_for('auth.login')) 

    if g.user['role'] == 'admin':
        flash("Administrators cannot use the borrowing system.", "error")
        return redirect(url_for('archive.view', id=id))

    success, message, redirect_route = process_borrow_logic(get_db(), session['user_id'], id)
    
    if message:
        flash(message, "success" if success else "error")
        
    return redirect(url_for(redirect_route, id=id))

@bp.route("/read/<int:id>")
def read(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    db = get_db()
    borrow_record = get_active_borrow_record(db, session['user_id'], id)
    
    if not borrow_record or borrow_record['actual_time_left'] <= 0:
        if borrow_record:
            remove_expired_borrow(db, borrow_record['id'])
        flash("Time Expired. Your access to this PDF has ended.", "error")
        return redirect(url_for('archive.view', id=id))
        
    thesis = db.execute('SELECT title, file_path FROM thesis WHERE id = ?', (id,)).fetchone()
    return render_template('archive/read.html', thesis=thesis, thesis_id=id, time_left=borrow_record['actual_time_left'])
