import os
import uuid
import math 
from datetime import datetime
from flask import Blueprint, flash, g, redirect, render_template, request, url_for, session, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from flaskr.db import get_db

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
            file = request.files['profile_pic']
            if file.filename != '':
                filename = secure_filename(file.filename)
                unique_filename = f"user_{user_id}_{filename}"
                
                filepath = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_pics', unique_filename)
                file.save(filepath)

                db.execute('UPDATE user SET profile_pic = ? WHERE id = ?', (unique_filename, user_id))
                db.commit()
                
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
                db.execute('UPDATE user SET password = ? WHERE id = ?', (generate_password_hash(new_password), user_id))
                db.commit()
                flash('Password successfully updated!')
                return redirect(url_for('user.profile'))
            flash(error)

    projects_query = db.execute(
        'SELECT COUNT(id) as count FROM thesis WHERE uploader_id = ?',
        (user_id,)
    ).fetchone()
    total_projects = projects_query['count'] if projects_query else 0

    bookmarks_query = db.execute(
        'SELECT COUNT(thesis_id) as count FROM bookmark WHERE user_id = ?',
        (user_id,)
    ).fetchone()
    total_bookmarks = bookmarks_query['count'] if bookmarks_query else 0

    return render_template(
        'user/profile.html', 
        total_projects=total_projects, 
        total_bookmarks=total_bookmarks
    )

@bp.route('/history')
def history():
    if g.user is None:
        flash("Please log in to view your history.")
        return redirect(url_for('auth.login'))

    user_id = g.user['id']
    db = get_db()
    
    # 1. Get filter, sort, and pagination parameters
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '')
    date_filter = request.args.get('date', '')
    sort_order = request.args.get('sort', 'newest') # New sorting parameter!
    
    per_page = 10
    offset = (page - 1) * per_page

    # 2. Build the query dynamically based on filters
    conditions = "WHERE h.user_id = ?"
    params = [user_id]

    if action_filter:
        conditions += " AND h.action = ?"
        params.append(action_filter)
    
    if date_filter:
        conditions += " AND date(h.timestamp) = ?"
        params.append(date_filter)

    # 3. Count total items for pagination
    total_events = db.execute(
        f'SELECT COUNT(*) FROM user_history h {conditions}', 
        params
    ).fetchone()[0]

    # 4. Handle Sorting Logic
    order_sql = "ORDER BY h.timestamp DESC"
    if sort_order == 'oldest':
        order_sql = "ORDER BY h.timestamp ASC"

    # 5. Fetch the actual history data
    query = f'''
        SELECT h.action, h.timestamp, t.id AS thesis_id, t.title 
        FROM user_history h
        LEFT JOIN thesis t ON h.thesis_id = t.id
        {conditions}
        {order_sql}
        LIMIT ? OFFSET ?
    '''
    
    fetch_params = params + [per_page, offset]
    history_data = db.execute(query, fetch_params).fetchall()
    
    import math
    total_pages = math.ceil(total_events / per_page) if total_events > 0 else 1

    return render_template(
        'user/history.html',
        history_events=history_data,
        current_page=page,
        total_pages=total_pages,
        current_action=action_filter,
        current_date=date_filter,
        current_sort=sort_order 
    )

@bp.route('/bookmarks')
def bookmarks():
    if g.user is None:
        flash("Please log in to view your bookmarks.")
        return redirect(url_for('auth.login'))

    user_id = g.user['id']
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    current_sort = request.args.get('sort', 'date')
    current_order = request.args.get('order', 'desc').lower()

    valid_columns = {
        'title': 't.title',
        'author': 'a.last_name',
        'date': 'b.date_bookmarked'
    }
    
    db_col = valid_columns.get(current_sort, 'b.date_bookmarked')
    if current_order not in ['asc', 'desc']:
        current_order = 'desc'

    db = get_db() 

    total_bookmarks = db.execute(
        'SELECT COUNT(*) FROM bookmark WHERE user_id = ?', 
        (user_id,)
    ).fetchone()[0]

    query = f'''
        SELECT 
            b.thesis_id, 
            t.title, 
            GROUP_CONCAT(a.last_name || ', ' || a.first_name, '; ') AS author,
            b.date_bookmarked AS date_added
        FROM bookmark b
        JOIN thesis t ON b.thesis_id = t.id
        LEFT JOIN thesis_author ta ON t.id = ta.thesis_id
        LEFT JOIN author a ON ta.author_id = a.id
        WHERE b.user_id = ?
        GROUP BY b.thesis_id, t.title, b.date_bookmarked
        ORDER BY {db_col} {current_order.upper()}
        LIMIT ? OFFSET ?
    '''
    
    bookmarks_data = db.execute(query, (user_id, per_page, offset)).fetchall()
    total_pages = math.ceil(total_bookmarks / per_page) if total_bookmarks > 0 else 1

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
    if 'user_id' not in session:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return {"error": "Unauthorized"}, 401
        
        flash("You need to be logged in to bookmark theses.", "error")
        return redirect(url_for('auth.login')) 

    user_id = session['user_id']
    db = get_db()

    existing_bookmark = db.execute(
        'SELECT 1 FROM bookmark WHERE user_id = ? AND thesis_id = ?', 
        (user_id, thesis_id)
    ).fetchone()

    is_bookmarked = False

    if existing_bookmark:
        db.execute('DELETE FROM bookmark WHERE user_id = ? AND thesis_id = ?', (user_id, thesis_id))
        db.execute('INSERT INTO user_history (user_id, action, thesis_id) VALUES (?, ?, ?)', (user_id, 'Unbookmarked', thesis_id))
        is_bookmarked = False
        msg = "Removed from bookmarks."
    else:
        db.execute('INSERT INTO bookmark (user_id, thesis_id) VALUES (?, ?)', (user_id, thesis_id))
        db.execute('INSERT INTO user_history (user_id, action, thesis_id) VALUES (?, ?, ?)', (user_id, 'Bookmarked', thesis_id))
        is_bookmarked = True
        msg = "Thesis bookmarked successfully!"

    db.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {"bookmarked": is_bookmarked, "message": msg}

    flash(msg, "success")
    return redirect(request.referrer or url_for('user.view', id=thesis_id))


@bp.route("/submit", methods=['GET', 'POST'])
def submit():
    db = get_db()
    programs = db.execute("SELECT id, name FROM department").fetchall()
    formats = db.execute("SELECT id, format FROM format").fetchall()
    branches = db.execute("SELECT id, name FROM branch").fetchall()

    if request.method == 'POST':
        
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
        middle_name = request.form.get('author_middle_name', '')
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

            author = db.execute("SELECT id FROM author WHERE student_no = ?", (student_no,)).fetchone()
            if author:
                author_id = author['id']
            else:
                query = db.execute(
                    "INSERT INTO author (first_name, last_name, student_no) VALUES (?, ?, ?, ?)",
                    (first_name, last_name, student_no)
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

            db.execute(
                "INSERT INTO user_history (user_id, action, thesis_id) VALUES (?, ?, ?)",
                (uploader_id, 'Submitted', thesis_id)
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

        return redirect(url_for('user.dashboard'))
    return render_template("user/form.html", programs=programs, formats=formats, branches=branches)













