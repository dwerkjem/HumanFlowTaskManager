import dash
from dash import html

from modules.pages.nav_bar import create_nav_bar

dash.register_page(__name__, path="/", title="Home")

layout = html.Div([
    create_nav_bar(),
    html.H1("Welcome to the home page!")
])
