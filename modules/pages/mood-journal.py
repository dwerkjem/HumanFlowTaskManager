import dash
from dash import html, dcc, callback
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, ALL
from datetime import datetime
from modules.custom_logger import create_logger
from modules.customORM import CustomORM
from bson import ObjectId
import json

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

    dcc.Interval(id='mongo-data-table-interval', interval=60*1000, n_intervals=0), # Update every 1 minute

    html.H1("Mood Journal"),
    
    html.Div(
        [
            dbc.Button("Add Entry", id="add-entry-button", color="primary"),
            dbc.Button("Refresh", id="refresh-button", color="primary")
        ],
        className="d-grid gap-2"
    ),
    
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
                            dbc.Label("Mood Slider (Devastated = 1, Ecstatic = 10)"),
                            dcc.Slider(
                                id='mood-slider',
                                min=1,
                                max=10,
                                step=1,
                                marks={
                                    1: "Devastated",
                                    2: "Very Sad",
                                    3: "Sad",
                                    4: "Down",
                                    5: "Neutral",
                                    6: "Okay",
                                    7: "Content",
                                    8: "Happy",
                                    9: "Excited",
                                    10: "Ecstatic"
                                },
                                value=5
                            )
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
    Output('mood-slider', 'value'),
    Output('notes-input', 'value'),
    Input('add-entry-button', 'n_clicks'),
    Input('close-entry-button', 'n_clicks'),
    Input('submit-entry-button', 'n_clicks'),
    State('date-input', 'value'),
    State('mood-slider', 'value'),
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
        Input('submit-entry-button', 'n_clicks'),
        Input('refresh-button', 'n_clicks'),
        Input({'type': 'delete-button', 'index': ALL}, 'n_clicks')
    ],
    [
        State('date-input', 'value'),
        State('mood-slider', 'value'),
        State('notes-input', 'value')
    ],
    prevent_initial_call=True
)
def refresh_mood_journal(_n_intervals, submit_clicks, refresh_clicks, delete_clicks, date_val, mood_val, notes_val):
    # Guard: if DB is offline, just return an empty list
    if not CustomORM().check_connection_health():
        return []

    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered_prop_id = ctx.triggered[0]['prop_id']
    triggered = {}

    if 'submit-entry-button' in triggered_prop_id:
        triggered = {'type': 'submit-entry-button', 'index': ''}
    elif triggered_prop_id.startswith("{"):
        try:
            # Correctly parse the JSON part before the dot
            triggered = json.loads(triggered_prop_id.split('.')[0])
        except json.JSONDecodeError:
            triggered = {'type': '', 'index': ''}
    else:
        triggered = {'type': triggered_prop_id, 'index': ''}

    if triggered.get('type') == 'submit-entry-button' and date_val and mood_val:
        CustomORM().db["mood_journal"].insert_one({
            "date": date_val,
            "mood": mood_val,
            "notes": notes_val or ""
        })
        logger.info("Added new mood journal entry.")

    elif triggered.get('type') == 'delete-button':
        delete_id = triggered.get('index')
        if isinstance(delete_id, str) and ObjectId.is_valid(delete_id):
            CustomORM().db["mood_journal"].delete_one({"_id": ObjectId(delete_id)})
            logger.info(f"Deleted entry with ObjectId: {delete_id}")
        else:
            logger.error(f"Invalid ObjectId: {delete_id}")

    # For refresh-button or mongo-data-table-interval, just re-query
    mood_journal = CustomORM().query_collection("mood_journal")
    if mood_journal:
        for doc in mood_journal:
            if "_id" in doc and isinstance(doc["_id"], ObjectId):
                doc["_id"] = str(doc["_id"])

        # Exclude the _id column
        columns = [col for col in mood_journal[0].keys() if col != "_id"]

        return [
            dbc.Table(
                children=[
                    html.Thead(
                        html.Tr([html.Th(col) for col in columns] + [html.Th("Actions")])
                    ),
                    html.Tbody([
                        html.Tr(
                            [html.Td(row.get(col, 'N/A')) for col in columns]
                            + [
                                html.Td(
                                    dbc.Button(
                                        "Delete",
                                        id={"type": "delete-button", "index": row["_id"]},
                                        color="danger",
                                        size="sm"
                                    )
                                )
                            ]
                        ) for row in mood_journal
                    ])
                ],
                bordered=True,
                hover=True,
                responsive=True,
                striped=True
            )
        ]
    return []