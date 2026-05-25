import math

def get_all_departments(db):
    return db.execute("SELECT id, name, icon, description FROM department").fetchall()

def get_search_results(db, user_id, dept_id, search_term, sort, year, page, per_page=10):
    conditions = "AND thesis.status = 'approved'"
    cond_params = []
    department_info = {
        "id": None,
        "name": "All Collections", 
        "icon": "fa-globe", 
        "description": f"Searching global archive for '{search_term}'" if search_term else "All Collections"
    }

    if dept_id is not None:
        conditions += " AND thesis.department_id = ?"
        cond_params.append(dept_id)
        dept = db.execute("SELECT id, name, description, icon FROM department WHERE id = ?", (dept_id,)).fetchone()
        if dept: department_info = dept

    if search_term:
        conditions += """ 
            AND (thesis.title LIKE '%' || ? || '%' OR thesis.abstract LIKE '%' || ? || '%' 
            OR thesis.keywords LIKE '%' || ? || '%' OR author.first_name LIKE '%' || ? || '%' 
            OR author.last_name LIKE '%' || ? || '%')
        """
        cond_params.extend([search_term] * 5)

    if year:
        conditions += " AND strftime('%Y', thesis.date_published) = ?"
        cond_params.append(year)

    if user_id:
        user = db.execute("SELECT role FROM user WHERE id = ?", (user_id,)).fetchone()
        if user and user['role'] == 'admin':
            pass # admins can see all statuses in search
        else:
            conditions += " AND (thesis.status = 'approved' OR thesis.uploader_id = ?)"
            cond_params.append(user_id)
    else:
        # guests only see approved
        conditions += " AND thesis.status = 'approved'"

    count_sql = """
        SELECT COUNT(DISTINCT thesis.id) FROM thesis 
        JOIN thesis_author ON thesis.id = thesis_author.thesis_id 
        JOIN author ON thesis_author.author_id = author.id 
        WHERE 1=1
    """ + conditions
    
    total_results = db.execute(count_sql, cond_params).fetchone()[0]

    select_sql = f"""
        SELECT thesis.id, thesis.title, thesis.date_published, thesis.file_path, thesis.status,
               department.name AS department_name, department.icon, department.description,
               GROUP_CONCAT(author.first_name || ' ' || author.last_name, ', ') AS authors,
               {'EXISTS(SELECT 1 FROM bookmark WHERE thesis_id = thesis.id AND user_id = ?)' if user_id else '0'} AS is_bookmarked
        FROM thesis 
        JOIN thesis_author ON thesis.id = thesis_author.thesis_id 
        JOIN author ON thesis_author.author_id = author.id 
        JOIN department ON thesis.department_id = department.id 
        WHERE 1=1 {conditions}
        GROUP BY thesis.id
    """

    order_map = {
        'az': " ORDER BY thesis.title ASC",
        'za': " ORDER BY thesis.title DESC",
        'oldest': " ORDER BY thesis.date_published ASC"
    }
    select_sql += order_map.get(sort, " ORDER BY thesis.date_published DESC") + " LIMIT ? OFFSET ?"

    main_params = ([user_id] if user_id else []) + cond_params + [per_page, (page - 1) * per_page]
    theses = db.execute(select_sql, main_params).fetchall()
    
    total_pages = math.ceil(total_results / per_page) if total_results > 0 else 1
    
    return theses, department_info, total_results, total_pages

def get_thesis_details(db, thesis_id):
    query = """
        SELECT t.id, t.title, t.abstract, t.keywords, t.file_path, t.call_number, t.barcode,
            t.status, t.uploader_id, 
            strftime('%Y', t.date_published) AS year, d.name AS department_name, 
            d.description AS program_name, d.id as department_id, d.icon, f.format AS document_type,
            GROUP_CONCAT(a.first_name || ' ' || a.last_name, ', ') AS authors,
            GROUP_CONCAT(a.last_name || ', ' || SUBSTR(a.first_name, 1, 1) || '.', ', ') AS citation_authors
        FROM thesis t
        JOIN department d ON t.department_id = d.id
        LEFT JOIN format f ON t.format_id = f.id
        LEFT JOIN thesis_author ta ON t.id = ta.thesis_id
        LEFT JOIN author a ON ta.author_id = a.id
        WHERE t.id = ? GROUP BY t.id
    """
    return db.execute(query, (thesis_id,)).fetchone()

def get_thesis_advisors_string(db, thesis_id):
    advisors = db.execute('''
        SELECT adv.first_name || ' ' || adv.last_name AS full_name
        FROM thesis_advisor tadv
        JOIN advisor adv ON tadv.advisor_id = adv.id
        WHERE tadv.thesis_id = ?
    ''', (thesis_id,)).fetchall()
    return ", ".join([row['full_name'] for row in advisors])

def check_user_bookmark(db, user_id, thesis_id):
    if not user_id: return False
    return bool(db.execute('SELECT 1 FROM bookmark WHERE user_id = ? AND thesis_id = ?', (user_id, thesis_id)).fetchone())

def get_active_borrow_record(db, user_id, thesis_id):
    if not user_id: return None
    return db.execute('''
        SELECT id,
            CASE WHEN is_paused = 1 THEN time_left 
            ELSE time_left - CAST((strftime('%s', 'now') - strftime('%s', last_tick)) AS INTEGER) END as actual_time_left
        FROM active_borrow WHERE user_id = ? AND thesis_id = ?
    ''', (user_id, thesis_id)).fetchone()

def get_daily_borrow_count(db, user_id):
    if not user_id: return 0
    res = db.execute('''
        SELECT COUNT(*) as count FROM user_history 
        WHERE user_id = ? AND action = 'Borrowed' AND date(timestamp) = date('now')
    ''', (user_id,)).fetchone()
    return res['count'] if res else 0

def process_borrow_logic(db, user_id, thesis_id):
    thesis = db.execute('SELECT file_path FROM thesis WHERE id = ?', (thesis_id,)).fetchone()
    if not thesis or not thesis['file_path']:
        return False, "This thesis does not have an available digital copy.", 'archive.view'

    active = db.execute('''
        SELECT 1 FROM user_history WHERE user_id = ? AND thesis_id = ? AND action = 'Borrowed' 
        AND timestamp >= datetime('now', '-2 hours')
    ''', (user_id, thesis_id)).fetchone()
    if active:
        return True, None, 'archive.read' 
        
    if get_daily_borrow_count(db, user_id) >= 5:
        return False, "You have exceeded the allowed borrowing limit of 5 theses per day.", 'archive.view'
        
    db.execute('DELETE FROM active_borrow WHERE user_id = ? AND thesis_id = ?', (user_id, thesis_id))
    db.execute("INSERT INTO user_history (user_id, action, thesis_id) VALUES (?, 'Borrowed', ?)", (user_id, thesis_id))
    db.execute("INSERT INTO active_borrow (user_id, thesis_id, time_left, last_tick, is_paused) VALUES (?, ?, 7200, CURRENT_TIMESTAMP, 0)", (user_id, thesis_id))
    db.commit()
    
    return True, "Thesis borrowed successfully. You have 2 hours to read it.", 'archive.read'

def remove_expired_borrow(db, borrow_id):
    db.execute('DELETE FROM active_borrow WHERE id = ?', (borrow_id,))
    db.commit()

def increment_thesis_views(db, thesis_id):
    db.execute("UPDATE thesis SET views = views + 1 WHERE id = ?", (thesis_id,))
    db.commit()
