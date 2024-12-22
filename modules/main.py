import os
import json
import redis
from dash import Dash, html, dcc, Output, Input
from flask import Flask, session, redirect, url_for, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import random
import sys

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

# Extract usernames and passwords for BasicAuth
USER_PWD = {user_info['username']: user_info['password'] for user_info in raw_credentials.values()}

# Extract group information
USER_GROUPS = {user_info['username']: user_info['group'] for user_info in raw_credentials.values()}

server = Flask(__name__)
server.secret_key = os.getenv("SECRET_KEY", random.randint(0, 1000000000))
app = Dash(__name__, 
           server=server, 
           suppress_callback_exceptions=True, 
           use_pages=True,
           pages_folder="pages")  # Update path to absolute

# Initialize Redis client with Docker service name
redis_host = os.getenv('REDIS_HOST', 'redis')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_client = redis.Redis(host=redis_host, port=redis_port, db=0)

# Verify Redis connection
try:
    redis_client.ping()
    logger.info("Successfully connected to Redis.")
except redis.ConnectionError as e:
    logger.error(f"Failed to connect to Redis: {e}")

# Custom key function for rate limiting
def custom_key_func():
    remote_addr = get_remote_address()
    # Assuming the internal network IP range is 192.168.0.0/16
    if remote_addr.startswith('192.168.'):
        return None  # No rate limiting for internal network
    return remote_addr

# Initialize Flask-Limiter with Redis storage and custom key function
limiter = Limiter(
    key_func=custom_key_func,
    app=server,
    storage_uri=f"redis://{redis_host}:{redis_port}",
    default_limits=["200 per day", "50 per hour"]
)

@app.server.before_request
def before_request():
    session.permanent = True
    if 'username' in session:
        session['group'] = USER_GROUPS.get(session['username'])
        logger.debug(f"User '{session['username']}' logged in with group '{session['group']}'.")

@app.server.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute", key_func=custom_key_func)
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in USER_PWD and USER_PWD[username] == password:
            session['username'] = username
            session['group'] = USER_GROUPS.get(username)
            logger.info(f"User '{username}' logged in successfully.")
            return redirect(url_for('index'))
        else:
            logger.warning("Invalid credentials.")
            return "Invalid credentials", 401
    
    return '''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    '''

@app.server.route('/logout')
def logout():
    username = session.pop('username', None)
    session.pop('group', None)
    logger.info(f"User '{username}' logged out.")
    return redirect(url_for('index'))

def clear_rate_limit(user_ip):
    keys = redis_client.keys(f"LIMITER/{user_ip}/*")
    for key in keys:
        redis_client.delete(key)
    logger.info(f"Rate limits for {user_ip} cleared.")

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Example callback to demonstrate group-based access control
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
