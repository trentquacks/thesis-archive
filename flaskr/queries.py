import math
import uuid

def get_user_thesis(db, user_id):
    return db.execute("""
        SELECT thesis.id, title, status, strftime('%Y', thesis.date_published) as year, department.icon 
        FROM thesis 
        JOIN department ON thesis.department_id = department.id
        WHERE uploader_id = ?
        ORDER BY thesis.date_published DESC
    """, (user_id,)).fetchall()


def update_profile_picture(db, filename, user_id):
    db.execute('UPDATE user SET profile_pic = ? WHERE id = ?', (filename, user_id))
    db.commit()


def update_user_password(db, user_id, hashed_password):
    db.execute('UPDATE user SET password = ? WHERE id = ?', (hashed_password, user_id))
    db.commit()


def get_user_project_count(db, user_id):
    result = db.execute('SELECT COUNT(id) as count FROM thesis WHERE uploader_id = ?', (user_id,)).fetchone()
    return result['count'] if result else 0


def get_user_bookmark_count(db, user_id):
    result = db.execute('SELECT COUNT(thesis_id) as count FROM bookmark WHERE user_id = ?', (user_id,)).fetchone()
    return result['count'] if result else 0

import math

def fetch_paginated_data(db, main_query, count_query, params, page, per_page=10):
    """automatically paginates any SQL query."""
    
    total_items = db.execute(count_query, params).fetchone()[0]
   
    paginated_query = f"{main_query} LIMIT ? OFFSET ?"
    fetch_params = params + [per_page, (page - 1) * per_page]
    
    data = db.execute(paginated_query, fetch_params).fetchall()
    
    total_pages = max(1, math.ceil(total_items / per_page))
    
    return data, total_items, total_pages


def get_user_bookmarks_paginated(db, user_id, page, current_sort, current_order):
    valid_columns = {'title': 't.title', 'author': 'a.last_name', 'date': 'b.date_bookmarked'}
    db_col = valid_columns.get(current_sort, 'b.date_bookmarked')
    db_order = "ASC" if current_order == 'asc' else "DESC"

    count_query = "SELECT COUNT(*) FROM bookmark WHERE user_id = ?"
    
    main_query = f'''
        SELECT 
            b.thesis_id, t.title, 
            GROUP_CONCAT(a.last_name || ', ' || a.first_name, '; ') AS author,
            b.date_bookmarked AS date_added
        FROM bookmark b
        JOIN thesis t ON b.thesis_id = t.id
        LEFT JOIN thesis_author ta ON t.id = ta.thesis_id
        LEFT JOIN author a ON ta.author_id = a.id
        WHERE b.user_id = ?
        GROUP BY b.thesis_id, t.title, b.date_bookmarked
        ORDER BY {db_col} {db_order}
    '''

    return fetch_paginated_data(db, main_query, count_query, [user_id], page)


def toggle_user_bookmark(db, user_id, thesis_id):
    existing_bookmark = db.execute(
        'SELECT 1 FROM bookmark WHERE user_id = ? AND thesis_id = ?', 
        (user_id, thesis_id)
    ).fetchone()

    is_bookmarked = existing_bookmark is None

    if is_bookmarked:
        db.execute('INSERT INTO bookmark (user_id, thesis_id) VALUES (?, ?)', (user_id, thesis_id))
        db.execute('INSERT INTO user_history (user_id, action, thesis_id) VALUES (?, ?, ?)', (user_id, 'Bookmarked', thesis_id))
        msg = "Thesis bookmarked successfully!"
    else:
        db.execute('DELETE FROM bookmark WHERE user_id = ? AND thesis_id = ?', (user_id, thesis_id))
        db.execute('INSERT INTO user_history (user_id, action, thesis_id) VALUES (?, ?, ?)', (user_id, 'Unbookmarked', thesis_id))
        msg = "Removed from bookmarks."

    db.commit()
    
    return is_bookmarked, msg


def get_user_history_paginated(db, user_id, page, action_filter, date_filter, sort_order):
    filters = {'h.user_id': user_id}

    if action_filter:
        filters['h.action'] = action_filter
    if date_filter:
        filters['date(h.timestamp)'] = date_filter

    where_sql = "WHERE " + " AND ".join(f"{k} = ?" for k in filters.keys())
    params = list(filters.values())
    order_sql = "ASC" if sort_order == 'oldest' else "DESC"

    count_query = f"SELECT COUNT(*) FROM user_history h {where_sql}"
    
    main_query = f'''
        SELECT h.action, h.timestamp, t.id AS thesis_id, t.title 
        FROM user_history h
        LEFT JOIN thesis t ON h.thesis_id = t.id
        {where_sql} ORDER BY h.timestamp {order_sql}
    '''

    data, total_items, total_pages = fetch_paginated_data(db, main_query, count_query, params, page)
    return data, total_items, total_pages


def get_submission_form_options(db):
    programs = db.execute("SELECT id, name FROM department").fetchall()
    formats = db.execute("SELECT id, format FROM format").fetchall()
    branches = db.execute("SELECT id, name FROM branch").fetchall()
    return programs, formats, branches

def _process_contributors(db, thesis_id, person_data_list, role):
    config = {
        'author': {
            'table': 'author',
            'id_col': 'student_no',
            'map_table': 'thesis_author',
            'fk_col': 'author_id'
        },
        'advisor': {
            'table': 'advisor',
            'id_col': 'faculty_no',
            'map_table': 'thesis_advisor',
            'fk_col': 'advisor_id'
        }
    }
    
    c = config[role]
    
    for data in person_data_list:
        unique_val = data[c['id_col']]
        
        person = db.execute(
            f"SELECT id FROM {c['table']} WHERE {c['id_col']} = ?", 
            (unique_val,)
        ).fetchone()
        
        if person:
            person_id = person['id']
        else:
            query = db.execute(
                f"INSERT INTO {c['table']} (first_name, middle_name, last_name, {c['id_col']}) VALUES (?, ?, ?, ?)",
                (data['first_name'], data['middle_name'], data['last_name'], unique_val)
            )
            person_id = query.lastrowid
            
        db.execute(
            f"INSERT INTO {c['map_table']} (thesis_id, {c['fk_col']}) VALUES (?, ?)", 
            (thesis_id, person_id)
        )


def submit_thesis_transaction(db, uploader_id, file_path, date_published, author_data_list, advisor_data_list, thesis_data):
    temp_barcode = f"PENDING-BC-{uuid.uuid4().hex[:8].upper()}"
    temp_call_num = f"PENDING-CN-{uuid.uuid4().hex[:8].upper()}"

    try:
        query = db.execute("""
            INSERT INTO thesis (
                title, abstract, keywords, file_path, status, barcode, call_number, 
                department_id, branch_id, format_id, uploader_id, date_published
            ) VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?)
        """, (
            thesis_data['title'], thesis_data['abstract'], thesis_data['keywords'], 
            file_path, temp_barcode, temp_call_num, thesis_data['department_id'], 
            thesis_data['branch_id'], thesis_data['format_id'], uploader_id, date_published
        ))
        thesis_id = query.lastrowid

        _process_contributors(db, thesis_id, author_data_list, 'author')
        _process_contributors(db, thesis_id, advisor_data_list, 'advisor')

        db.execute("INSERT INTO user_history (user_id, action, thesis_id) VALUES (?, ?, ?)", (uploader_id, 'Submitted', thesis_id))

        db.commit()
        return True, None

    except Exception as e:
        db.rollback() 
        return False, str(e)
