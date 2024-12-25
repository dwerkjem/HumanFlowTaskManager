import dash
from dash import html
import dash_bootstrap_components as dbc

from modules.custom_logger import create_logger
from modules.customORM import CustomORM

dash.register_page(__name__)


logger = create_logger()

if CustomORM().check_connection_health():
    CustomORM().make_collection_if_not_exists("journal")

    journal = CustomORM().query_collection("journal")
else:
    journal = None

layout = html.Div([
    dbc.Alert(
        "Failed to connect to the database." if not CustomORM().check_connection_health() else "Connected to the database.",
        color="danger" if not CustomORM().check_connection_health() else "success"
    ),
    html.Div(id="journal", children=[])
])