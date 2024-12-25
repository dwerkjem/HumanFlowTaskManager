import dash
from dash import html, dcc, callback, no_update
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from datetime import datetime
from modules.custom_logger import create_logger
from modules.customORM import CustomORM
from bson import ObjectId

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

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
        dismissable=True,  # Replace 'dismissible=True' with 'dismissable=True'
        duration=3000
    ),

    dcc.Interval(id='mongo-data-table-interval', interval=60*1000, n_intervals=0), # Update every 1 minute

    html.H1("Mood Journal"),
    dbc.Button("Add Entry", id="add-entry-button", color="primary", className="mb-1"),
    dbc.Modal(
        [
            dbc.ModalHeader("Add Entry"),
            dbc.ModalBody(
                [
                    dbc.Form(
                        [
                            dbc.Label("Date"),
                            dbc.Input(id="date-input", type="date", value=datetime.now().strftime("%Y-%m-%d"))
                        ]
                    ),
                    dbc.Form(
                        [
                            dbc.Label("Mood (Bad = 1, Good = 10)"),
                            dbc.Input(id="mood-input", type="number", min=1, max=10, step=1)
                        ]
                    ),
                    dbc.Form(
                        [
                            dbc.Label("Notes"),
                            dbc.Textarea(id="notes-input", placeholder="Enter notes here")
                        ]
                    )
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button("Submit", id="submit-entry-button", color="primary"),
                    dbc.Button("Close", id="close-entry-button", color="secondary")
                ]
            )
        ],
        id="add-entry-modal",
        is_open=False
    ),

    html.Div(id="mood_journal", children=[])
])

@callback(
    Output('db-alert', 'is_open'),
    Output('db-alert', 'children'),
    Output('db-alert', 'color'),
    Input('interval-component', 'n_intervals')
)
def update_alert(_):
    if CustomORM().check_connection_health():
        return False, "Connected to the database.", "success"
    else:
        return True, "Failed to connect to the database.", "danger"

def hide_alert(n_intervals):
    logger.info(f"hide_alert triggered with n_intervals={n_intervals}")
    return False if CustomORM().check_connection_health() else True

@callback(
    Output('add-entry-modal', 'is_open'),
    Output('date-input', 'value'),
    Output('mood-input', 'value'),
    Output('notes-input', 'value'),
    Input('add-entry-button', 'n_clicks'),
    Input('close-entry-button', 'n_clicks'),
    Input('submit-entry-button', 'n_clicks'),
    State('date-input', 'value'),
    State('mood-input', 'value'),
    State('notes-input', 'value'),
    prevent_initial_call=True
)
def handle_modal(add_clicks, close_clicks, submit_clicks, date_val, mood_val, notes_val):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'add-entry-button':
        # Open modal, reset fields
        return True, datetime.now().strftime("%Y-%m-%d"), 5, ""
    elif button_id == 'close-entry-button':
        # Close modal
        return False, date_val, mood_val, notes_val
    elif button_id == 'submit-entry-button':
        # Close modal after submission; reset fields or keep them
        return False, datetime.now().strftime("%Y-%m-%d"), 5, ""
    raise dash.exceptions.PreventUpdate


@callback(
    Output('mood_journal', 'children'),
    [
        Input('mongo-data-table-interval', 'n_intervals'),
        Input('submit-entry-button', 'n_clicks')
    ],
    [
        State('date-input', 'value'),
        State('mood-input', 'value'),
        State('notes-input', 'value')
    ],
    prevent_initial_call=True
)
def refresh_mood_journal(_n_intervals, submit_clicks, date_val, mood_val, notes_val):
    # Guard: if DB is offline, just return an empty list
    if not CustomORM().check_connection_health():
        return []

    ctx = dash.callback_context
    if ctx.triggered and ctx.triggered[0]['prop_id'].startswith('submit-entry-button'):
        # Insert new entry if valid
        if date_val and mood_val:
            CustomORM().db["mood_journal"].insert_one({
                "date": date_val,
                "mood": mood_val,
                "notes": notes_val or ""
            })

    # Query the collection
    mood_journal = CustomORM().query_collection("mood_journal")

    # Convert any ObjectIds to strings to avoid JSON serialization errors
    if mood_journal:
        for doc in mood_journal:
            if "_id" in doc and isinstance(doc["_id"], ObjectId):
                doc["_id"] = str(doc["_id"])

        # Build a simple table (or use dbc.Table.from_dataframe if you want a DataFrame)
        return [dbc.Table(
            # If mood_journal is a list of dicts, you can manually build rows,
            # or convert to a DataFrame. Here's a quick manual approach:
            children=[
                html.Thead(html.Tr([html.Th(col) for col in mood_journal[0].keys()])),
                html.Tbody([
                    html.Tr([html.Td(item[col]) for col in item.keys()])
                    for item in mood_journal
                ])
            ],
            striped=True,
            bordered=True,
            hover=True
        )]

    # If empty, return an empty list
    return []

