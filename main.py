from dash import Dash, html, dcc, page_container
from dash_auth import BasicAuth

app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)
USER_PWD = {
    "username": "password",
    "user2": "password2",
}
BasicAuth(app, USER_PWD)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])
if __name__ == "__main__":
    app.run_server(debug=True)