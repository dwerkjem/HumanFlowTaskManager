import os
import json
import redis

from dash import Dash, html, dcc, Output, Input
from dash_auth import BasicAuth
from flask import Flask, session, redirect, url_for, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from modules.custom_logger import create_logger
from modules.human_hash import generate_human_readable_hash as human_hash

logger = create_logger()

# Load user credentials from JSON file
with open('credentials.json') as f:
    raw_credentials = json.load(f)

# Extract usernames and passwords for BasicAuth
USER_PWD = {user_info['username']: user_info['password'] for user_info in raw_credentials.values()}

# Extract group information
USER_GROUPS = {user_info['username']: user_info['group'] for user_info in raw_credentials.values()}

server = Flask(__name__)
server.secret_key = os.getenv("SECRET_KEY", "supersecretkey")
app = Dash(__name__, server=server, suppress_callback_exceptions=True)

BasicAuth(app, USER_PWD)

# Initialize Redis client
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Initialize Flask-Limiter with Redis storage
limiter = Limiter(
    get_remote_address,
    app=server,
    storage_uri="redis://localhost:6379",
    default_limits=["200 per day", "50 per hour"]
)

@app.server.before_request
def before_request():
    session.permanent = True
    if 'username' in session:
        session['group'] = USER_GROUPS.get(session['username'])
        logger.debug(f"User '{session['username']}' logged in with group '{session['group']}'.")

@app.server.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
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
            logger.warning(f"Invalid login attempt for username '{username}'.")
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

@app.server.route('/')
def index():
    return app.index()

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
        return html.Div("Welcome Admin!")
    elif group == '1':
        return html.Div("Welcome User!")
    else:
        return html.Div("Unauthorized access.")

if __name__ == "__main__":
    app.run_server(debug=True)