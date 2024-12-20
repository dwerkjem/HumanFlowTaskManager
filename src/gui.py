from dash import Dash, dcc, html, Output, Input

# Initialize the Dash app
app = Dash(__name__)

# App layout
app.layout = html.Div([
    html.H1("Dash Slider Example"),
    html.P("Move the slider to change the value:"),

    # Slider component
    dcc.Slider(
        id='my-slider',
        min=0,
        max=100,
        step=1,
        value=50,  # Default value
        marks={i: str(i) for i in range(0, 101, 10)},  # Marks every 10
    ),

    # Output for the slider value
    html.Div(id='slider-output', style={'marginTop': 20})
])

# Callback to update the output based on the slider value
@app.callback(
    Output('slider-output', 'children'),
    Input('my-slider', 'value')
)
def update_output(value):
    return f'Selected value: {value}'

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
