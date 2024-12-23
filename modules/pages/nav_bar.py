from dash import html

def create_nav_bar(group_name, username):
    return html.Nav([
        html.Ul([
            html.Li(html.A("Home", href="/")),
            html.Li(html.A("Logout", href="/logout")),
            html.Li(html.A(f"{group_name} {username}!", href="/profile"))
        ], className="nav-list")
    ], className="nav-bar")