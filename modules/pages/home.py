from dash import html

layout = html.Div([
    html.H1("Home Page"),
    html.P("Welcome to the Home Page!"),
    html.A("Go to About Page", href="/about")
])