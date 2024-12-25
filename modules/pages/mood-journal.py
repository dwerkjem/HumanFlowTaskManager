import dash
from dash import html, dcc, callback, no_update
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, MATCH, ALL
from datetime import datetime
from modules.custom_logger import create_logger
from modules.customORM import CustomORM
from bson import ObjectId
import json

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

dash.register_page(__name__)

logger = create_logger()

# Ensure collection exists
if CustomORM().check_connection_health():
    CustomORM().make_collection_if_not_exists("mood_journal")
    mood_journal = CustomORM().query_collection("mood_journal")
else:
    mood_journal = None

layout = html.Div([
    dcc.Interval(id='interval-component', interval=10000, n_intervals=0),
    dbc.Alert(
        id="db-alert",
        # Initially show either success/failure message
        children=(
            "Failed to connect to the database."
            if not CustomORM().check_connection_health() else
            "Connected to the database."
        ),
        color=(
            "danger"
            if not CustomORM().check_connection_health() else
            "success"
        ),
        is_open=True,
        dismissable=True,
        duration=3000
    ),

    # Update every 15 seconds
    dcc.Interval(id='mongo-data-table-interval', interval=15*1000, n_intervals=0), 

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
                            dbc.Input(
                                id="date-input",
                                type="date",
                                value=datetime.now().strftime("%Y-%m-%d"),
                                readonly=True
                            )
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
    [
        Input('interval-component', 'n_intervals'),
        Input({'type': 'delete-btn', 'row_id': ALL}, 'n_clicks')
    ],
    prevent_initial_call=True
)
def handle_db_alert(n_intervals, delete_clicks):
    """
    A merged callback that:
      - Checks DB connection every 10s (interval-component).
      - Shows a "Deleted entry with ID" message when a delete button is clicked.

    Because Dash does NOT allow multiple callbacks with the same outputs,
    we handle both events here in one callback.
    """

    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered = ctx.triggered[0]["prop_id"].split(".")[0]

    # If the DB check interval triggered this callback:
    if triggered == "interval-component":
        if CustomORM().check_connection_health():
            return (False, "Connected to the database.", "success")
        else:
            return (True, "Failed to connect to the database.", "danger")

    # Otherwise, it must be a delete button
    try:
        button_id = json.loads(triggered)  # e.g. {"type":"delete-btn","row_id":"someID"}
        row_id = button_id.get("row_id")
        # We show a quick alert that the entry was deleted.
        return (True, f"Deleted entry with ID: {row_id}", "warning")
    except Exception as e:
        # If somehow not JSON or missing row_id
        logger.error(f"Error parsing delete button ID: {e}")
        return no_update, no_update, no_update

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
def handle_modal(add_clicks, close_clicks, submit_clicks,
                 date_val, mood_val, notes_val):
    """
    Single callback to handle the modal open, close, and field reset on submit.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'add-entry-button':
        # Open the modal & reset fields to default
        return True, datetime.now().strftime("%Y-%m-%d"), 5, ""
    elif button_id == 'close-entry-button':
        # Close modal, keep the current form values
        return False, date_val, mood_val, notes_val
    elif button_id == 'submit-entry-button':
        # Close modal after submission & reset form
        return False, datetime.now().strftime("%Y-%m-%d"), 5, ""
    raise dash.exceptions.PreventUpdate


@callback(
    Output('mood_journal', 'children'),
    [
        Input('mongo-data-table-interval', 'n_intervals'),
        Input('submit-entry-button', 'n_clicks'),
        Input('refresh-button', 'n_clicks'),
        Input({'type': 'delete-btn', 'row_id': ALL}, 'n_clicks')
    ],
    [
        State('date-input', 'value'),
        State('mood-slider', 'value'),
        State('notes-input', 'value')
    ],
    prevent_initial_call=True
)
def refresh_mood_journal(_n_intervals, submit_clicks, refresh_clicks, delete_clicks,
                         date_val, mood_val, notes_val):
    """
    This callback handles:
      - Polling (interval)
      - Submitting a new entry
      - Refreshing the table
      - Deleting an entry

    Then it rebuilds the table with the latest data.
    """
    # If DB is offline, just return an empty list
    if not CustomORM().check_connection_health():
        logger.error("Database connection failed.")
        return []

    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered = ctx.triggered[0]['prop_id'].split('.')[0]

    # 1) If "Submit" was clicked, insert a new doc
    if triggered == 'submit-entry-button' and date_val and mood_val is not None:
        try:
            CustomORM().db["mood_journal"].insert_one({
                "Date": date_val,
                "Mood": mood_val,
                "Notes": notes_val or ""
            })
            logger.info(f"Inserted new entry: Date={date_val}, Mood={mood_val}, Notes={notes_val}")
        except Exception as e:
            logger.error(f"Error inserting new entry: {e}")
            return no_update

    # 2) If "Refresh" was clicked, just log it (re-query below)
    elif triggered == 'refresh-button':
        logger.info("Refresh button clicked.")

    # 3) If a delete button was clicked, remove that doc by _id
    elif isinstance(triggered, str) and triggered.startswith("{"):
        try:
            button_id = json.loads(triggered)  # e.g. {"type": "delete-btn", "row_id": "someOID"}
            if button_id.get('type') == 'delete-btn':
                row_id = button_id.get('row_id')
                CustomORM().db["mood_journal"].delete_one({"_id": ObjectId(row_id)})
                logger.info(f"Deleted entry with _id: {row_id}")
        except Exception as e:
            logger.error(f"Error deleting entry: {e}")
            return no_update

    # Finally, re-query the updated data
    try:
        mood_journal = CustomORM().query_collection("mood_journal")
        if not mood_journal:
            logger.info("No entries found in mood_journal.")
            return []

        # Convert ObjectId to string & add "Actions" column
        for doc in mood_journal:
            if "_id" in doc and isinstance(doc["_id"], ObjectId):
                doc["_id"] = str(doc["_id"])
            # Add an Actions column with Edit & Delete buttons
            doc["Actions"] = html.Div(
                [
                    dbc.Button(
                        "Edit",
                        id={"type": "edit-btn", "row_id": doc["_id"]},
                        color="info",
                        className="me-2",
                        n_clicks=0
                    ),
                    dbc.Button(
                        "Delete",
                        id={"type": "delete-btn", "row_id": doc["_id"]},
                        color="danger",
                        n_clicks=0
                    )
                ]
            )

        # Define table columns
        columns = [col for col in mood_journal[0].keys() if col != "_id"]
        if "Actions" not in columns:
            columns.append("Actions")

        # Build table header
        table_header = html.Thead(html.Tr([html.Th(col) for col in columns]))

        # Build table body
        table_rows = []
        for row in mood_journal:
            row_cells = []
            for col in columns:
                cell_content = row[col]
                # If the cell is already a Dash component, keep it as-is
                row_cells.append(html.Td(cell_content))
            table_rows.append(html.Tr(row_cells))

        table_body = html.Tbody(table_rows)

        # Return the final table
        table = dbc.Table(
            [table_header, table_body],
            striped=True,
            bordered=True,
            hover=True,
            responsive=True
        )
        return [table]

    except Exception as e:
        logger.error(f"Error building the mood journal table: {e}")
        return []