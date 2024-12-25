import os
import json
import dash
import redis
import random
import sys

from dash import Dash, html, dcc, Output, Input
from flask import Flask, session, redirect, url_for, request, g
from flask_limiter.util import get_remote_address
import dash_bootstrap_components as dbc

from modules.custom_logger import create_logger

stylesheets = [dbc.themes.FLATLY]

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
    pages_folder='pages',
    title='Dash App',
    update_title='Loading...',
    external_stylesheets=stylesheets
)

app.layout = html.Div(
    [
        dbc.NavbarSimple(
            children=[
                dbc.NavItem(dbc.NavLink("Home", href="/", active="exact")),
                dbc.NavItem(dbc.NavLink("Goals", href="/goals", active="exact")),
                dbc.NavItem(dbc.NavLink("Mood Journal", href="/mood-journal", active="exact")),
                dbc.NavItem(dbc.NavLink("Tasks", href="/tasks", active="exact")),
                dbc.NavItem(dbc.NavLink("Logout", id="logout-link")),
                dbc.Label(className="fa fa-moon", html_for="switch"),
                dbc.Switch(id="switch", value=True, className="d-inline-block ms-1", persistence=True),
                dbc.Label(className="fa fa-sun", html_for="switch"),
            ],
            brand="Human Flow Task Manager",
            brand_href="/",
            color="primary",
            dark=True,
            expand="lg",
        ),
        # Hidden Div for clientside callback
        html.Div(id='theme-output', style={'display': 'none'}),
        dcc.Location(id='url', refresh=False),
        # Page content will be rendered by the callback
        dash.page_container,
    ]
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

@server.before_request
def before_request():
    session.permanent = True

    if 'username' in session:
        session['group'] = USER_GROUPS.get(session['username'])
        g.username = session['username']
        g.group = session['group']
    else:
        g.username = None
        g.group = None
    if request.endpoint not in ('login', 'static', 'logout') and 'username' not in session:
        return redirect(url_for('login'))

@server.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        ip = get_remote_address()

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
    """
    Log the user out and redirect them to the /login page.
    """
    try:
        username = session.pop('username', None)
        session.pop('group', None)
        logger.info(f"User '{username}' logged out successfully.")
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return "Error during logout", 500

@server.route('/')
def index():
    """
    If user is logged in, load the main dash content; otherwise, redirect to login page.
    """
    if 'username' not in session:
        return redirect(url_for('login'))
    else:
        return redirect('/pages/index')  # Adjusted to point to the Dash page

def clear_rate_limit(user_ip):
    # Same helper function you already had
    keys = redis_client.keys(f"LIMITER/{user_ip}/*")
    for key in keys:
        redis_client.delete(key)
    logger.info(f"Rate limits for {user_ip} cleared.")

# Protect Dash Routes with Client-Side Callback
app.clientside_callback(
    """
    function(switchOn) {
        document.documentElement.setAttribute("data-bs-theme", switchOn ? "light" : "dark"); 
        return window.dash_clientside.no_update;
    }
    """,
    Output("theme-output", "children"),  # Correct Output
    Input("switch", "value"),
)

@app.callback(
    [Output('url', 'pathname'), Output('url', 'refresh')],
    [Input('logout-link', 'n_clicks')]
)
def logout_user(n_clicks):
    if n_clicks:
        session.pop('username', None)
        session.pop('group', None)
        logger.info(f"User logged out successfully.")
        # Return both the new pathname and `True` to force a page reload.
        return '/login', True
    return dash.no_update, dash.no_update