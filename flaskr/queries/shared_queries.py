import math

def fetch_paginated_data(db, main_query, count_query, params, page, per_page=10):
    """Automatically paginates any SQL query."""
    total_items = db.execute(count_query, params).fetchone()[0]
   
    paginated_query = f"{main_query} LIMIT ? OFFSET ?"
    fetch_params = params + [per_page, (page - 1) * per_page]
    
    data = db.execute(paginated_query, fetch_params).fetchall()
    total_pages = max(1, math.ceil(total_items / per_page))
    
    return data, total_items, total_pages
