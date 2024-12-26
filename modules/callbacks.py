# callbacks.py
from dash import callback_context, html
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, ALL
from bson import ObjectId
import json
from datetime import datetime

from flask import session, redirect, url_for, request, g

from modules.custom_logger import create_logger
from modules.customORM import CustomORM
def load_credentials():
    try:
        with open('credentials.json') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading credentials: {e}")
        return {}

raw_credentials = load_credentials()

logger = create_logger()
USER_PWD = {user_info['username']: user_info['password'] for user_info in raw_credentials.values()}
USER_GROUPS = {user_info['username']: user_info['group'] for user_info in raw_credentials.values()}

def register_callbacks(app, server, redis_client):
    # Callback to update the database connection alert
    @app.callback(
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

    # Callback to handle modal visibility and form reset
    @app.callback(
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
        ctx = callback_context
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

    # Callback to refresh the mood journal table
    @app.callback(
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

        ctx = callback_context
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

    @app.callback(
    [Output('url', 'pathname'), Output('url', 'refresh')],
    [Input('logout-link', 'n_clicks')]
    )
    def logout_user(n_clicks):
        if n_clicks:
            session.pop('username', None)
            session.pop('group', None)
            logger.info(f"User logged out successfully.")
            # Return both the new pathname and `True` to force a page reload.
            return '/login', True
        return dash.no_update, dash.no_update


    @server.before_request
    def before_request():
        session.permanent = True

        if 'username' in session:
            session['group'] = USER_GROUPS.get(session['username'])
            g.username = session['username']
            g.group = session['group']
        else:
            g.username = None
            g.group = None
        if request.endpoint not in ('login', 'static', 'logout') and 'username' not in session:
            return redirect(url_for('login'))

    @server.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            ip = request.remote_addr

            # Check if user is locked out
            attempts_key = f"login_attempts:{ip}"
            attempts = redis_client.get(attempts_key)
            attempts = int(attempts) if attempts else 0

            if attempts >= 10:
                return "Too many failed login attempts. Please contact the administrator", 429

            if username in USER_PWD and USER_PWD[username] == password:
                # Successful login; reset attempts
                redis_client.delete(attempts_key)
                session['username'] = username
                session['group'] = USER_GROUPS.get(username)
                logger.info(f"User '{username}' logged in successfully.")
                return redirect(url_for('index'))
            else:
                new_attempts = redis_client.incr(attempts_key)
                if new_attempts == 1:
                    # First failed attempt; set 1-hour expiry
                    redis_client.expire(attempts_key, 3600)
                logger.warning("Invalid credentials.")
                return "Invalid credentials", 401

        return '''
            <form method="post">
                Username: <input type="text" name="username"><br>
                Password: <input type="password" name="password"><br>
                <input type="submit" value="Login">
            </form>
        '''

    @server.route('/logout')
    def logout():
        """
        Log the user out and redirect them to the /login page.
        """
        try:
            username = session.pop('username', None)
            session.pop('group', None)
            logger.info(f"User '{username}' logged out successfully.")
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return "Error during logout", 500

    @server.route('/')
    def index():
        """
        If user is logged in, load the main dash content; otherwise, redirect to login page.
        """
        if 'username' not in session:
            return redirect(url_for('login'))
        else:
            return redirect('/pages/index')

    def clear_rate_limit(user_ip):
        keys = redis_client.keys(f"LIMITER/{user_ip}/*")
        for key in keys:
            redis_client.delete(key)
        logger.info(f"Rate limits for {user_ip} cleared.")

    # Protect Dash Routes with Client-Side Callback
    app.clientside_callback(
        """
        function(switchOn) {
            document.documentElement.setAttribute("data-bs-theme", switchOn ? "light" : "dark"); 
            return window.dash_clientside.no_update;
        }
        """,
        Output("theme-output", "children"),  # Correct Output
        Input("switch", "value"),
    )
