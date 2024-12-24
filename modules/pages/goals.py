import dash
import dash_bootstrap_components as dbc
from dash import html

from modules.custom_logger import create_logger

dash.register_page(__name__)

logger = create_logger()

layout = html.Div([
    html.H1("Welcome to Human Flow Task Manager")
    
])