import functools

from datetime import datetime 
from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from werkzeug.security import check_password_hash
from flaskr import oauth
from flaskr.db import get_db
from flaskr.queries.shared_queries import track_daily_traffic
from flaskr.queries.auth_queries import get_user_by_email, increment_failed_attempts, lock_user_account, reset_failed_attempts, unpause_user_borrows, pause_user_borrows

bp = Blueprint("auth", __name__, url_prefix="/auth")

def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    db = get_db()
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = (
            get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        )
        if g.user and g.user['role'] == 'admin':
            result = db.execute("SELECT COUNT(id) as count FROM thesis WHERE status = 'pending'").fetchone()
            g.pending_count = result['count'] if result else 0
        else:
            g.pending_count = 0

    track_daily_traffic(db, is_registered=(g.user is not None))

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None
        
        user = get_user_by_email(db, email) 
        
        if user is None:
            error = 'Incorrect email or password.'
        else:
            if user['lockout_until']:
                lockout_time = datetime.strptime(user['lockout_until'], '%Y-%m-%d %H:%M:%S')
                if datetime.now() < lockout_time:
                    # lockout status display
                    time_left = int((lockout_time - datetime.now()).total_seconds() / 60) or 1
                    error = f'Account locked due to multiple failed attempts. Try again in {time_left} minute(s).'
                else:
                    # allow login after 10 minutes
                    reset_failed_attempts(db, user['id'])
                    user = get_user_by_email(db, email) # refresh the user dictionary
            
            # validate password
            if error is None:
                if not check_password_hash(user['password'], password):
                    error = 'Incorrect email or password.'
                    increment_failed_attempts(db, user['id'])
                    
                    # if wrong attempt 5 times
                    updated_user = get_user_by_email(db, email)
                    if updated_user['failed_attempts'] >= 5:
                        lock_user_account(db, user['id'])
                        error = 'Account locked due to 5 failed attempts. Try again in 10 minutes.'
                else:
                    reset_failed_attempts(db, user['id'])
                    session.clear()
                    session['user_id'] = user['id']
                    unpause_user_borrows(db, user['id'])

                    db.execute("INSERT INTO user_history (user_id, action) VALUES (?, ?)", (user['id'], 'Logged In'))
                    db.commit()

                    return redirect(url_for('index'))
                    
        if error:
            flash(error, 'error')
            
    return render_template('auth/login.html')

@bp.route('/login/google')
def google_login():
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri, hd='cvsu.edu.ph', prompt='select_account')

@bp.route('/auth/google/callback')
def google_callback():
    from flaskr import oauth
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')
    
    email = user_info.get('email')
    first_name = user_info.get('given_name', '')
    last_name = user_info.get('family_name', '')
    
    if not email.endswith('@cvsu.edu.ph'):
        flash("Only @cvsu.edu.ph emails are allowed.", "error")
        return redirect(url_for('auth.login'))

    db = get_db()
    user = get_user_by_email(db, email)

    if user is None:
        session['oauth_email'] = email
        session['oauth_first_name'] = first_name
        session['oauth_last_name'] = last_name
        return redirect(url_for('auth.complete_profile'))

    # if user exists, log them in
    session.clear()
    session['user_id'] = user['id']
    
    unpause_user_borrows(db, user['id'])

    db.execute("INSERT INTO user_history (user_id, action) VALUES (?, ?)", (user['id'], 'Logged In via Google'))
    db.commit()

    flash('Successfully logged in!', 'success')
    return redirect(url_for('index'))

@bp.route('/complete-profile', methods=('GET', 'POST'))
def complete_profile():
    email = session.get('oauth_email')
    first_name = session.get('oauth_first_name')
    last_name = session.get('oauth_last_name')

    if not email:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        student_no = request.form['student_no']
        course = request.form['course']
        
        db = get_db()
        error = None

        if not student_no:
            error = 'Student number is required.'
        elif not course:
            error = 'Course is required.'

        if error is None:
            try:
                # insert the user with preferably a unhackable random password..
                dummy_password = '!OAUTH_LOGIN_ONLY!' 
                db.execute(
                    "INSERT INTO user (first_name, last_name, email, password, student_no, course) VALUES (?, ?, ?, ?, ?, ?)",
                    (first_name, last_name, email, dummy_password, student_no, course),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {email} is already registered."
            else:
                user = get_user_by_email(db, email)
                
                # clear temp OAuth data
                session.pop('oauth_email', None)
                session.pop('oauth_first_name', None)
                session.pop('oauth_last_name', None)
                
                # log the user in
                session.clear()
                session['user_id'] = user['id']

                db.execute("INSERT INTO user_history (user_id, action) VALUES (?, ?)", (user['id'], 'Logged In via Google'))
                db.commit()

                flash('Account created successfully!', 'success')
                return redirect(url_for("index"))

        if error:
            flash(error, 'error')

    return render_template('auth/complete_profile.html', email=email, first_name=first_name, last_name=last_name)

@bp.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    user_id = session.get("user_id")
    
    if user_id:
        db = get_db()
        pause_user_borrows(db, user_id)
        db.execute("INSERT INTO user_history (user_id, action) VALUES (?, ?)", (user_id, 'Logged Out'))
        db.commit()
        
    session.clear()
    return redirect(url_for("index"))
