from dash import html

def create_nav_bar():
    return html.Nav([
        html.Ul([
            html.Li(html.A("Home", href="/")),
            html.Li(html.A("Logout", href="/logout")),
        ], className="nav-list")
    ], className="nav-bar")
