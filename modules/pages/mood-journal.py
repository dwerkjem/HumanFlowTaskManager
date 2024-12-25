import dash
from dash import html
import dash_bootstrap_components as dbc
from datetime import datetime

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

from modules.custom_logger import create_logger
from modules.customORM import CustomORM
from dash import html, dcc
from dash.dependencies import Output, Input

dash.register_page(__name__)

logger = create_logger()

if CustomORM().check_connection_health():
    CustomORM().make_collection_if_not_exists("mood_journal")

    mood_journal = CustomORM().query_collection("mood_journal")
else:
    mood_journal = None

layout = html.Div([
    dcc.Interval(id='interval-component', interval=10000, n_intervals=0),
    dbc.Alert(
        id="db-alert",
        children="Failed to connect to the database." if not CustomORM().check_connection_health() else "Connected to the database.",
        color="danger" if not CustomORM().check_connection_health() else "success",
        is_open=True,
        dismissable=True,
        duration=3000
    ),

    dcc.Interval(id='mongo-datatable-interval', interval=60*1000, n_intervals=0), # Update every 1 minute

    html.H1("mood_journal"),
    dbc.Button("Save To Database", id="save-button", color="success", className="mb-3"),
    dbc.Button("Add Entry", id="add-entry-button", color="primary", className="mb-3"),    

    html.Div(id="mood_journal", children=[])
])

@app.callback(
    Output('db-alert', 'is_open'),
    Output('db-alert', 'children'),
    Output('db-alert', 'color'),
    Input('interval-component', 'n_intervals')
)
def update_alert(n_intervals):
    if CustomORM().check_connection_health():
        return False, "Connected to the database.", "success"
    else:
        return True, "Failed to connect to the database.", "danger"

def hide_alert(n_intervals):
    logger.info(f"hide_alert triggered with n_intervals={n_intervals}")
    return False if CustomORM().check_connection_health() else True
