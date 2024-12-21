from flask import Flask, redirect, url_for, session, jsonify, request
from authlib.integrations.flask_client import OAuth
from dash import Dash, html, dcc
from pathlib import Path
from dash.dependencies import Output, Input
from dotenv import load_dotenv
import os

# Load environment variables from .env file
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)


# Flask server setup
server = Flask(__name__)
server.secret_key = os.getenv("FLASK_SECRET_KEY")

# Configure server-side session management
server.config["SESSION_TYPE"] = "filesystem"

# Secure session cookies
server.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
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
    requested_address = str(os.getenv("USER_HOST", "127.0.0.1"))
    requested_port = str(os.getenv("USER_PORT", 8050))
    app.run(debug=True, host=requested_address, port=requested_port)