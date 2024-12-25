import dash
from dash import html, dcc

import dash_bootstrap_components as dbc
import time

from modules.custom_logger import create_logger

dash.register_page(__name__)


logger = create_logger()

