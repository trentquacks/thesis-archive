import functools
from datetime import datetime
from flask import Blueprint, render_template, g, redirect, url_for, flash, request
from flaskr.db import get_db
from flaskr.helper import extract_contributors_from_form, save_uploaded_file
from flaskr.queries.shared_queries import get_form_dropdown_options
from flaskr.queries.admin_queries import (
    get_thesis_stats, get_departments_list, get_filtered_review_theses, 
    update_thesis_status_and_log, get_thesis_by_id, 
    update_thesis_record, get_thesis_authors, get_thesis_advisors
)
bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        if g.user['role'] != 'admin':
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for("archive.index"))
        return view(**kwargs)
    return wrapped_view


@bp.route("/dashboard")
@admin_required
def dashboard():
    return render_template("admin/dashboard.html")


@bp.route("/review")
@admin_required
def review():
    db = get_db()
    
    department_filter = request.args.get('department', 'all')
    sort_filter = request.args.get('sort', 'newest')
    status_filter = request.args.get('status', 'pending') 
    page = request.args.get('page', 1, type=int)
    
    departments = get_departments_list(db)
    total_pending, total_approved, total_rejected = get_thesis_stats(db)
    theses, total_theses, total_pages = get_filtered_review_theses(
        db, status_filter, department_filter, sort_filter, page
    )

    return render_template(
        "admin/review.html",
        theses=theses,
        departments=departments,
        current_dept=department_filter,
        current_sort=sort_filter,
        current_status=status_filter,
        total_pending=total_pending,
        total_approved=total_approved,
        total_rejected=total_rejected,
        current_page=page,
        total_pages=total_pages,
        total_theses=total_theses
    )


@bp.route('/thesis/<int:id>/status/<string:new_status>', methods=['POST'])
@admin_required
def update_status(id, new_status):
    if new_status not in ['approved', 'rejected', 'pending']:
        flash("Invalid status update.", "error")
        return redirect(request.referrer or url_for('admin.review'))

    db = get_db()
    thesis_title = update_thesis_status_and_log(db, id, g.user['id'], new_status)
    
    if not thesis_title:
        flash("Thesis record not found.", "error")
    else:
        flash(f"Project '{thesis_title}' has been {new_status}.", "success")
        
    return redirect(request.referrer or url_for('admin.review'))

@bp.route('/thesis/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(id):
    db = get_db()
    thesis = get_thesis_by_id(db, id)

    if not thesis:
        flash("Thesis record not found.", "error")
        return redirect(url_for('admin.review'))
        
    if thesis['status'] == 'rejected':
        flash("Cannot edit a rejected thesis.", "error")
        return redirect(url_for('admin.review'))

    if request.method == 'POST':
        author_data_list = extract_contributors_from_form(request.form, 'author')
        advisor_data_list = extract_contributors_from_form(request.form, 'advisor')
        
        file = request.files.get('file')
        file_path = None
        if file and file.filename != '':
            pub_date = thesis['date_published']
            upload_year = str(pub_date)[:4] if pub_date else str(datetime.now().year)
            prefix = f"thesis_{g.user['id']}_{int(datetime.now().timestamp())}"
            try:
                file_path, _, _ = save_uploaded_file(
                    file, upload_year, prefix, allowed_extensions=['pdf'], max_size_mb=50
                )
            except ValueError as e:
                flash(str(e), "error")
                return redirect(request.url)

        form_data = {
            'title': request.form['title'].strip(),
            'abstract': request.form['abstract'].strip(),
            'keywords': request.form.get('keywords', '').strip(),
            'isbn': request.form.get('isbn', '').strip(),
            'barcode': request.form.get('barcode', '').strip(),
            'call_number': request.form.get('call_number', '').strip(),
            'department_id': request.form['department_id'],
            'branch_id': request.form['branch_id'],
            'format_id': request.form['format_id']
        }
        
        if not form_data['title'] or not form_data['abstract'] or not form_data['department_id']:
            flash("Title, Abstract, and Department are required.", "error")
        else:
            update_thesis_record(
                db, id, g.user['id'], form_data, 
                file_path=file_path, authors=author_data_list, advisors=advisor_data_list
            )
            flash("Thesis record updated successfully.", "success")
            return redirect(url_for('admin.review'))

    departments, branches, formats = get_form_dropdown_options(db)
    authors = get_thesis_authors(db, id)
    advisors = get_thesis_advisors(db, id)
    
    return render_template(
        "admin/edit.html", 
        thesis=thesis, 
        departments=departments, 
        branches=branches, 
        formats=formats,
        authors=authors,
        advisors=advisors
    )
