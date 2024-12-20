from flask import Flask, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
from dash import Dash, html
from dash.dependencies import Output, Input
from dotenv import load_dotenv
import os
import modules.authorize

# Load environment variables
load_dotenv()

# Flask server setup
server = Flask(__name__)
server.secret_key = os.getenv("FLASK_SECRET_KEY")

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

# Dash layout
app.layout = html.Div([
    html.H1("Dash App with SSO Login"),
    html.Div(id="user-info"),
    html.A("Login with SSO", href="/login"),
    html.A("Logout", href="/logout", style={"marginLeft": "20px"}),
])

# Flask routes for login and logout 
@server.route("/login")
def login():
    redirect_uri = url_for("authorize", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@server.route("/authorize")
def authorize():
    return modules.authorize.authorize(oauth)
@server.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# Callback to display user info
@app.callback(
    Output("user-info", "children"),
    Input("user-info", "id")
)
def display_user_info(_):
    user = session.get("user")
    if user:
        return html.Div([
            html.Img(src=user.get("picture"), style={"height": "50px"}),
            html.Span(f"Welcome {user['name']} ({user['email']})!", style={"marginLeft": "10px"})
        ])
    else:
        return "You are not logged in."

if __name__ == '__main__':
    app.run(debug=True)