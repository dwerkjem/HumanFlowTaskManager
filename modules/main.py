import os
import json
import dash
import redis
import random
import sys

from dash import Dash, html, dcc
from flask import Flask
import dash_bootstrap_components as dbc

from modules.custom_logger import create_logger
from modules.callbacks import register_callbacks

stylesheets = [
    dbc.themes.FLATLY,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css",
]

logger = create_logger()



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


register_callbacks(app, server, redis_client)