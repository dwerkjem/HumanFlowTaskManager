import dash
from dash import html, dcc
import pymongo
import dotenv
import os
import dash_bootstrap_components as dbc
import time
from datetime import datetime
from dash import callback_context
from bson import ObjectId

from modules.custom_logger import create_logger

dash.register_page(__name__)

dotenv.load_dotenv()

logger = create_logger()

def get_db_connection():
    root_username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
    root_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    client = pymongo.MongoClient(f"mongodb://{root_username}:{root_password}@mongo:27017/")
    return client["HumanFlowTaskManagerDB"]

now = time.strftime("%Y-%m-%d %H:%M", time.localtime())

def check_connection(db):
    try:
        db.command("ping")
        logger.info("Successfully connected to MongoDB.")
        return True
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        return False

db = get_db_connection()
def display_mood_table():
    moods = db.moods.find()
    return html.Div([
        html.Table([
            html.Thead([
                html.Tr([
                    html.Th("Value"),
                    html.Th("Timestamp"),
                    html.Th("Actions")
                ])
            ]),
            html.Tbody([
                html.Tr([
                    html.Td(mood["value"]),
                    html.Td(time.strftime("%Y-%m-%d %H:%M", time.localtime(mood["timestamp"]))),
                    html.Td(dbc.Button("Delete", color="danger", id={"type": "delete-button", "index": str(mood["_id"])}))
                ]) for mood in moods
            ])
        ]),
        dbc.Modal([
            dbc.ModalHeader("Confirm Deletion"),
            dbc.ModalBody("Are you sure you want to delete this mood entry?"),
            dbc.ModalFooter([
                dbc.Button("Yes", id="confirm-delete", color="danger"),
                dbc.Button("No", id="cancel-delete", className="ml-auto")
            ])
        ], id="confirm-delete-modal", is_open=False)
    ])


@dash.callback(
    dash.Output("confirm-delete-modal", "is_open"),
    dash.Output("confirm-delete", "data-mood-id"),
    dash.Input({"type": "delete-button", "index": dash.ALL}, "n_clicks"),
    dash.State({"type": "delete-button", "index": dash.ALL}, "id"),
    dash.State("confirm-delete-modal", "is_open")
)
def toggle_confirm_modal(n_clicks, ids, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, None
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if button_id:
            mood_id = eval(button_id)["index"]
            return not is_open, mood_id
    return is_open, None

layout = html.Div([
    html.Div([
        html.H1("how are you feeling today? Bad to Good"),
        
    ]),
        dcc.Slider(
            id='mood-slider',
            min=0,
            max=10,
            step=0.25,
            value=0,
            marks={i: str(i) for i in range(11)}
        ),
        html.Div(id='slider-output-container'),
        dbc.Button("Submit", color="primary", className="mr-1", id="submit-button"),
        display_mood_table()

]) if check_connection(db) else html.H1("Error connecting to MongoDB.")

@dash.callback(
    dash.Output("slider-output-container", "children"),
    [dash.Input("submit-button", "n_clicks"),
     dash.Input("confirm-delete", "n_clicks")],
    [dash.State("mood-slider", "value"),
     dash.State("confirm-delete", "data-mood-id")]
)
def handle_mood(n_clicks_submit, n_clicks_delete, value, mood_id):
    ctx = callback_context
    if not ctx.triggered:
        return "Submit your mood"
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if button_id == "submit-button" and n_clicks_submit:
        db.moods.insert_one({
            "value": value,
            "timestamp": time.time()
        })
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"Mood submitted at {now} with value {value}"
    elif button_id == "confirm-delete" and n_clicks_delete and mood_id:
        db.moods.delete_one({"_id": ObjectId(mood_id)})
        return "Mood entry deleted"
    return ""