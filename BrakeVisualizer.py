# -*- coding: utf-8 -*-
"""
Created on Fri May  3 10:59:35 2019

@author: Miguel Fabra
"""

# import math
# import json
# import time
# from datetime import datetime as dtdt
# import numpy as np
import pandas as pd
# import dash
import dash_html_components as html
import dash_core_components as dcc
# import dash_daq as daq
# from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import plotly.express as px
# import os
import base64
import datetime
import io

import dash
from dash.dependencies import Input, Output, State
import dash_table





def singleGraph(graphid, figure):
    return [html.Div([dcc.Graph(id=graphid[0], figure=figure[0])], style={'layout': {'height': 800},
                                                                          'width': '100%'})]


def doubleGraphVertical(graphid, figure):
    return [html.Div([dcc.Graph(id=graphid[0], figure=figure[0])]),
            html.Div([dcc.Graph(id=graphid[1], figure=figure[1])])]


def doubleGraphHorizontal(graphid, figure):
    return [html.Div([dcc.Graph(id=graphid[0], figure=figure[0])], style={'float': 'left',
                                                                          'layout': {'height': 800},
                                                                          'width': '50%'}),
            html.Div([dcc.Graph(id=graphid[1], figure=figure[1])], style={'float': 'right',
                                                                          'layout': {'height': 800},
                                                                          'width': '50%'})]


def trippleGraphHorizontal(graphid, figure):
    return [html.Div([dcc.Graph(id=graphid[0], figure=figure[0])], style={'layout': {'height': 800},
                                                                          'width': '33%',
                                                                          'display': 'inline-block'}),
            html.Div([dcc.Graph(id=graphid[1], figure=figure[1])], style={'layout': {'height': 800},
                                                                          'width': '33%',
                                                                          'display': 'inline-block'}),
            html.Div([dcc.Graph(id=graphid[2], figure=figure[2])], style={'layout': {'height': 800},
                                                                          'width': '33%',
                                                                          'display': 'inline-block'})]



        # =============================================================================
# Main DASH
# =============================================================================



app = dash.Dash(__name__)
server = app.server


app.layout = html.Div([
    html.H2(id='tittle', children='Campos Engineering', style={'text-align': 'center', 'fontSize': 20}),
    html.Div([
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Files')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            },
            # Allow multiple files to be uploaded
            multiple=True
        ),
        # html.Div(id='output-data-upload'),
    ]),
    dcc.Tabs(id ="tabs",
             children = [dcc.Tab(id='Results_tab', value='tab-1', label='Results'),
                         dcc.Tab(id='xyz_tab', value='tab-2', label='xyz'),
                         dcc.Tab(id='File_tab', value='tab-3', label='File'),
                         ],
             value='tab-1'),
])


# =============================================================================
# TABS AND DATA
# =============================================================================




# =============================================================================
# SELECTORS AND LAYOUT
# =============================================================================


def process_outputdf(df):
    output = df
    output.magnitude = output.apply(lambda row: row.magnitude.split('.')[-1], axis=1)

    RPM = output[output.magnitude == 'RPM'][['ts', 'measure']].set_index('ts')
    RPM_avg = output[output.magnitude == 'RPM_average'][['ts', 'measure']].set_index('ts')
    Load = output[output.magnitude == 'Load'][['ts', 'measure']].set_index('ts')
    Temperature = output[output.magnitude == 'Temperature'][['ts', 'measure']].set_index('ts')
    Pressure = output[output.magnitude == 'Pressure'][['ts', 'measure']].set_index('ts')

    RPM.columns = ['RPM']
    RPM_avg.columns = ['RPM_average']
    Load.columns = ['Load [N/m]']
    Temperature.columns = ['Temperature [ºC]']
    Pressure.columns = ['Pressure [bar]']

    data = pd.concat([RPM, RPM_avg, Load, Temperature, Pressure], axis=1)
    data = data.sort_values('ts')
    data = data.fillna(method='ffill')
    data = data.fillna(method='bfill')
    data.index = data.index - data.index.min()

    RPMs = data.groupby('ts')['RPM'].mean().to_frame('measure')
    RPMs['magnitude'] = 'RPM'
    RPM_avgs = data.groupby('ts')['RPM_average'].mean().to_frame('measure')
    RPM_avgs['magnitude'] = 'RPM_avg'
    Temperatures = data.groupby('ts')['Temperature [ºC]'].mean().to_frame('measure')
    Temperatures['magnitude'] = 'Temperature [ºC]'
    Pressures = data.groupby('ts')['Pressure [bar]'].mean().to_frame('measure')
    Pressures['magnitude'] = 'Pressure [bar]'
    Loads = data.groupby('ts')['Load [N/m]'].mean().to_frame('measure')
    Loads['magnitude'] = 'Load [N/m]'

    data2 = pd.concat([RPMs, RPM_avgs, Temperatures, Pressures, Loads])
    data2 = data2.reset_index()

    return data2


def parse_contents_df(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')),
                delimiter=';',
                header=0, names=['id', 'ts', 'date', 'magnitude', 'measure']
            )
            df = process_outputdf(df)
            return df
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
            df = process_outputdf(df)
            return df
    except Exception as e:
        print(e)

def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')),
                delimiter=';',
                header=0, names=['id', 'ts', 'date', 'magnitude', 'measure']
            )
            df = process_outputdf(df)
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
            df = process_outputdf(df)
    except Exception as e:
        print(e)
        return [html.Div([
            'There was an error processing this file.'
        ]), '']

    df = df.reset_index()
    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),
        dash_table.DataTable(
            df.to_dict('records'),
            [{'name': i, 'id': i} for i in df.columns]
        ),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])

@app.callback([Output('File_tab', 'children'),
               Output('Results_tab', 'children'),
               Output('xyz_tab', 'children')
               ],
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
              State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children_File_tab = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]

        df = [
            parse_contents_df(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)][0]

        myid1 = ['Results']
        fig1 = px.line(df, x='ts', y='measure', color='magnitude')
        fig1.update_layout(hovermode='x',
                           height=800)
        figure1 = [fig1]

        myid2 = ['xyz']
        x = list(df[df.magnitude == 'Temperature [ºC]'].measure)
        y = list(df[df.magnitude == 'Pressure [bar]'].measure)
        z = list(df[df.magnitude == 'Load [N/m]'].measure)
        fig2 = go.Figure(data=[go.Scatter3d(x=x, y=y, z=z,
                                            mode='markers',
                                            marker=dict(size=12,
                                                        color=z,                # set color to an array/list of desired values
                                                        colorscale='Viridis',   # choose a colorscale
                                                        opacity=0.8))],)
        fig2.update_layout(scene=dict(xaxis_title='Temperature [ºC]',
                                      yaxis_title='Pressure [bar]',
                                      zaxis_title='Load [N/m]'),
                           height=800)
        figure2 = [fig2]

        return children_File_tab, singleGraph(myid1, figure1), singleGraph(myid2, figure2)
    else:
        return [],[],[]


@app.callback(Output('tabs', 'children'),
              [Input('file', 'n_clicks')])
def update_tabs(file):
    tab_height = 2000

    children = [
        dcc.Tab(id='Results_tab', value='tab-1', label='Results', style={'padding': '0','line-height': tab_height},
                selected_style={'padding': '0','line-height': tab_height}),
        dcc.Tab(id='xyz_tab', value='tab-2', label='File', style={'padding': '0', 'line-height': tab_height},
                selected_style={'padding': '0', 'line-height': tab_height}),
        dcc.Tab(id='File_tab', value='tab-3', label='File', style={'padding': '0', 'line-height': tab_height},
                selected_style={'padding': '0', 'line-height': tab_height}),

    ]
    return children


# =============================================================================
# FUNCTION MAIN
# =============================================================================

if __name__ == '__main__':
    app.run_server(debug=False)
