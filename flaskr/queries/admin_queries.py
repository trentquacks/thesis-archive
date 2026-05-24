from flaskr.queries.shared_queries import fetch_paginated_data

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
