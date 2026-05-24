import math
from datetime import date
from flask import session

def fetch_paginated_data(db, main_query, count_query, params, page, per_page=10):
    """Automatically paginates any SQL query."""
    total_items = db.execute(count_query, params).fetchone()[0]
   
    paginated_query = f"{main_query} LIMIT ? OFFSET ?"
    fetch_params = params + [per_page, (page - 1) * per_page]
    
    data = db.execute(paginated_query, fetch_params).fetchall()
    total_pages = max(1, math.ceil(total_items / per_page))
    
    return data, total_items, total_pages

def get_form_dropdown_options(db):
    """Fetches all dropdown options required for thesis forms."""
    departments = db.execute("SELECT id, name FROM department ORDER BY name").fetchall()
    formats = db.execute("SELECT id, format FROM format ORDER BY format").fetchall()
    branches = db.execute("SELECT id, name FROM branch ORDER BY name").fetchall()
    return departments, formats, branches

def track_daily_traffic(db, is_registered):
    """Bumps the daily traffic counter once per session per day."""
    today = str(date.today())
    
    # Only bump the counter if they haven't been counted today in this session
    if session.get('last_counted_date') != today:
        # Ensure a row exists for today
        db.execute('INSERT OR IGNORE INTO daily_traffic (visit_date) VALUES (?)', (today,))
        
        # Increment the correct column
        if is_registered:
            db.execute('UPDATE daily_traffic SET registered_visits = registered_visits + 1 WHERE visit_date = ?', (today,))
        else:
            db.execute('UPDATE daily_traffic SET guest_visits = guest_visits + 1 WHERE visit_date = ?', (today,))
            
        db.commit()
        session['last_counted_date'] = today
