import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Load data
print("Loading data...")
df = pd.read_csv('bangladesh_police_crime_data_2021_2025.csv')

# Data preprocessing
df['Date'] = pd.to_datetime(df['Year'].astype(str) + '-' + df['Month'] + '-01')
df['Year'] = df['Date'].dt.year
df['Month_Num'] = df['Date'].dt.month

# Crime categories
crime_columns = ['Dacoity', 'Robbery', 'Murder', 'Speedy_Trial', 'Riot', 
                'Woman_Child_Repression', 'Kidnapping', 'Police_Assault', 
                'Burglary', 'Theft', 'Other_Cases', 'Arms_Act', 'Explosive_Act', 
                'Narcotics', 'Smuggling', 'Recovery_Cases']

# Police units
police_units = sorted(df['Unit'].unique())

print("Data loaded successfully!")

# Define the layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("🇧🇩 Bangladesh Crime Data Dashboard", 
                   className="text-center mb-4",
                   style={'color': '#2E86AB', 'fontWeight': 'bold'}),
            html.P("Interactive Analysis of Crime Statistics (2021-2025)", 
                  className="text-center text-muted mb-4"),
            html.Hr()
        ])
    ]),
    
    # Controls Row
    dbc.Row([
        dbc.Col([
            html.Label("👮 Select Police Unit:", className="fw-bold"),
            dcc.Dropdown(
                id='unit-dropdown',
                options=[{'label': unit, 'value': unit} for unit in police_units],
                value=['DMP', 'CMP'],
                multi=True,
            )
        ], width=4),
        
        dbc.Col([
            html.Label("📅 Select Year Range:", className="fw-bold"),
            dcc.RangeSlider(
                id='year-slider',
                min=df['Year'].min(),
                max=df['Year'].max(),
                value=[2021, 2024],
                marks={str(year): str(year) for year in df['Year'].unique()},
                step=1
            )
        ], width=4),
        
        dbc.Col([
            html.Label("🔍 Select Crime Types:", className="fw-bold"),
            dcc.Dropdown(
                id='crime-dropdown',
                options=[{'label': crime, 'value': crime} for crime in crime_columns],
                value=['Murder', 'Robbery', 'Narcotics', 'Theft', 'Woman_Child_Repression'],
                multi=True,
            )
        ], width=4)
    ], className="mb-4 p-3", style={'backgroundColor': '#f8f9fa', 'borderRadius': '10px'}),
    
    # Summary Cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("📈 Total Cases", className="card-title"),
                    html.H2(id="total-cases", children="0", className="text-primary"),
                    html.P("Across selected filters", className="card-text text-muted")
                ])
            ], color="light", className="text-center")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("📊 Avg Monthly", className="card-title"),
                    html.H2(id="avg-monthly", children="0", className="text-success"),
                    html.P("Average monthly cases", className="card-text text-muted")
                ])
            ], color="light", className="text-center")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("🔺 Peak Crime", className="card-title"),
                    html.H2(id="peak-crime", children="-", className="text-warning"),
                    html.P("Most frequent crime type", className="card-text text-muted")
                ])
            ], color="light", className="text-center")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("👥 Units", className="card-title"),
                    html.H2(id="total-units", children="0", className="text-info"),
                    html.P("Police units in view", className="card-text text-muted")
                ])
            ], color="light", className="text-center")
        ], width=3)
    ], className="mb-4"),
    
    # Tabs
    dcc.Tabs(id="tabs", value='tab-overview', children=[
        dcc.Tab(label='📊 Overview Dashboard', value='tab-overview'),
        dcc.Tab(label='📈 Crime Trends', value='tab-trends'),
        dcc.Tab(label='🔍 Crime Analysis', value='tab-analysis'),
        dcc.Tab(label='📋 Raw Data', value='tab-data')
    ]),
    
    html.Div(id='tab-content', className="mt-4")
], fluid=True)

# Chart functions
def create_crime_pie_chart(filtered_df, selected_crimes):
    if not selected_crimes:
        selected_crimes = crime_columns[:5]
    
    crime_totals = filtered_df[selected_crimes].sum()
    fig = px.pie(
        values=crime_totals.values,
        names=crime_totals.index,
        title="Crime Type Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    return fig

def create_monthly_trend_chart(filtered_df):
    monthly_data = filtered_df.groupby('Date')['Total_Cases'].sum().reset_index()
    fig = px.line(
        monthly_data, 
        x='Date', 
        y='Total_Cases',
        title='Monthly Crime Trend',
        labels={'Total_Cases': 'Total Cases'}
    )
    fig.update_layout(hovermode='x unified', height=400)
    return fig

def create_top_units_chart(filtered_df):
    unit_totals = filtered_df.groupby('Unit')['Total_Cases'].sum().sort_values(ascending=False).head(10)
    fig = px.bar(
        x=unit_totals.values,
        y=unit_totals.index,
        orientation='h',
        title='Top 10 Police Units',
        labels={'x': 'Total Cases', 'y': 'Unit'},
        color=unit_totals.values,
        color_continuous_scale='Viridis'
    )
    fig.update_layout(height=400)
    return fig

def create_crime_trends_chart(filtered_df, selected_crimes):
    if not selected_crimes:
        selected_crimes = ['Murder', 'Robbery', 'Theft']
    
    monthly_crimes = filtered_df.groupby('Date')[selected_crimes].sum().reset_index()
    
    fig = go.Figure()
    for crime in selected_crimes:
        fig.add_trace(go.Scatter(
            x=monthly_crimes['Date'],
            y=monthly_crimes[crime],
            name=crime,
            mode='lines+markers'
        ))
    
    fig.update_layout(
        title='Crime Trends Over Time',
        xaxis_title='Date',
        yaxis_title='Cases',
        hovermode='x unified',
        height=500
    )
    return fig

def create_seasonal_patterns_chart(filtered_df):
    monthly_avg = filtered_df.groupby('Month_Num')['Total_Cases'].mean().reset_index()
    fig = px.line(
        monthly_avg,
        x='Month_Num',
        y='Total_Cases',
        title='Seasonal Patterns',
        labels={'Month_Num': 'Month', 'Total_Cases': 'Average Cases'}
    )
    fig.update_traces(mode='lines+markers', line=dict(width=3))
    fig.update_xaxes(
        tickvals=list(range(1, 13)), 
        ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    )
    fig.update_layout(height=400)
    return fig

# Callbacks
@app.callback(
    [Output('total-cases', 'children'),
     Output('avg-monthly', 'children'),
     Output('peak-crime', 'children'),
     Output('total-units', 'children')],
    [Input('unit-dropdown', 'value'),
     Input('year-slider', 'value')]
)
def update_summary_cards(selected_units, year_range):
    filtered_df = df[
        (df['Unit'].isin(selected_units)) &
        (df['Year'] >= year_range[0]) & 
        (df['Year'] <= year_range[1])
    ]
    
    total_cases = filtered_df['Total_Cases'].sum()
    avg_monthly = filtered_df.groupby(['Year', 'Month'])['Total_Cases'].sum().mean()
    peak_crime = filtered_df[crime_columns].sum().idxmax()
    total_units = len(filtered_df['Unit'].unique())
    
    return (
        f"{total_cases:,.0f}",
        f"{avg_monthly:,.0f}",
        peak_crime,
        f"{total_units}"
    )

@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs', 'value'),
     Input('unit-dropdown', 'value'),
     Input('year-slider', 'value'),
     Input('crime-dropdown', 'value')]
)
def render_tab_content(selected_tab, selected_units, year_range, selected_crimes):
    filtered_df = df[
        (df['Unit'].isin(selected_units)) &
        (df['Year'] >= year_range[0]) & 
        (df['Year'] <= year_range[1])
    ]
    
    if selected_tab == 'tab-overview':
        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(figure=create_crime_pie_chart(filtered_df, selected_crimes))
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(figure=create_monthly_trend_chart(filtered_df))
                    ])
                ])
            ], width=6)
        ])
    
    elif selected_tab == 'tab-trends':
        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(figure=create_crime_trends_chart(filtered_df, selected_crimes))
                    ])
                ])
            ], width=12)
        ])
    
    elif selected_tab == 'tab-analysis':
        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(figure=create_seasonal_patterns_chart(filtered_df))
                    ])
                ])
            ], width=12)
        ])
    
    elif selected_tab == 'tab-data':
        display_df = filtered_df.head(50)
        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Filtered Data (First 50 rows)"),
                    dbc.CardBody([
                        html.Div([
                            html.P(f"Showing {len(display_df)} rows", className="text-muted"),
                            dbc.Table.from_dataframe(
                                display_df.round(2),
                                striped=True,
                                bordered=True,
                                hover=True,
                                responsive=True,
                                style={'maxHeight': '500px', 'overflowY': 'auto', 'fontSize': '12px'}
                            )
                        ])
                    ])
                ])
            ], width=12)
        ])

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8050)))