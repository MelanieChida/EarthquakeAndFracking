import numpy as np
import pandas as pd
import re
from scipy.spatial.distance import cdist
from math import radians, sin, cos, sqrt, atan2
import dash
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import folium
from folium.plugins import MarkerCluster, MiniMap
import requests
import plotly.express as px
import plotly.graph_objects as go

app = Dash(__name__)
server = app.server

url1 = 'https://raw.githubusercontent.com/MelanieChida/EarthquakesAndFracking/main/src/FracTrackerNationalWells_Part1.csv'
file_path1 = 'C:/Users/melli/Desktop/deploywithrender/src/FracTrackerNationalWells_Part1.csv'
data1 = pd.read_csv(url1, encoding='cp1252')

url2 = 'https://raw.githubusercontent.com/MelanieChida/EarthquakesAndFracking/main/src/FracTrackerNationalWells_Part2.csv'
file_path2 = 'C:/Users/melli/Desktop/deploywithrender/src/FracTrackerNationalWells_Part2.csv'
data2 = pd.read_csv(url2, encoding='cp1252')

url3 = 'https://raw.githubusercontent.com/MelanieChida/EarthquakesAndFracking/main/src/FracTrackerNationalWells_Part3-TX.csv'
file_path3 = 'C:/Users/melli/Desktop/deploywithrender/src/FracTrackerNationalWells_Part3_TX.csv'
data3 = pd.read_csv(url3, encoding='cp1252')

url4 = 'https://raw.githubusercontent.com/MelanieChida/EarthquakesAndFracking/main/src/2023earthquakesupto10-14.csv'
file_path4 = 'C:/Users/melli/Desktop/deploywithrender/src/2023earthquakesupto10-14.csv'
earthquake_data = pd.read_csv(url4, encoding='cp1252')

fracking_data = pd.concat([data1, data2, data3], ignore_index=True)

url5 = 'https://raw.githubusercontent.com/MelanieChida/EarthquakesAndFracking/main/src/earthquake_with_distance.csv'
file_path4 = 'C:/Users/melli/Desktop/deploywithrender/src/earthquake_with_distance.csv'
earthquake_with_distance = pd.read_csv(url5, encoding='cp1252')

earthquake_data = earthquake_with_distance.dropna(subset=['state'])

# Get the bounding box coordinates for the United States
us_bounding_box = [[24.396308, -125.000000], [49.384358, -66.934570]]


# Function to create the Folium map
def create_folium_map(earthquake_data):
    # Create a map centered around the United States
    us_map = folium.Map(location=[28.8283, -98.5795], zoom_start=5, control_scale=True, max_bounds=True, max_bounds_viscosity=1.0)

    # Create a GeoJSON layer for the United States boundary
    us_geojson_url = 'https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json'
    us_geojson = requests.get(us_geojson_url).json()
    us_boundary_layer = folium.GeoJson(us_geojson, name='United States Boundary').add_to(us_map)

    # Create a MarkerCluster for adding earthquake markers
    marker_cluster = MarkerCluster().add_to(us_map)

    # Iterate through the DataFrame and add markers for each earthquake
    for index, row in earthquake_data.iterrows():
        # Include min_site_distances in the pop-up content using .format()
        popup_content = "Location: {}<br>Distance to Nearest Fracking Site (km): {:.2f}".format(row['place'], row['min_site_distances'])

        # Add the marker with the customized pop-up content
        folium.Marker([row['latitude'], row['longitude']], popup=folium.Popup(popup_content, max_width=300)).add_to(marker_cluster)

    # Create a MiniMap to provide an overview
    minimap = MiniMap(toggle_display=True, position='bottomright')
    us_map.add_child(minimap)

    return us_map


# Create Folium map
us_map = create_folium_map(earthquake_data)

# Count the number of earthquakes for each state
state_counts = earthquake_data['state'].value_counts().reset_index()

# Rename columns for better clarity
state_counts.columns = ['State', 'Count']

# Create an interactive pie chart using plotly
fig_pie = px.pie(state_counts, names='State', values='Count', title='Proportion of Earthquakes by State')

# Adjust layout for better visibility of labels and center the title
fig_pie.update_layout(
    title=dict(text='Proportion of Earthquakes by State', x=0.5),  # Center the title
    showlegend=True,
)

# Adjust pie chart appearance
fig_pie.update_traces(
    textposition='inside',
    textinfo='percent+label',
    pull=[0.1] * len(state_counts)
)

# Scatterplot of Earthquake Magnitude vs Distance to Nearest Fracking Site (km) for each state
scatter_plots = {}

for state in earthquake_data['state'].unique():
    state_earthquakes = earthquake_data[earthquake_data['state'] == state]
    scatter_fig = px.scatter(state_earthquakes, x='min_site_distances', y='mag',
                             labels={'mag': 'Earthquake Magnitude', 'min_site_distances': 'Distance to Nearest Fracking Site (km)'},
                             title=f'Earthquake Magnitude vs Distance ({state})')

    scatter_plots[state] = scatter_fig

# Initialize Dash app
app = dash.Dash(__name__)

# Define layout
app.layout = html.Div(style={'textAlign': 'center'}, children=[
    html.H1(children='Earthquakes & Fracking in the US',
            style={'textAlign': 'center', 'width': '100%', 'font-family': 'Arial', 'fontSize': 50,
                   'color': '#3588FE'}),
    html.H1(children='Choose a State:',
            style={'textAlign': 'center', 'width': '100%', 'font-family': 'Arial','fontSize': 15}),
    # Dropdown for state selection

    dcc.Dropdown(
        id='state-dropdown',
        options=[{'label': state, 'value': state} for state in sorted(earthquake_data['state'].unique())],
        value='TX',  # Default selected state
        style={'textAlign': 'center','width': '100%','justify-content': 'center',
               'verticalAlign': 'middle','font-family': 'Arial',
               'border': 2, 'border - radius': 20}
    ),

    # Map on the top
    html.Div(children=[
        html.Iframe(id='earthquake-map', srcDoc=us_map._repr_html_(), width='100%', height='800px'),
    ]),

    # Three charts below the map
    html.Div(children=[
        # Pie chart on the left, smaller size
        dcc.Graph(
            id='pie-chart',
            figure=fig_pie,
            config={'staticPlot': False},
            style={'width': '33%', 'height': '40%', 'font-family': 'Arial'}  # Adjust the size here
        ),

        # Scatterplot in the middle, smaller size
        dcc.Graph(
            id='scatter-plot',
            style={'width': '33%', 'height': '40%', 'font-family': 'Arial', 'textAlign': 'center'}  # Adjust the size here
        ),

        # Histogram on the right, smaller size
        dcc.Graph(
            id='histogram-chart',
            style={'width': '33%', 'height': '40%', 'font-family': 'Arial', 'textAlign': 'center'}  # Adjust the size here
        ),
    ], style={'display': 'flex'})
])


# Callback to update scatterplot based on dropdown selection
@app.callback(
    Output('scatter-plot', 'figure'),
    [Input('state-dropdown', 'value')]
)
def update_scatter_plot(selected_state):
    return scatter_plots.get(selected_state, px.scatter()).update_layout(title = dict(x=0.5, xanchor='center'))  # Return an empty scatter plot if the state is not found


# Callback to update histogram based on dropdown selection
@app.callback(
    Output('histogram-chart', 'figure'),
    [Input('state-dropdown', 'value')]
)
def update_histogram(selected_state):
    state_earthquakes = earthquake_data[earthquake_data['state'] == selected_state]
    histogram_fig = px.histogram(state_earthquakes, x='mag', title=f'Earthquake Magnitudes in {selected_state}')

    histogram_fig.update_layout(
        xaxis_title='Magnitude',
        yaxis_title='Frequency'
    )
    return histogram_fig.update_layout(title = dict(x=0.5, xanchor='center'))


if __name__ == '__main__':
    app.run_server(debug=True)
