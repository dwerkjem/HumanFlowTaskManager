import os
import redis
from flask import Flask, redirect, url_for, session, jsonify, request
from flask_session import Session
from authlib.integrations.flask_client import OAuth
from dash import Dash, html, dcc
from dash.dependencies import Output, Input
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# Print loaded environment variables for debugging
print("USER_HOST from env:", os.getenv("USER_HOST"))
print("USER_PORT from env:", os.getenv("USER_PORT"))

# Flask server setup
server = Flask(__name__)
server.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback")

# Configure server-side session management
server.config["SESSION_TYPE"] = "redis"
server.config["SESSION_PERMANENT"] = False
server.config["SESSION_USE_SIGNER"] = True
server.config["SESSION_REDIS"] = redis.Redis(host="redis", port=6379)
Session(server)

# Initialize Redis client with Docker service name
redis_host = os.getenv('REDIS_HOST', 'redis')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_client = redis.Redis(host=redis_host, port=redis_port, db=0)

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
    storage_uri=f"redis://{redis_host}:{redis_port}/0",
    app=server,
)

# OAuth configuration
oauth = OAuth(server)
auth0 = oauth.register(
    name="auth0",
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{os.getenv('AUTH0_DOMAIN')}/.well-known/openid-configuration",
)

# Dash app setup
app = Dash(__name__, server=server, suppress_callback_exceptions=True)

# Navbar layout
navbar = html.Nav(
    className="navbar",
    children=[
        html.Div(
            className="navbar-container",
            children=[
                html.A("Home", href="/", className="navbar-link"),
                html.A(id="login-logout-link", className="navbar-link", style={"marginLeft": "20px"}),
            ]
        )
    ]
)

# Dash layout
app.layout = html.Div([
    navbar,
    html.Div(id="user-info"),
    html.Div([
        html.H2("Welcome to the Authenticated Task Manager"),
    ], style={"marginTop": "20px"})
])

# Flask routes for Auth0 login and logout
@server.route("/login")
def login():
    redirect_uri = url_for("authorize", _external=True)
    nonce = os.urandom(24).hex()
    session["auth0_nonce"] = nonce
    return auth0.authorize_redirect(redirect_uri=redirect_uri, nonce=nonce)

@server.route("/authorize")
def authorize():
    token = auth0.authorize_access_token()
    nonce = session.pop("auth0_nonce", None)
    user_info = auth0.parse_id_token(token, nonce=nonce)
    session["user"] = user_info
    return redirect("/")

@server.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(f"https://{os.getenv('AUTH0_DOMAIN')}/v2/logout?returnTo={url_for('index', _external=True)}&client_id={os.getenv('AUTH0_CLIENT_ID')}")

@server.route("/")
def index():
    return app.index()

# Callback to update the login/logout link in the navbar
@app.callback(
    Output("login-logout-link", "children"),
    Output("login-logout-link", "href"),
    Input("user-info", "children")
)
def update_navbar(_):
    if session.get("user"):
        return "Logout", "/logout"
    else:
        return "Login", "/login"

# Callback to display user info
@app.callback(
    Output("user-info", "children"),
    Input("user-info", "id")
)
def display_user_info(_):
    user = session.get("user")
    if user:
        name = user.get("name") or user.get("email") or "User"
        return f"Welcome, {name}!"
    else:
        return "You are not logged in."

if __name__ == "__main__":
    requested_address = os.getenv("USER_HOST", "0.0.0.0")
    requested_port = int(os.getenv("APP_PORT_CONTAINER", 8050))
    print(f"Starting server at {requested_address}:{requested_port}")
    app.run_server(debug=True, host=requested_address, port=requested_port)