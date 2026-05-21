import os
from datetime import datetime
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from flask import Blueprint, flash, g, redirect, render_template, request, url_for, session, current_app
from flaskr.db import get_db
from flaskr.helper import (save_uploaded_file, extract_contributors_from_form)
from flaskr.queries import (get_submission_form_options, get_user_thesis, submit_thesis_transaction, toggle_user_bookmark,
                            update_profile_picture,
                            update_user_password, 
                            get_user_project_count, 
                            get_user_bookmark_count,
                            get_user_bookmarks_paginated,
                            get_user_history_paginated,
                            toggle_user_bookmark,
                            get_submission_form_options,
                            submit_thesis_transaction
                            )
bp = Blueprint("user", __name__, url_prefix="/user")

@bp.before_request
def require_login():
    if g.user is None:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return {"error:": "Unauthorized"}, 401
        flash("Login required", "error")
        return redirect(url_for('auth.login'))

@bp.route("/dashboard")
def dashboard():
    db = get_db()
    current_user_id = session['user_id']
    theses = get_user_thesis(db, current_user_id)

    total_projects = len(theses)
    under_review = sum(1 for t in theses if t['status'] == 'pending')
    approved = sum(1 for t in theses if t['status'] == 'approved')

    return render_template("user/dashboard.html", 
        theses=theses,
        total_projects=total_projects,
        under_review=under_review,
        approved=approved
        )


@bp.route('/profile', methods=('GET', 'POST'))
def profile():
    db = get_db()
    user_id = g.user['id']

    if request.method == 'POST':
        if 'profile_pic' in request.files:
            _, _, unique_filename = save_uploaded_file(
                request.files['profile_pic'], 
                'profile_pics', 
                f"user_{user_id}"
            )
            
            if unique_filename:
                update_profile_picture(db, unique_filename, user_id)
                flash('Profile picture updated successfully!')
                return redirect(url_for('user.profile'))

        elif 'current_password' in request.form:
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            
            error = None
            if not check_password_hash(g.user['password'], current_password):
                error = 'Incorrect current password.'
            elif new_password != confirm_password:
                error = 'New passwords do not match.'
                
            if error is None:
                update_user_password(db, generate_password_hash(new_password), user_id)
                flash('Password successfully updated!', "success")
                return redirect(url_for('user.profile'))
            flash(error)

    total_projects = get_user_project_count(db, user_id)
    total_bookmarks = get_user_bookmark_count(db, user_id)

    return render_template(
        'user/profile.html', 
        total_projects=total_projects, 
        total_bookmarks=total_bookmarks
    )

@bp.route('/history')
def history():
    user_id = g.user['id']
    
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '')
    date_filter = request.args.get('date', '')
    sort_order = request.args.get('sort', 'newest')
    
    history_data, total_events, total_pages = get_user_history_paginated(
        get_db(), user_id, page, action_filter, date_filter, sort_order
    )

    return render_template(
        'user/history.html',
        history_events=history_data,
        total_events=total_events, 
        current_page=page,
        total_pages=total_pages,
        current_action=action_filter,
        current_date=date_filter,
        current_sort=sort_order 
    )
@bp.route('/bookmarks')
def bookmarks():
    user_id = g.user['id']
    
    page = request.args.get('page', 1, type=int)
    current_sort = request.args.get('sort', 'date')
    current_order = request.args.get('order', 'desc').lower()

    bookmarks_data, total_bookmarks, total_pages = get_user_bookmarks_paginated(
        get_db(), user_id, page, current_sort, current_order
    )

    return render_template(
        'user/bookmarks.html',
        bookmarks=bookmarks_data,
        total_bookmarks=total_bookmarks,
        current_page=page,
        total_pages=total_pages,
        current_sort=current_sort,
        current_order=current_order 
    )

@bp.route("/bookmark/<int:thesis_id>", methods=["POST"])
def toggle_bookmark(thesis_id):
    is_bookmarked, msg = toggle_user_bookmark(get_db(), g.user['id'], thesis_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {"bookmarked": is_bookmarked, "message": msg}

    flash(msg, "success")
    return redirect(request.referrer or url_for('user.view', id=thesis_id))

@bp.route("/submit", methods=['GET', 'POST'])
def submit():
    db = get_db()

    if request.method == 'POST':
        date_published = request.form.get('date')
        upload_year = str(date_published)[:4] if date_published else str(datetime.now().year)

        file = request.files.get('file')
        file_path, actual_save_path = "N/A", None

        if file and file.filename != '':
            timestamp = int(datetime.now().timestamp())
            prefix = f"thesis_{g.user['id']}_{timestamp}"
            try:
                file_path, actual_save_path, _ = save_uploaded_file(
                    file, upload_year, prefix, allowed_extensions=['pdf'], max_size_mb=50
                )
            except ValueError as e:
                flash(str(e), "error")
                return redirect(request.url)

        author_data_list = extract_contributors_from_form(request.form, 'author')
        advisor_data_list = extract_contributors_from_form(request.form, 'advisor')

        thesis_data = {
            'title': request.form.get('title'),
            'abstract': request.form.get('abstract'),
            'keywords': request.form.get('keywords'),
            'department_id': request.form.get('program'),
            'branch_id': request.form.get('branch'),
            'format_id': request.form.get('format')
        }

        success, error_msg = submit_thesis_transaction(
            db, g.user['id'], file_path, date_published, author_data_list, advisor_data_list, thesis_data
        )

        if success:
            flash('Thesis submitted successfully and is pending approval!', 'success')
            return redirect(url_for('user.dashboard'))
        else:
            if actual_save_path and os.path.exists(actual_save_path):
                os.remove(actual_save_path) # Rollback file if DB fails
            flash(f"An error occurred while saving: {error_msg}", 'error')

    programs, formats, branches = get_submission_form_options(db)
    return render_template("user/form.html", programs=programs, formats=formats, branches=branches)
