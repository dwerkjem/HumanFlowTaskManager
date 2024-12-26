import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from datetime import datetime

from modules.customORM import CustomORM

dash.register_page(__name__)

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