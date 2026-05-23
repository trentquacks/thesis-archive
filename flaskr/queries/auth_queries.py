from datetime import datetime, timedelta

def increment_failed_attempts(db, user_id):
    db.execute(
        'UPDATE user SET failed_attempts = failed_attempts + 1 WHERE id = ?',
        (user_id,)
    )
    db.commit()

def lock_user_account(db, user_id):
    lockout_time = datetime.now() + timedelta(minutes=10)
    db.execute(
        'UPDATE user SET lockout_until = ? WHERE id = ?',
        (lockout_time.strftime('%Y-%m-%d %H:%M:%S'), user_id)
    )
    db.commit()

def reset_failed_attempts(db, user_id):
    db.execute(
        'UPDATE user SET failed_attempts = 0, lockout_until = NULL WHERE id = ?',
        (user_id,)
    )
    db.commit()

def get_user_by_email(db, email):
    """Retrieves a user record by their email address."""
    return db.execute(
        'SELECT * FROM user WHERE email = ?', 
        (email,)
    ).fetchone()

def pause_user_borrows(db, user_id):
    """Pauses the countdown for any active thesis borrows for the user."""
    db.execute('''
        UPDATE active_borrow 
        SET time_left = MAX(0, time_left - CAST((strftime('%s', 'now') - strftime('%s', last_tick)) AS INTEGER)),
            is_paused = 1 
        WHERE user_id = ? AND is_paused = 0
    ''', (user_id,))
    db.commit()

def unpause_user_borrows(db, user_id):
    """Resumes the countdown for any paused thesis borrows for the user."""
    db.execute('''
        UPDATE active_borrow 
        SET last_tick = CURRENT_TIMESTAMP, is_paused = 0 
        WHERE user_id = ? AND is_paused = 1
    ''', (user_id,))
    db.commit()

