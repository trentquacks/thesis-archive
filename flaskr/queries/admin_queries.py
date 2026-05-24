from flaskr.queries.shared_queries import fetch_paginated_data
from flask import current_app
from datetime import datetime
import os

def get_thesis_stats(db):
    """Returns the total count for pending, approved, and rejected theses."""
    total_pending = db.execute("SELECT COUNT(id) FROM thesis WHERE status = 'pending'").fetchone()[0]
    total_approved = db.execute("SELECT COUNT(id) FROM thesis WHERE status = 'approved'").fetchone()[0]
    total_rejected = db.execute("SELECT COUNT(id) FROM thesis WHERE status = 'rejected'").fetchone()[0]
    
    return total_pending, total_approved, total_rejected

def get_departments_list(db):
    """Fetches all departments for the filter dropdown."""
    return db.execute('SELECT id, name FROM department ORDER BY name').fetchall()

def get_filtered_review_theses(db, status_filter, department_filter, sort_filter, page):
    """Builds and executes the paginated query for the review dashboard."""
    count_query = "SELECT COUNT(t.id) FROM thesis t WHERE t.status = ?"
    main_query = """
        SELECT t.id, t.title, t.status, t.date_added, d.name as department_name 
        FROM thesis t
        JOIN department d ON t.department_id = d.id
        WHERE t.status = ?
    """
    params = [status_filter]
    
    if department_filter != 'all':
        count_query += " AND t.department_id = ?"
        main_query += " AND t.department_id = ?"
        params.append(department_filter)
        
    if sort_filter == 'oldest':
        main_query += " ORDER BY t.date_added ASC"
    else:
        main_query += " ORDER BY t.date_added DESC"
        
    return fetch_paginated_data(db, main_query, count_query, params, page)

def update_thesis_status_and_log(db, thesis_id, user_id, new_status):
    """
    Updates the thesis status, logs it in user_history, and commits to the DB.
    Returns the title of the thesis on success, or None if the thesis wasn't found.
    """
    thesis = db.execute("SELECT title FROM thesis WHERE id = ?", (thesis_id,)).fetchone()
    
    if not thesis:
        return None
        
    db.execute(
        "UPDATE thesis SET status = ? WHERE id = ?",
        (new_status, thesis_id)
    )
    
    action_text = f"Marked as {new_status.capitalize()}"
    db.execute(
        "INSERT INTO user_history (user_id, action, thesis_id) VALUES (?, ?, ?)",
        (user_id, action_text, thesis_id)
    )
    
    db.commit()
    return thesis['title']

def get_thesis_by_id(db, thesis_id):
    """Fetches a single thesis record by its ID."""
    return db.execute("SELECT * FROM thesis WHERE id = ?", (thesis_id,)).fetchone()

def get_form_options(db):
    """Fetches all dropdown options required for the thesis form."""
    departments = db.execute("SELECT id, name FROM department ORDER BY name").fetchall()
    branches = db.execute("SELECT id, name FROM branch ORDER BY name").fetchall()
    formats = db.execute("SELECT id, format FROM format ORDER BY format").fetchall()
    return departments, branches, formats

def get_thesis_authors(db, thesis_id):
    """Fetches all authors associated with a specific thesis."""
    return db.execute("""
        SELECT a.* FROM author a 
        JOIN thesis_author ta ON a.id = ta.author_id 
        WHERE ta.thesis_id = ?
    """, (thesis_id,)).fetchall()

def get_thesis_advisors(db, thesis_id):
    """Fetches all advisors associated with a specific thesis."""
    return db.execute("""
        SELECT a.* FROM advisor a 
        JOIN thesis_advisor ta ON a.id = ta.advisor_id 
        WHERE ta.thesis_id = ?
    """, (thesis_id,)).fetchall()

def update_thesis_record(db, thesis_id, user_id, data, file_path=None, authors=None, advisors=None):
    """Updates base thesis data, handles optional file uploads, and rewrites contributor relationships."""
    
    query = """UPDATE thesis 
       SET title = ?, abstract = ?, keywords = ?, isbn = ?, 
           barcode = ?, call_number = ?, department_id = ?, 
           branch_id = ?, format_id = ?"""
    
    params = [data['title'], data['abstract'], data['keywords'], data['isbn'],
         data['barcode'], data['call_number'], data['department_id'],
         data['branch_id'], data['format_id']]
    
    if file_path:
        query += ", file_path = ?"
        params.append(file_path)
        
    query += " WHERE id = ?"
    params.append(thesis_id)
    
    db.execute(query, tuple(params))
    
    def _process_admin_contributors(role, data_list):
        config = {
            'author': {'table': 'author', 'id_col': 'student_no', 'map_table': 'thesis_author', 'fk_col': 'author_id'},
            'advisor': {'table': 'advisor', 'id_col': 'faculty_no', 'map_table': 'thesis_advisor', 'fk_col': 'advisor_id'}
        }
        c = config[role]
        
        db.execute(f"DELETE FROM {c['map_table']} WHERE thesis_id = ?", (thesis_id,))
        
        for person in data_list:
            unique_val = person[c['id_col']]
            existing = db.execute(f"SELECT id FROM {c['table']} WHERE {c['id_col']} = ?", (unique_val,)).fetchone()
            
            if existing:
                person_id = existing['id']
            else:
                res = db.execute(
                    f"INSERT INTO {c['table']} (first_name, middle_name, last_name, {c['id_col']}) VALUES (?, ?, ?, ?)",
                    (person['first_name'], person['middle_name'], person['last_name'], unique_val)
                )
                person_id = res.lastrowid
                
            db.execute(f"INSERT INTO {c['map_table']} (thesis_id, {c['fk_col']}) VALUES (?, ?)", (thesis_id, person_id))

    if authors is not None:
        _process_admin_contributors('author', authors)
    if advisors is not None:
        _process_admin_contributors('advisor', advisors)

    action_text = f"Edited record details"
    db.execute(
        "INSERT INTO user_history (user_id, action, thesis_id) VALUES (?, ?, ?)",
        (user_id, action_text, thesis_id)
    )
    db.commit()


def delete_thesis_record(db, thesis_id, user_id):
    """Safely deletes a thesis, its mappings, and optionally its physical file."""
    thesis = db.execute("SELECT title, file_path FROM thesis WHERE id = ?", (thesis_id,)).fetchone()
    
    if not thesis:
        return None
        
    # delete the physical file from the server if it exists
    if thesis['file_path']:
        actual_path = thesis['file_path'].lstrip('/') 
        if os.path.exists(actual_path):
            try:
                os.remove(actual_path)
            except OSError:
                pass 

    db.execute("DELETE FROM thesis_author WHERE thesis_id = ?", (thesis_id,))
    db.execute("DELETE FROM thesis_advisor WHERE thesis_id = ?", (thesis_id,))
    db.execute("DELETE FROM thesis WHERE id = ?", (thesis_id,))
    
    action_text = f"Deleted record: {thesis['title']}"
    db.execute(
        "INSERT INTO user_history (user_id, action, thesis_id) VALUES (?, ?, NULL)",
        (user_id, action_text)
    )
    
    db.commit()
    return thesis['title']


def get_dashboard_stats(db):
    """Fetches overview statistics for the main admin dashboard."""
    # total thesis & this week
    total_thesis = db.execute("SELECT COUNT(id) FROM thesis").fetchone()[0]
    thesis_week = db.execute("SELECT COUNT(id) FROM thesis WHERE date_added >= datetime('now', '-7 days')").fetchone()[0]
    
    # approved and rejected & this Week
    approved_total = db.execute("SELECT COUNT(id) FROM thesis WHERE status = 'approved'").fetchone()[0]
    approved_week = db.execute("SELECT COUNT(id) FROM thesis WHERE status = 'approved' AND date_added >= datetime('now', '-7 days')").fetchone()[0]
    
    rejected_total = db.execute("SELECT COUNT(id) FROM thesis WHERE status = 'rejected'").fetchone()[0]
    rejected_week = db.execute("SELECT COUNT(id) FROM thesis WHERE status = 'rejected' AND date_added >= datetime('now', '-7 days')").fetchone()[0]
    
    # deleted records & last year
    deleted_total = db.execute("SELECT COUNT(id) FROM user_history WHERE action LIKE 'Deleted record:%'").fetchone()[0]
    deleted_last_year = db.execute("SELECT COUNT(id) FROM user_history WHERE action LIKE 'Deleted record:%' AND timestamp >= datetime('now', '-1 year')").fetchone()[0]
    
    # registered accounts
    total_users = db.execute("SELECT COUNT(id) FROM user").fetchone()[0]
    
    # fake data for template
    users_week = db.execute("SELECT COUNT(id) FROM user WHERE date_registered >= datetime('now', '-7 days')").fetchone()[0]
    
    return {
        'total_thesis': total_thesis,
        'thesis_week': thesis_week,
        'approved_total': approved_total,
        'approved_week': approved_week,
        'rejected_total': rejected_total,
        'rejected_week': rejected_week,
        'deleted_total': deleted_total,
        'deleted_last_year': deleted_last_year,
        'total_users': total_users,
        'users_week': users_week
    }

def get_traffic_data(db, time_range='7days'):
    """Fetches traffic data scaled by days or months based on the requested time range."""
    
    if time_range == '30days':
        query = """
            WITH RECURSIVE dates(date) AS (
                SELECT date('now', '-29 days') UNION ALL
                SELECT date(date, '+1 day') FROM dates WHERE date < date('now')
            )
            SELECT d.date, COALESCE(t.guest_visits, 0) as guests, COALESCE(t.registered_visits, 0) as registered
            FROM dates d LEFT JOIN daily_traffic t ON d.date = t.visit_date ORDER BY d.date ASC
        """
        rows = db.execute(query).fetchall()
        labels = [datetime.strptime(row['date'], '%Y-%m-%d').strftime('%b %d') for row in rows]
        
    elif time_range == '1year':
        query = """
            WITH RECURSIVE months(ym) AS (
                SELECT strftime('%Y-%m', date('now', '-11 months')) UNION ALL
                SELECT strftime('%Y-%m', date(ym || '-01', '+1 month')) FROM months WHERE ym < strftime('%Y-%m', 'now')
            )
            SELECT m.ym as date, SUM(COALESCE(t.guest_visits, 0)) as guests, SUM(COALESCE(t.registered_visits, 0)) as registered
            FROM months m LEFT JOIN daily_traffic t ON strftime('%Y-%m', t.visit_date) = m.ym
            GROUP BY m.ym ORDER BY m.ym ASC
        """
        rows = db.execute(query).fetchall()
        labels = [datetime.strptime(row['date'], '%Y-%m').strftime('%b %Y') for row in rows]
        
    elif time_range == 'all':
        first_record = db.execute("SELECT MIN(visit_date) as min_date FROM daily_traffic").fetchone()
        start_date = first_record['min_date'] if first_record and first_record['min_date'] else datetime.now().strftime('%Y-%m-%d')
        
        query = f"""
            WITH RECURSIVE months(ym) AS (
                SELECT strftime('%Y-%m', '{start_date}') UNION ALL
                SELECT strftime('%Y-%m', date(ym || '-01', '+1 month')) FROM months WHERE ym < strftime('%Y-%m', 'now')
            )
            SELECT m.ym as date, SUM(COALESCE(t.guest_visits, 0)) as guests, SUM(COALESCE(t.registered_visits, 0)) as registered
            FROM months m LEFT JOIN daily_traffic t ON strftime('%Y-%m', t.visit_date) = m.ym
            GROUP BY m.ym ORDER BY m.ym ASC
        """
        rows = db.execute(query).fetchall()
        labels = [datetime.strptime(row['date'], '%Y-%m').strftime('%b %Y') for row in rows]
        
    else:
        # Default: Last 7 Days (Daily)
        query = """
            WITH RECURSIVE dates(date) AS (
                SELECT date('now', '-6 days') UNION ALL
                SELECT date(date, '+1 day') FROM dates WHERE date < date('now')
            )
            SELECT d.date, COALESCE(t.guest_visits, 0) as guests, COALESCE(t.registered_visits, 0) as registered
            FROM dates d LEFT JOIN daily_traffic t ON d.date = t.visit_date ORDER BY d.date ASC
        """
        rows = db.execute(query).fetchall()
        labels = [datetime.strptime(row['date'], '%Y-%m-%d').strftime('%b %d') for row in rows]

    guests = [row['guests'] for row in rows]
    registered = [row['registered'] for row in rows]
    
    return labels, guests, registered

def get_department_distribution(db):
    """Fetches the number of theses per department for the pie chart."""
    rows = db.execute('''
        SELECT d.name, COUNT(t.id) as count
        FROM department d
        LEFT JOIN thesis t ON d.id = t.department_id
        GROUP BY d.id, d.name
        ORDER BY count DESC
    ''').fetchall()
    
    labels = [row['name'] for row in rows]
    counts = [row['count'] for row in rows]
    
    return labels, counts

from flaskr.queries.shared_queries import fetch_paginated_data

def get_projects_tracking_data(db, sort_filter, page, per_page=10):
    """Fetches engagement stats (views, borrows, recent borrowers) for approved projects."""
    count_query = "SELECT COUNT(id) FROM thesis WHERE status = 'approved'"
    
    # counts borrows and grabs the names of the most recent borrowers
    main_query = """
        SELECT t.id, t.title, t.views, d.name as department_name,
               (SELECT COUNT(*) FROM user_history uh WHERE uh.thesis_id = t.id AND uh.action = 'Borrowed') as borrow_count,
               (
                   SELECT GROUP_CONCAT(first_name || ' ' || last_name, ', ') 
                   FROM (
                       SELECT u.first_name, u.last_name 
                       FROM user_history uh 
                       JOIN user u ON uh.user_id = u.id 
                       WHERE uh.thesis_id = t.id AND uh.action = 'Borrowed' 
                       ORDER BY uh.timestamp DESC LIMIT 3
                   )
               ) as recent_borrowers
        FROM thesis t
        JOIN department d ON t.department_id = d.id
        WHERE t.status = 'approved'
    """
    
    if sort_filter == 'most_viewed':
        main_query += " ORDER BY t.views DESC"
    elif sort_filter == 'most_borrowed':
        main_query += " ORDER BY borrow_count DESC"
    else:
        main_query += " ORDER BY t.date_published DESC"
        
    return fetch_paginated_data(db, main_query, count_query, [], page, per_page)
