import configparser
import requests
import os
from dotenv import load_dotenv
from flask import Flask, redirect, url_for, session
from jose import jwt, JWTError
from authlib.integrations.flask_client import OAuth
from dash import Dash, html
from dash.dependencies import Output, Input

# Load environment variables
load_dotenv()

# Flask server setup
server = Flask(__name__)
server.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))

# Secure session cookies
server.config.update(
    SESSION_COOKIE_SECURE=True,  # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,  # Not accessible via JavaScript
    SESSION_COOKIE_SAMESITE='Lax'  # Prevent CSRF
)

# OAuth setup
oauth = OAuth(server)

# Configure the third-party SSO provider (Google in this example)
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    client_kwargs={"scope": "openid email profile"},
)

# Dash app setup
app = Dash(__name__, server=server, suppress_callback_exceptions=True)

# Read authorized emails from config.ini
config = configparser.ConfigParser()
config.read('config.ini')
authorized_admin_emails = config.get('AUTH', 'authorized_admin_emails').split(',')
authorized_viewer_emails = config.get('AUTH', 'authorized_viewer_emails').strip('{}').split(',')

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
        html.H2("Welcome to the Human Flow Task Manager"),
    ], style={"marginTop": "20px"})
])

# Flask routes for login and logout 
@server.route("/login")
def login():
    redirect_uri = url_for("authorize", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@server.route("/authorize")
def authorize():
    token_response = oauth.google.authorize_access_token()
    id_token = token_response.get('id_token')
    if not id_token:
        return "ID token not found in the response.", 400

    try:
        # Fetch Google's public keys
        jwks_url = "https://www.googleapis.com/oauth2/v3/certs"
        jwks = requests.get(jwks_url).json()

        # Get key ID from token header
        header = jwt.get_unverified_header(id_token)
        kid = header['kid']

        # Find the matching public key
        key = None
        for jwk in jwks['keys']:
            if jwk['kid'] == kid:
                key = jwk
                break

        if not key:
            return "Matching public key not found", 400

        # Construct the public key
        from jose import jwk
        from jose.utils import base64url_decode

        public_key = jwk.construct(key)
        message, encoded_signature = id_token.rsplit('.', 1)
        decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))

        # Verify the signature
        if not public_key.verify(message.encode("utf-8"), decoded_signature):
            return "Signature verification failed.", 400

        # Decode and verify the ID token
        decoded_token = jwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=os.getenv("GOOGLE_CLIENT_ID"),
            issuer="https://accounts.google.com",
            options={"verify_at_hash": False}  # Disable at_hash verification
        )

        # Store user information
        session["user"] = {
            "name": decoded_token.get("name"),
            "email": decoded_token.get("email"),
            "picture": decoded_token.get("picture"),
        }

        return redirect("/")

    except (JWTError, StopIteration) as e:
        return f"Token verification failed: {str(e)}", 400

@server.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

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
        return "Login with Google", "/login"

# Callback to display user info and authorization level
@app.callback(
    Output("user-info", "children"),
    Input("user-info", "id")
)
def display_user_info(_):
    user = session.get("user")
    if user:
        email = user.get("email")
        if email in authorized_admin_emails:
            role = "Admin"
        elif email in authorized_viewer_emails:
            role = "Viewer"
        else:
            role = "Unauthorized"

        return html.Div([
            html.Img(src=user.get("picture"), style={"height": "50px"}),
            html.Span(f"Welcome {user['name']} ({user['email']})! Role: {role}", style={"marginLeft": "10px"})
        ])
    else:
        return "You are not logged in."

if __name__ == '__main__':
    app.run(debug=True)