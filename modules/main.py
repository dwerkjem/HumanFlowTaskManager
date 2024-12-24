import os
import json
import redis
import random
import sys

from dash import Dash, html, dcc, Output, Input
from flask import Flask, session, redirect, url_for, request, g
from flask_limiter.util import get_remote_address


from modules.pages.nav_bar import create_nav_bar
if __name__ != "__main__":
    from modules.custom_logger import create_logger
else:
    from custom_logger import create_logger

logger = create_logger()

def load_credentials():
    try:
        with open('credentials.json') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading credentials: {e}")
        return {}

raw_credentials = load_credentials()

USER_PWD = {user_info['username']: user_info['password'] for user_info in raw_credentials.values()}
USER_GROUPS = {user_info['username']: user_info['group'] for user_info in raw_credentials.values()}

server = Flask(__name__)
server.secret_key = os.getenv("SECRET_KEY", str(random.randint(0, 1000000000)))

app = Dash(
    __name__,
    server=server,
    suppress_callback_exceptions=True,
    use_pages=True,
    pages_folder='pages'
)

# Redis config
redis_host = os.getenv('REDIS_HOST', 'redis')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_client = redis.Redis(host=redis_host, port=redis_port, db=0)

# Verify Redis
try:
    redis_client.ping()
    logger.info("Successfully connected to Redis.")
except redis.ConnectionError as e:
    logger.error(f"Failed to connect to Redis: {e}")

# Custom key function
def custom_key_func():
    """If IP is internal, exempt from rate limiting. Otherwise, use the remote IP."""
    remote_addr = get_remote_address()
    if (remote_addr.startswith('192.168.')):
        return None  # No rate limit for internal IP range
    return remote_addr


@server.before_request
def before_request():
    session.permanent = True
    if 'username' in session:
        session['group'] = USER_GROUPS.get(session['username'])
        logger.debug(f"User '{session['username']}' logged in with group '{session['group']}'.")


@server.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        ip = custom_key_func()

        # Check if user is locked out
        attempts_key = f"login_attempts:{ip}"
        attempts = redis_client.get(attempts_key)
        attempts = int(attempts) if attempts else 0

        if attempts >= 10:
            return "Too many failed login attempts. Please contact the administrator", 429

        if username in USER_PWD and USER_PWD[username] == password:
            # Successful login; reset attempts
            redis_client.delete(attempts_key)
            session['username'] = username
            session['group'] = USER_GROUPS.get(username)
            logger.info(f"User '{username}' logged in successfully.")
            return redirect(url_for('index'))
        else:
            new_attempts = redis_client.incr(attempts_key)
            if new_attempts == 1:
                # First failed attempt; set 1-hour expiry
                redis_client.expire(attempts_key, 3600)
            logger.warning("Invalid credentials.")
            return "Invalid credentials", 401

    return '''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    '''


@server.route('/logout')
def logout():
    try:
        username = session.pop('username', None)
        session.pop('group', None)
        logger.info(f"User '{username}' logged out.")
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return "Internal Server Error", 500
    return redirect(url_for('login'))


@server.route('/')
def index():
    return redirect(url_for('login'))


def clear_rate_limit(user_ip):
    # Same helper function you already had
    keys = redis_client.keys(f"LIMITER/{user_ip}/*")
    for key in keys:
        redis_client.delete(key)
    logger.info(f"Rate limits for {user_ip} cleared.")


app.layout = html.Div([
    create_nav_bar(),
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if 'username' not in session:
        logger.warning("Unauthorized access.")
        return html.Div([
            html.P("You are not logged in. Please login at "),
            html.A("Login", href="/login")
        ])
    
    group = session.get('group')
    if pathname == '/':
        if group == '0':
            return html.Div([
                html.P("Welcome Admin!"),
                html.A("Logout", href="/logout")
            ])
        elif group == '1':
            return html.Div([
                html.P("Welcome User!"),
                html.A("Logout", href="/logout")
            ])
    else:
        return html.Div([
            html.P("Invalid group. Please contact the administrator."),
        ])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'clear_rate_limit':
        if len(sys.argv) != 3:
            print("Usage: python main.py clear_rate_limit <user_ip>")
        else:
            user_ip = sys.argv[2]
            clear_rate_limit(user_ip)
    else:
        app.run_server(debug=False)