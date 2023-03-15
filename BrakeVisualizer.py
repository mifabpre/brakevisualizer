# -*- coding: utf-8 -*-
"""
Created on Fri May  3 10:59:35 2022
@author: Miguel Fabra, Santi Conesa, Dani Di Iorio
"""
import html as html
import pandas as pd
import numpy as np
import dash
import plotly.graph_objects as go
import base64
import datetime
import io
import os
import webbrowser
import dash_bootstrap_components as dbc
import logging
import warnings
from plotly.subplots import make_subplots
from dash import dcc, html, dash_table
from tkinter import filedialog
from tkinter import *
from dash_extensions.enrich import MultiplexerTransform, DashProxy
from scipy.signal import savgol_filter


warnings.filterwarnings('ignore')

text_instructions = \
    '1. Select your category with the dropdown.\n' \
    '2. Drag and drop or select files (Maximum 10 test files).\n' \
    '3. After doing the calculations, the tabs are activated and the graphs can be viewed.\n' \
    '4. The graphs are the following:\n' \
    '   4.1. Results. sensor values on the complete test. If there are inserted more than one test, it can be ' \
    'synchronized with the slider.\n' \
    '   4.2. 3D graph Mu on function of Pressure and Temperature.\n' \
    '   4.3. Mu on function of Temperature on different Pressure ranges. Ranges can be adjusted with the ' \
    'sliders.\n' \
    '   4.4. Mu on function of Pressure on different Temperature ranges. Ranges can be adjusted with the ' \
    'sliders.\n' \
    '   4.5. X-Y of pedal stiffness and torque to be sure that the machine is working correctly.\n' \
    '   4.6. Table with all data of the inserted test.\n' \
    '5. You can clear all the data and start again with the button "Clear Data".\n' \
    '6. You can download the graphs with the button "Download graphs". You only need to select the desired ' \
    'path and the name for the file. An HTML file is downloaded.'
instructions_brakevisualizer = \
    html.Div([
        html.Div([
            html.Blockquote(),
        ]),
        html.Div([
            html.Blockquote(),
            dcc.Textarea(
                id='textarea-example',
                value=text_instructions,
                style={'width': '100%', 'height': 700, 'borderWidth': '1px', 'borderStyle': 'dashed',
                       'borderRadius': '5px', 'background': 'lightyellow', 'fontSize': 20},
            ),
            html.Div(id='textarea-example-output', style={'whiteSpace': 'pre-line'}),
            html.Blockquote(),
        ], style={"display": "grid", "grid-template-columns": "1.5% 97% 1.5%"})
    ])


def GetFolderPath():
    root = Tk()
    root.attributes('-topmost', True)
    root.withdraw()
    folderpath = filedialog.askdirectory()
    root.destroy()
    return folderpath


def polynomical_regression(dataframe_temp, graph_type):
    try:
        if len(dataframe_temp[graph_type]) > 2 and len(dataframe_temp['Mu']) > 2:
            dataframe_temp.sort_values(graph_type, inplace=True)
            dataframe_temp.reset_index(drop=True, inplace=True)
            mymodel = np.polyfit(dataframe_temp[graph_type].values.tolist(), dataframe_temp['Mu'].values.tolist(), 2)
            mymodel = np.poly1d(mymodel)
            dataframe_temp['X'] = np.linspace(int(dataframe_temp[graph_type].min()),
                                              int(dataframe_temp[graph_type].max()), len(dataframe_temp.index))
            dataframe_temp['Mu'] = mymodel(dataframe_temp['X'])
        else:
            dataframe_temp['Mu'] = None
            dataframe_temp['X'] = None
        return dataframe_temp['Mu'], dataframe_temp['X']

    except KeyError:
        dataframe_temp['Mu'] = None
        dataframe_temp['X'] = None
        return dataframe_temp['Mu'], dataframe_temp['X']


def Results_Graph(dataframe, n_df, files_list, ranges):
    fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.25, 0.25, 0.25, 0.25, 0.25],
                        x_title='Time [s]', specs=[[{"secondary_y": True}], [{"secondary_y": True}],
                                                   [{"secondary_y": True}], [{"secondary_y": True}],
                                                   [{"secondary_y": True}]], vertical_spacing=0.02)

    for i in range(0, n_df):
        dataframe_temp = dataframe.loc[dataframe['df_id'] == i + 1]
        dataframe_temp = dataframe_temp.replace(0, None)

        all_colors = ['#ff0000', '#0000ff', '#008000', '#ffa500', '#696969', '#ff69b4',
                      '#4b0082', '#ffd700', '#ffd700', '#d2691e']
        if n_df <= 1:
            colors = all_colors[0:5]
        else:
            colors = [all_colors[i], all_colors[i], all_colors[i], all_colors[i], all_colors[i]]

        fig.add_trace(go.Scatter(
            x=dataframe_temp['Timestamp'],
            y=dataframe_temp['RPM'],
            name=files_list[i],
            line_color=colors[0],
            legendgroup=str(i),
            showlegend=True,
            visible=True
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=dataframe_temp['Timestamp'],
            y=dataframe_temp['Temperature'],
            name=files_list[i],
            line_color=colors[1],
            legendgroup=str(i),
            showlegend=False,
            visible=True
        ), row=2, col=1)

        fig.add_trace(go.Scatter(
            x=dataframe_temp['Timestamp'],
            y=dataframe_temp['Pressure'],
            name=files_list[i],
            line_color=colors[2],
            legendgroup=str(i),
            showlegend=False,
            visible=True
        ), row=3, col=1)

        fig.add_trace(go.Scatter(
            x=dataframe_temp['Timestamp'],
            y=dataframe_temp['Load'],
            name=files_list[i],
            line_color=colors[3],
            legendgroup=str(i),
            showlegend=False,
            visible=True
        ), row=4, col=1)

        fig.add_trace(go.Scatter(
            x=dataframe_temp['Timestamp'],
            y=dataframe_temp['Mu_No_Filtered'],
            name=files_list[i],
            line_color=colors[4],
            legendgroup=str(i),
            showlegend=False,
            visible=True
        ), row=5, col=1)

        fig.add_trace(go.Scatter(
            x=dataframe_temp['Timestamp'],
            y=dataframe_temp['Mu'],
            name=files_list[i],
            line_color=colors[0],
            legendgroup=str(i),
            showlegend=False,
            visible=True
        ), row=5, col=1)

    large_rockwell_template = dict(layout=go.Layout(title_font=dict(family='Rockwell', size=20)))
    fig.update_layout(title="Brakes Bedding Analysis", template=large_rockwell_template,
                      legend_tracegroupgap=20)
    fig.update_layout(legend_groupclick='togglegroup')

    fig.update_yaxes(title_text='Shaft speed [RPM]', row=1, col=1, zeroline=False,
                     rangemode='nonnegative')
    fig.update_yaxes(title_text='Temperature [ºC]', row=2, col=1, zeroline=False, rangemode='nonnegative')
    fig.update_yaxes(title_text='Brake_Press [bar]', row=3, col=1, zeroline=False)
    fig.update_yaxes(title_text='Brake Torque [Nm]', row=4, col=1, zeroline=False)
    fig.update_yaxes(title_text='Friction coeff [-]', row=5, col=1, zeroline=True)
    fig.update_layout(hovermode='x')
    fig.update_traces(xaxis='x5', mode='lines', hoverinfo='all')
    fig.update_xaxes(matches='x', showspikes=True, spikecolor='black', spikesnap='data', spikemode='across',
                     spikethickness=1, spikedash='solid', rangemode='nonnegative', zeroline=False,
                     range=[ranges[0], ranges[1]])
    fig.update_yaxes(showspikes=True, spikecolor='black', spikesnap='data', spikemode='across',
                     spikethickness=1, spikedash='solid')
    fig.update_layout(autosize=True, height=900)
    fig.update_xaxes(autorange=True)

    return fig


def Mu_Results_Tab(dataframe, n_df, files_list, ranges):
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True,
                        column_widths=[0.5, 0.5],
                        horizontal_spacing=0.04,
                        y_title='Friction coefficient [-]',
                        subplot_titles=("Mu - Temperature [ºC]", "Mu - Brake Pressure [bar]",))

    for i in range(0, n_df):
        dataframe_temp = dataframe.loc[dataframe['df_id'] == i + 1]

        all_colors = ['#ff0000', '#0000ff', '#008000', '#ffa500', '#696969', '#ff69b4',
                      '#4b0082', '#ffd700', '#ffd700', '#d2691e']

        if n_df <= 1:
            colors = all_colors[0:4]
        else:
            colors = [all_colors[i], all_colors[i], all_colors[i], all_colors[i], all_colors[i]]

        dataframe_temp = dataframe_temp.set_index('Timestamp')
        dataframe_temp = dataframe_temp[ranges[0]/100:ranges[1]/100]
        dataframe_temp.reset_index(drop=True, inplace=True)
        lr1 = pd.DataFrame()
        lr2 = pd.DataFrame()

        for idx in range(1, len(dataframe_temp['Temperature'])):

            if dataframe_temp.at[idx, 'Temperature'] is not None and dataframe_temp.at[idx, 'Mu'] is not None and \
                    dataframe_temp.at[idx, 'Mu'] is not np.nan:

                if dataframe_temp.at[idx, 'Temperature'] > 80 and dataframe_temp.at[idx, 'Mu'] > 0:
                    lr1.at[idx, 'Mu_Temp'] = dataframe_temp.at[idx, 'Mu']
                    lr1.at[idx, 'Mu'] = dataframe_temp.at[idx, 'Mu']
                    lr1.at[idx, 'Temperature'] = dataframe_temp.at[idx, 'Temperature']

            if dataframe_temp.at[idx, 'Pressure'] is not None and dataframe_temp.at[idx, 'Pressure'] > 0 \
                    and dataframe_temp.at[idx, 'Mu'] is not None and dataframe_temp.at[idx, 'Mu'] is not np.nan:

                if 10 < dataframe_temp.at[idx, 'Pressure'] and dataframe_temp.at[idx, 'Mu'] > 0:
                    lr2.at[idx, 'Mu_Press'] = dataframe_temp.at[idx, 'Mu']
                    lr2.at[idx, 'Mu'] = dataframe_temp.at[idx, 'Mu']
                    lr2.at[idx, 'Pressure'] = dataframe_temp.at[idx, 'Pressure']

        if len(lr1.index) > 0 and len(lr2.index) > 0:
            lr1['Mu'], lr1['X'] = polynomical_regression(lr1, 'Temperature')
            lr2['Mu'], lr2['X'] = polynomical_regression(lr2, 'Pressure')
        else:
            lr1['Temperature'] = None
            lr1['Mu_Temp'] = None
            lr1['X'] = None
            lr1['Mu'] = None
            lr2['Pressure'] = None
            lr2['Mu_Press'] = None
            lr2['X'] = None
            lr2['Mu'] = None

        fig.add_trace(go.Scatter(
            x=lr1['Temperature'],
            y=lr1['Mu_Temp'],
            name=files_list[i], mode="markers",
            line_color=colors[0],
            legendgroup=str(i),
            showlegend=True
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=lr1['X'],
            y=lr1['Mu'],
            showlegend=False,
            line=dict(color=colors[0], width=4),
            legendgroup=str(i)
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=lr2['Pressure'],
            y=lr2['Mu_Press'],
            name=files_list[i], mode="markers",
            line_color=colors[1],
            legendgroup=str(i),
            showlegend=False,
        ), row=1, col=2)

        fig.add_trace(go.Scatter(
            x=lr2['X'],
            y=lr2['Mu'],
            showlegend=False,
            line=dict(color=colors[1], width=4),
            legendgroup=str(i)
        ), row=1, col=2)

    large_rockwell_template = dict(layout=go.Layout(title_font=dict(family='Rockwell', size=20)))
    fig.update_layout(template=large_rockwell_template, showlegend=True, legend_groupclick='togglegroup')
    fig.update_layout(height=650)
    fig.update_xaxes(zeroline=True)
    fig.update_layout(hovermode='y')
    fig.update_traces(yaxis='y1', hoverinfo='y')
    fig.update_xaxes(showspikes=True, spikecolor='black', spikemode='across',
                     spikethickness=1, spikedash='solid', rangemode='nonnegative', zeroline=False)
    fig.update_xaxes(title_text='Temperature [ºC]', row=1, col=1, zeroline=False, rangemode='nonnegative')
    fig.update_xaxes(title_text='Brake_Press [bar]', row=1, col=2, zeroline=False)
    fig.update_yaxes(showspikes=True, spikecolor='black', spikemode='across',
                     spikethickness=1, spikedash='solid')
    fig.update_traces(marker=dict(size=2), selector=dict(mode='markers'))

    return fig


def Graph_3d(dataframe, n_df, files_list):
    fig = go.Figure()
    for i in range(0, n_df):
        dataframe_temp = dataframe.loc[dataframe['df_id'] == i + 1]

        all_colors = ['#ff0000', '#0000ff', '#008000', '#ffa500', '#696969', '#ff69b4',
                      '#4b0082', '#ffd700', '#ffd700', '#d2691e']

        x = list(dataframe_temp['Temperature'])
        y = list(dataframe_temp['Pressure'])
        z = list(dataframe_temp['Mu'])

        fig.add_trace(go.Scatter3d(x=x, y=y, z=z,
                                   mode='markers',
                                   showlegend=True,
                                   name=files_list[i],
                                   marker=dict(size=4,
                                               color=all_colors[i],
                                               opacity=0.8)))

    fig.update_layout(scene=dict(xaxis_title='Temperature [ºC]',
                                 yaxis_title='Pressure [bar]',
                                 zaxis_title='Friction coefficient [-]'))
    fig.update_layout(autosize=True, height=900)

    return fig


def Mu_Press_Graph(dataframe, n_df, files_list, ranges):
    fig = make_subplots(rows=1, cols=4, shared_yaxes=True,
                        column_widths=[0.5, 0.5, 0.5, 0.5],
                        y_title='Friction coefficient', x_title='Temperature [ºC]',
                        horizontal_spacing=0.04,
                        subplot_titles=(str(ranges[0][0]) + "-" + str(ranges[0][1]) + " [bar]",
                                        str(ranges[1][0]) + "-" + str(ranges[1][1]) + " [bar]",
                                        str(ranges[2][0]) + "-" + str(ranges[2][1]) + " [bar]",
                                        str(ranges[3][0]) + "-" + str(ranges[3][1]) + " [bar]"))

    for i in range(0, n_df):
        dataframe_temp = dataframe.loc[dataframe['df_id'] == i + 1]

        all_colors = ['#ff0000', '#0000ff', '#008000', '#ffa500', '#696969', '#ff69b4',
                      '#4b0082', '#ffd700', '#ffd700', '#d2691e']

        if n_df <= 1:
            colors = all_colors[0:4]
        else:
            colors = [all_colors[i], all_colors[i], all_colors[i], all_colors[i], all_colors[i]]

        dataframe_temp.reset_index(drop=True, inplace=True)
        dataframe_temp['Mu_Press_1'] = None
        dataframe_temp['Mu_Press_2'] = None
        dataframe_temp['Mu_Press_3'] = None
        dataframe_temp['Mu_Press_4'] = None
        lr1 = pd.DataFrame()
        lr2 = pd.DataFrame()
        lr3 = pd.DataFrame()
        lr4 = pd.DataFrame()

        for idx in range(1, len(dataframe_temp['Timestamp'])):

            if dataframe_temp.at[idx, 'Pressure'] is not None and dataframe_temp.at[idx, 'Pressure'] > 0 \
                    and dataframe_temp.at[idx, 'Mu'] is not None and dataframe_temp.at[idx, 'Mu'] is not np.nan:

                if ranges[0][0] < dataframe_temp.at[idx, 'Pressure'] < ranges[0][1] and \
                        dataframe_temp.at[idx, 'Temperature'] > 80 and dataframe_temp.at[idx, 'Mu'] > 0:
                    dataframe_temp.at[idx, 'Mu_Press_1'] = dataframe_temp.at[idx, 'Mu']
                    lr1.at[idx, 'Mu'] = dataframe_temp.at[idx, 'Mu']
                    lr1.at[idx, 'Temperature'] = dataframe_temp.at[idx, 'Temperature']

                if ranges[1][0] < dataframe_temp.at[idx, 'Pressure'] < ranges[1][1] and \
                        dataframe_temp.at[idx, 'Temperature'] > 80 and dataframe_temp.at[idx, 'Mu'] > 0:
                    dataframe_temp.at[idx, 'Mu_Press_2'] = dataframe_temp.at[idx, 'Mu']
                    lr2.at[idx, 'Mu'] = dataframe_temp.at[idx, 'Mu']
                    lr2.at[idx, 'Temperature'] = dataframe_temp.at[idx, 'Temperature']

                if ranges[2][0] < dataframe_temp.at[idx, 'Pressure'] < ranges[2][1] and \
                        dataframe_temp.at[idx, 'Temperature'] > 80 and dataframe_temp.at[idx, 'Mu'] > 0:
                    dataframe_temp.at[idx, 'Mu_Press_3'] = dataframe_temp.at[idx, 'Mu']
                    lr3.at[idx, 'Mu'] = dataframe_temp.at[idx, 'Mu']
                    lr3.at[idx, 'Temperature'] = dataframe_temp.at[idx, 'Temperature']

                if ranges[3][0] < dataframe_temp.at[idx, 'Pressure'] < ranges[3][1] and \
                        dataframe_temp.at[idx, 'Temperature'] > 80 and dataframe_temp.at[idx, 'Mu'] > 0:
                    dataframe_temp.at[idx, 'Mu_Press_4'] = dataframe_temp.at[idx, 'Mu']
                    lr4.at[idx, 'Mu'] = dataframe_temp.at[idx, 'Mu']
                    lr4.at[idx, 'Temperature'] = dataframe_temp.at[idx, 'Temperature']

        lr1['Mu'], lr1['X'] = polynomical_regression(lr1, 'Temperature')
        lr2['Mu'], lr2['X'] = polynomical_regression(lr2, 'Temperature')
        lr3['Mu'], lr3['X'] = polynomical_regression(lr3, 'Temperature')
        lr4['Mu'], lr4['X'] = polynomical_regression(lr4, 'Temperature')

        fig.add_trace(go.Scatter(
            x=dataframe_temp['Temperature'],
            y=dataframe_temp['Mu_Press_1'],
            name=files_list[i], mode="markers",
            line_color=colors[0],
            legendgroup=str(i),
            showlegend=True
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=lr1['X'],
            y=lr1['Mu'],
            showlegend=False,
            line=dict(color=colors[0], width=4),
            legendgroup=str(i)
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=dataframe_temp['Temperature'],
            y=dataframe_temp['Mu_Press_2'],
            mode="markers",
            line_color=colors[1],
            legendgroup=str(i),
            showlegend=False
        ), row=1, col=2)

        fig.add_trace(go.Scatter(
            x=lr2['X'],
            y=lr2['Mu'],
            showlegend=False,
            line=dict(color=colors[1], width=4),
            legendgroup=str(i)
        ), row=1, col=2)

        fig.add_trace(go.Scatter(
            x=dataframe_temp['Temperature'],
            y=dataframe_temp['Mu_Press_3'],
            mode="markers",
            line_color=colors[2],
            legendgroup=str(i),
            showlegend=False
        ), row=1, col=3)

        fig.add_trace(go.Scatter(
            x=lr3['X'],
            y=lr3['Mu'],
            legendgroup=str(i),
            line=dict(color=colors[2], width=4),
            showlegend=False
        ), row=1, col=3)

        fig.add_trace(go.Scatter(
            x=dataframe_temp['Temperature'],
            y=dataframe_temp['Mu_Press_4'],
            mode="markers",
            line_color=colors[3],
            legendgroup=str(i),
            showlegend=False
        ), row=1, col=4)

        fig.add_trace(go.Scatter(
            x=lr4['X'],
            y=lr4['Mu'],
            legendgroup=str(i),
            line=dict(color=colors[3], width=4),
            showlegend=False
        ), row=1, col=4)

    large_rockwell_template = dict(layout=go.Layout(title_font=dict(family='Rockwell', size=20)))
    fig.update_layout(template=large_rockwell_template, showlegend=True, legend_groupclick='togglegroup')
    fig.update_layout(height=650)
    fig.update_xaxes(zeroline=True)
    fig.update_layout(hovermode='y')
    fig.update_traces(yaxis='y1', hoverinfo='y')
    fig.update_xaxes(showspikes=True, spikecolor='black', spikemode='across',
                     spikethickness=1, spikedash='solid', rangemode='nonnegative', zeroline=False)
    fig.update_yaxes(showspikes=True, spikecolor='black', spikemode='across',
                     spikethickness=1, spikedash='solid')
    fig.update_yaxes(row=1, col=1, zeroline=True, rangemode='nonnegative')
    fig.update_yaxes(row=1, col=2, zeroline=True, rangemode='nonnegative')
    fig.update_yaxes(row=1, col=3, zeroline=True, rangemode='nonnegative')
    fig.update_yaxes(row=1, col=4, zeroline=True, rangemode='nonnegative')
    fig.update_traces(marker=dict(size=2), selector=dict(mode='markers'))

    return fig


def Mu_Temp_Graph(dataframe, n_df, files_list, ranges):
    fig = make_subplots(rows=1, cols=4, shared_yaxes=True,
                        column_widths=[0.5, 0.5, 0.5, 0.5],
                        y_title='Friction coefficient', x_title='Pressure [bar]',
                        horizontal_spacing=0.04,
                        subplot_titles=(str(ranges[0][0]) + "-" + str(ranges[0][1]) + " [ºC]",
                                        str(ranges[1][0]) + "-" + str(ranges[1][1]) + " [ºC]",
                                        str(ranges[2][0]) + "-" + str(ranges[2][1]) + " [ºC]",
                                        str(ranges[3][0]) + "-" + str(ranges[3][1]) + " [ºC]"))

    for i in range(0, n_df):
        dataframe_temp = dataframe.loc[dataframe['df_id'] == i + 1]

        all_colors = ['#ff0000', '#0000ff', '#008000', '#ffa500', '#696969', '#ff69b4',
                      '#4b0082', '#ffd700', '#ffd700', '#d2691e']

        if n_df <= 1:
            colors = all_colors[0:4]
        else:
            colors = [all_colors[i], all_colors[i], all_colors[i], all_colors[i], all_colors[i]]

        dataframe_temp.reset_index(drop=True, inplace=True)
        dataframe_temp['Mu_Temp_1'] = None
        dataframe_temp['Mu_Temp_2'] = None
        dataframe_temp['Mu_Temp_3'] = None
        dataframe_temp['Mu_Temp_4'] = None
        lr1 = pd.DataFrame()
        lr2 = pd.DataFrame()
        lr3 = pd.DataFrame()
        lr4 = pd.DataFrame()

        for idx in range(1, len(dataframe_temp['Timestamp'])):

            if dataframe_temp.at[idx, 'Temperature'] is not None and dataframe_temp.at[idx, 'Mu'] is not None and \
                    dataframe_temp.at[idx, 'Mu'] is not np.nan:

                if ranges[0][0] < dataframe_temp.at[idx, 'Temperature'] < ranges[0][1] and \
                        10 < dataframe_temp.at[idx, 'Pressure'] and dataframe_temp.at[idx, 'Mu'] > 0:
                    dataframe_temp.at[idx, 'Mu_Temp_1'] = dataframe_temp.at[idx, 'Mu']
                    lr1.at[idx, 'Mu'] = dataframe_temp.at[idx, 'Mu']
                    lr1.at[idx, 'Pressure'] = dataframe_temp.at[idx, 'Pressure']

                if ranges[1][0] < dataframe_temp.at[idx, 'Temperature'] < ranges[1][1] and \
                        10 < dataframe_temp.at[idx, 'Pressure'] and dataframe_temp.at[idx, 'Mu'] > 0:
                    dataframe_temp.at[idx, 'Mu_Temp_2'] = dataframe_temp.at[idx, 'Mu']
                    lr2.at[idx, 'Mu'] = dataframe_temp.at[idx, 'Mu']
                    lr2.at[idx, 'Pressure'] = dataframe_temp.at[idx, 'Pressure']

                if ranges[2][0] < dataframe_temp.at[idx, 'Temperature'] < ranges[2][1] and \
                        10 < dataframe_temp.at[idx, 'Pressure'] and dataframe_temp.at[idx, 'Mu'] > 0:
                    dataframe_temp.at[idx, 'Mu_Temp_3'] = dataframe_temp.at[idx, 'Mu']
                    lr3.at[idx, 'Mu'] = dataframe_temp.at[idx, 'Mu']
                    lr3.at[idx, 'Pressure'] = dataframe_temp.at[idx, 'Pressure']

                if ranges[3][0] < dataframe_temp.at[idx, 'Temperature'] < ranges[3][1] and \
                        10 < dataframe_temp.at[idx, 'Pressure'] and dataframe_temp.at[idx, 'Mu'] > 0:
                    dataframe_temp.at[idx, 'Mu_Temp_4'] = dataframe_temp.at[idx, 'Mu']
                    lr4.at[idx, 'Mu'] = dataframe_temp.at[idx, 'Mu']
                    lr4.at[idx, 'Pressure'] = dataframe_temp.at[idx, 'Pressure']

        lr1['Mu'], lr1['X'] = polynomical_regression(lr1, 'Pressure')
        lr2['Mu'], lr2['X'] = polynomical_regression(lr2, 'Pressure')
        lr3['Mu'], lr3['X'] = polynomical_regression(lr3, 'Pressure')
        lr4['Mu'], lr4['X'] = polynomical_regression(lr4, 'Pressure')

        fig.add_trace(go.Scatter(
            x=dataframe_temp['Pressure'],
            y=dataframe_temp['Mu_Temp_1'],
            name=files_list[i], mode="markers",
            line_color=colors[0],
            legendgroup=str(i),
            showlegend=True,
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=lr1['X'],
            y=lr1['Mu'],
            showlegend=False,
            line=dict(color=colors[0], width=4),
            legendgroup=str(i)
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=dataframe_temp['Pressure'],
            y=dataframe_temp['Mu_Temp_2'],
            mode='markers',
            line_color=colors[1],
            legendgroup=str(i),
            showlegend=False
        ), row=1, col=2)

        fig.add_trace(go.Scatter(
            x=lr2['X'],
            y=lr2['Mu'],
            legendgroup=str(i),
            line=dict(color=colors[1], width=4),
            showlegend=False
        ), row=1, col=2)

        fig.add_trace(go.Scatter(
            x=dataframe_temp['Pressure'],
            y=dataframe_temp['Mu_Temp_3'],
            mode='markers',
            line_color=colors[2],
            legendgroup=str(i),
            showlegend=False
        ), row=1, col=3)

        fig.add_trace(go.Scatter(
            x=lr3['X'],
            y=lr3['Mu'],
            legendgroup=str(i),
            line=dict(color=colors[2], width=4),
            showlegend=False
        ), row=1, col=3)

        fig.add_trace(go.Scatter(
            x=dataframe_temp['Pressure'],
            y=dataframe_temp['Mu_Temp_4'],
            mode='markers',
            line_color=colors[3],
            legendgroup=str(i),
            showlegend=False
        ), row=1, col=4)

        fig.add_trace(go.Scatter(
            x=lr4['X'],
            y=lr4['Mu'],
            legendgroup=str(i),
            line=dict(color=colors[3], width=4),
            showlegend=False
        ), row=1, col=4)

    large_rockwell_template = dict(layout=go.Layout(title_font=dict(family='Rockwell', size=20)))
    fig.update_layout(template=large_rockwell_template, showlegend=True, legend_groupclick='togglegroup')
    fig.update_layout(height=650)
    fig.update_xaxes(zeroline=True)
    fig.update_layout(hovermode='y')
    fig.update_traces(yaxis='y1', hoverinfo='y')
    fig.update_xaxes(showspikes=True, spikecolor='black', spikemode='across',
                     spikethickness=1, spikedash='solid', rangemode='nonnegative', zeroline=False)
    fig.update_yaxes(showspikes=True, spikecolor='black', spikemode='across',
                     spikethickness=1, spikedash='solid')
    fig.update_yaxes(row=1, col=1, zeroline=True, rangemode='nonnegative')
    fig.update_yaxes(row=1, col=2, zeroline=True, rangemode='nonnegative')
    fig.update_yaxes(row=1, col=3, zeroline=True, rangemode='nonnegative')
    fig.update_yaxes(row=1, col=4, zeroline=True, rangemode='nonnegative')
    fig.update_traces(marker=dict(size=2), selector=dict(mode='markers'))

    return fig


def graph_X_Y(dataframe, n_df, files_list):
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Pedal Stiffness", "Torque-Brake Press"))

    for i in range(0, n_df):
        dataframe_temp = dataframe.loc[dataframe['df_id'] == i + 1]

        all_colors = ['#ff0000', '#0000ff', '#008000', '#ffa500', '#696969', '#ff69b4',
                      '#4b0082', '#ffd700', '#ffd700', '#d2691e']

        if n_df <= 1:
            colors = all_colors[0:2]
        else:
            colors = [all_colors[i], all_colors[i], all_colors[i], all_colors[i], all_colors[i]]

        fig.add_trace(go.Scatter(x=dataframe_temp['Brake_Position'],
                                 y=dataframe_temp['Pressure'],
                                 mode='markers',
                                 showlegend=True,
                                 name=files_list[i],
                                 line_color=colors[0],
                                 legendgroup=str(i)
                                 ), row=1, col=1)

        fig.add_trace(go.Scatter(x=dataframe_temp['Pressure'],
                                 y=dataframe_temp['Load'],
                                 mode='markers',
                                 showlegend=False,
                                 line_color=colors[1],
                                 legendgroup=str(i)
                                 ), row=1, col=2)

    large_rockwell_template = dict(layout=go.Layout(title_font=dict(family='Rockwell', size=20)))
    fig.update_layout(template=large_rockwell_template, showlegend=True, legend_groupclick='togglegroup')
    fig.update_layout(height=600)
    fig.update_xaxes(zeroline=True)
    fig.update_layout(hovermode='y')
    fig.update_traces(hoverinfo='all')
    fig.update_xaxes(showspikes=True, spikecolor='black', spikemode='across',
                     spikethickness=1, spikedash='solid', rangemode='nonnegative', zeroline=False)
    fig.update_yaxes(showspikes=True, spikecolor='black', spikemode='across',
                     spikethickness=1, spikedash='solid')
    fig.update_yaxes(title_text='Brake_Press [bar]', row=1, col=1)
    fig.update_yaxes(title_text='Brake_Torque [Nm]', row=1, col=2)
    fig.update_xaxes(title_text='Brake Position [mm]', row=1, col=1)
    fig.update_xaxes(title_text='Brake_Press [bar]', row=1, col=2)
    fig.update_traces(marker=dict(size=3), selector=dict(mode='markers'))

    return fig


# =============================================================================
# Main DASH
# =============================================================================


app = DashProxy(external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True,
                transforms=[MultiplexerTransform()])
server = app.server

tabs_styles = {
    'height': '44px',
    'width': '100%',
    'z-index': '128'
}
tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold'
}
tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#119DFF',
    'color': 'white',
    'padding': '6px',
    'fontWeight': 'bold'
}

app.layout = html.Div([
    dcc.Store(id='memory-dataframe', storage_type='session', data=0),
    html.H2(id='tittle', children='Campos Racing Engineering', style={'text-align': 'center', 'fontSize': 24}),
    html.Blockquote(),
    html.Div([
        html.Blockquote(),
        dcc.Dropdown(['Formula 2', 'Formula 3', 'Formula 4'], 'Formula 3', id='championship',
                     style={'height': '60px', 'fontSize': 18}),
        html.Blockquote(),
        dbc.Button('Clear Data', id="clear_data", n_clicks=0,
                   style={'background-color': 'Grey', 'height': '60px', 'fontSize': 18}),
        html.Blockquote(),
        dcc.Upload(id='upload-data', children=html.Div(['Drag and Drop or ', html.A('Select File')]),
                   style={'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px', 'borderStyle': 'dashed',
                          'borderRadius': '5px', 'textAlign': 'center', 'background': 'lightyellow', 'fontSize': 20},
                   # Allow multiple files to be uploaded
                   multiple=True),
        html.Blockquote(),
        dbc.Button('Download graph', id="download", style={'background-color': 'Blue', 'height': '60px',
                                                           'fontSize': 18}),
        html.Blockquote(),
        dbc.Modal(
            [
                dbc.ModalHeader("Download options"),
                dbc.ModalBody(["Path to download",
                               dcc.Textarea(id='path', value="", style={'width': '100%'}, cols='1'),
                               "File name",
                               dcc.Textarea(id='file_name', value="", style={'width': '100%'}, cols='1')]),
                dbc.ModalFooter(dbc.Button("Download", id="btn_dwn", className="ml-auto")),
            ],
            id="modal",  # Give the modal an id name
            is_open=False,  # Open the modal at opening the webpage.
            size="xl",  # "sm", "lg", "xl" = small, large or extra large
            backdrop=True,  # Modal to not be closed by clicking on backdrop
            scrollable=True,  # Scrollable in case of large amount of text
            centered=True,  # Vertically center modal
            keyboard=True,  # Close modal when escape is pressed
            fade=True,  # True, False
            style={"max-width": "none", "width": "100%"}
        ),
    ], style={"display": "grid", "grid-template-columns": "0.5% 10% 0.5% 10% 0.5% 67% 0.5% 10% 1%", 'height': '60px'}),

    html.Blockquote(),

    html.Div([
        html.Blockquote(),
        dcc.Tabs(id="tabs",
                 value='tab-6',
                 children=[dcc.Tab(id='Results_tab', value='tab-1', label='RESULTS', style=tab_style,
                                   selected_style=tab_selected_style, disabled=True),
                           dcc.Tab(id='xyz_tab', value='tab-2', label='3D', style=tab_style,
                                   selected_style=tab_selected_style, disabled=True),
                           dcc.Tab(id='Mu-Temp_tab', value='tab-3', label='μ-P @ T', style=tab_style,
                                   selected_style=tab_selected_style, disabled=True),
                           dcc.Tab(id='Mu-P_tab', value='tab-4', label='μ-T @ P', style=tab_style,
                                   selected_style=tab_selected_style, disabled=True),
                           dcc.Tab(id='k_tab', value='tab-5', label='X-Y', style=tab_style,
                                   selected_style=tab_selected_style, disabled=True),
                           dcc.Tab(id='File_tab', value='tab-6', label='FILE', style=tab_style,
                                   selected_style=tab_selected_style, disabled=False)],
                 style=tabs_styles),
    ]),
])


# =============================================================================
# Functions and Callback
# =============================================================================


def Process_Output_df(df_process, df_id):
    global df_final
    output = df_process
    output = output.set_index('Index')

    mufactor = 1 / ((eff_diam / 2000) * 100000 * pistons_section)

    output['Mu_No_Filtered'] = None
    output['Mu'] = None
    output['Pressure_diff'] = None
    output['df_id'] = None

    output['Load'] = output['Load'].abs()
    for i in range(1, len(output['Timestamp']) + 1):

        # ------------------------------------------------- RPM filter due to peaks read by sensor
        if output.at[i, 'RPM'] > 2950:
            output.at[i, 'RPM'] = output.at[i - 1, 'RPM']

        if output.at[i, 'RPM_Average'] - output.at[i, 'RPM'] > 100:
            output.at[i, 'RPM_Average'] = output.at[i, 'RPM']

        if output.at[i, 'Temperature'] < 80:
            output.at[i, 'Temperature'] = None

        if i == 1:
            output.at[i, 'Timestamp'] = 0
        else:
            output.at[i, 'Timestamp'] = output.at[i - 1, 'Timestamp'] + 0.01

        if output.at[i, 'Pressure'] > 5 and output.at[i, 'Load'] > 30:
            output.at[i, 'Mu_No_Filtered'] = output.at[i, 'Load'] / output.at[i, 'Pressure'] * mufactor

        output.at[i, 'df_id'] = df_id

    output['RPM'] = savgol_filter(output['RPM'], 20, 3)
    output['Pressure'] = savgol_filter(output['Pressure'], 10, 3)
    output['Temperature'] = savgol_filter(output['Temperature'], 10, 3)
    output['Load'] = savgol_filter(output['Load'], 10, 3)

    output['Pressure_diff'] = output['Pressure'].diff()
    output['Pressure_diff'] = savgol_filter(output['Pressure_diff'], 10, 3)
    output['Mu'] = savgol_filter(output['Mu_No_Filtered'], 10, 3)

    for i in range(1, len(output['Timestamp']) + 1):
        if output.at[i, 'Pressure_diff'] > 1:
            output.at[i, 'Mu'] = None

    if df_id == 1:
        df_final = output
    if df_id > 1:
        for i in range(1, df_id):
            df_final = pd.concat([df_final, output])
    df_final = df_final.round(decimals=3)

    return df_final


def Parse_Contents(contents, filename, date_file, df_id):
    global df_read
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df_read = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')),
                sep=None, engine='python',
                header=0,
                names=['Index', 'Timestamp', 'RPM', 'RPM_Average', 'Temperature', 'Load', 'Pressure', 'Brake_Position']
            )
            df_read = Process_Output_df(df_read, df_id)
        elif 'xls' in filename:
            # Assume that the user uploaded an Excel file
            df_read = pd.read_excel(io.BytesIO(decoded), sheet_name=0)
            df_read = Process_Output_df(df_read, df_id)
    except Exception as e:
        print(e)
        return [0, [html.Div([
            'There was an error processing this file.'
        ]), '']]

    df_read = df_read.reset_index()
    list_of_files_temp.append(filename)
    list_of_dates_temp.append(date_file)
    if len(list_of_dates_temp) == 1:
        list_of_dates_temp[0] = str(datetime.datetime.fromtimestamp(list_of_dates_temp[0]))
    if len(list_of_files_temp) > 1:
        list_of_files_temp[len(list_of_files_temp) - 1] = " + " + list_of_files_temp[len(list_of_files_temp) - 1]
        list_of_dates_temp[len(list_of_dates_temp) - 1] = " + " + \
                                                          str(datetime.datetime.fromtimestamp(
                                                              list_of_dates_temp[len(list_of_dates_temp) - 1]))
    return [df_read, html.Div([
        html.Blockquote(),
        html.H5(list_of_files_temp),
        html.H6(list_of_dates_temp),
        dash_table.DataTable(
            id="table",
            data=df_read.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df_read.columns]
        ),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])]


# Update Output
@app.callback(
    [dash.dependencies.Output('memory-dataframe', "data"),
     dash.dependencies.Output('clear_data', "n_clicks"),
     dash.dependencies.Output('tabs', "value"),
     dash.dependencies.Output("upload-data", "contents"),
     dash.dependencies.Output("upload-data", "filename"),
     dash.dependencies.Output("upload-data", "last_modified")],
    [dash.dependencies.Input("upload-data", "contents"),
     dash.dependencies.Input('clear_data', "n_clicks")],
    [dash.dependencies.State("upload-data", "filename"),
     dash.dependencies.State("championship", "value"),
     dash.dependencies.State("upload-data", "last_modified"),
     dash.dependencies.State("memory-dataframe", "data"),
     dash.dependencies.State('tabs', "value")], prevent_initial_call=True)
def update_output(list_of_contents, btn_clear, list_of_names, car, list_dates, df_id, tab_actual):
    global df, pistons_section, eff_diam, list_of_files, list_of_dates, list_of_files_temp, list_of_dates_temp, \
        slider_values, slider_list, mu_press_slider_ranges, mu_temp_slider_ranges, slider_range, fig_range, \
        children_file_tab, tab6, results_range

    if df_id == 0:
        list_of_files = ['None']
        list_of_dates = []
        list_of_files_temp = []
        list_of_dates_temp = []
        slider_values = [0.1, 1, 5, 25]
        slider_list = []
        mu_press_slider_ranges = [[12, 15], [25, 30], [40, 45], [50, 60]]
        mu_temp_slider_ranges = [[100, 200], [200, 300], [300, 400], [400, 500]]
        slider_range = [-25, 25, 0, 1, {i: '{}'.format(i) for i in range(-25, 26)}]
        fig_range = []
        df = None

    if btn_clear != 0:
        list_of_files_temp.clear()
        list_of_dates_temp.clear()
        list_of_dates.clear()
        list_of_files.clear()
        list_of_files.append("None")
        slider_list.clear()
    btn_clear_temp = 0

    if list_of_names is not None and btn_clear == 0:
        if list_of_files[0] == 'None':
            list_of_files[0] = list_of_names[0]
            slider_list.append([list_of_names[0], 1, 0])
        else:
            list_of_files.append(list_of_names[0])
            slider_list.append([list_of_names[0], 1, 0])

    if car == 'Formula 2':
        pistons_section = 0.0045
        eff_diam = 240.467
    elif car == 'Formula 3':
        pistons_section = 0.0039
        eff_diam = 240.467
    elif car == 'Formula 4':
        pistons_section = 0.0028
        eff_diam = 238
    else:
        pistons_section = 0.0030
        eff_diam = 240

    if list_of_contents is not None and btn_clear == 0:
        df_id += 1

        results_temp = [
            Parse_Contents(c, n, d, df_id) for c, n, d in
            zip(list_of_contents, list_of_names, list_dates)]

        tab6 = results_temp[0][1]
        df = results_temp[0][0]
        results_range = None

        return df_id, btn_clear_temp, tab_actual, None, None, None
    else:
        tab6 = instructions_brakevisualizer
        df_id = 0
        return df_id, btn_clear_temp, 'tab-6', None, None, None


# disable tabs
@app.callback([dash.dependencies.Output('Results_tab', "children"),
               dash.dependencies.Output('xyz_tab', "children"),
               dash.dependencies.Output('Mu-Temp_tab', "children"),
               dash.dependencies.Output('Mu-P_tab', "children"),
               dash.dependencies.Output('k_tab', "children"),
               dash.dependencies.Output('File_tab', "children"),
               dash.dependencies.Output('Results_tab', "disabled"),
               dash.dependencies.Output('xyz_tab', "disabled"),
               dash.dependencies.Output('Mu-Temp_tab', "disabled"),
               dash.dependencies.Output('Mu-P_tab', "disabled"),
               dash.dependencies.Output('k_tab', "disabled"),
               dash.dependencies.Output('File_tab', "disabled")],
              [dash.dependencies.Input("memory-dataframe", "data"),
               dash.dependencies.Input('tabs', "value")], prevent_initial_call=False)
def enable_tabs(df_id, tab):
    if df_id > 0:
        if tab == 'tab-1':
            global fig_results, fig_results_inf, tab1, results_range
            if results_range is None:
                results_range = [int(df['Index'].min()), int(df['Index'].max())]
            fig_results = Results_Graph(df, df_id, list_of_files, results_range)
            fig_results_inf = Mu_Results_Tab(df, df_id, list_of_files, results_range)

            tab1 = \
                html.Div([
                    html.Blockquote(),
                    html.Div([
                        html.Blockquote(),
                        dcc.Dropdown(list_of_files, list_of_files[0], id='graph_selected'),
                        html.Blockquote(),
                        dcc.Dropdown(slider_values, slider_values[1], id='slide_move'),
                        html.Blockquote(),
                        dcc.Slider(id='slider', min=slider_range[0], max=slider_range[1], value=slider_range[2],
                                   step=slider_range[3], marks=slider_range[4]),
                        html.Blockquote(),
                    ], style={"display": "grid", "grid-template-columns": "0.5% 22% 0.5% 5% 0.5% 71% 1%"}),
                    html.Div([dcc.Graph(id='RESULTS', figure=fig_results)], style={'width': '100%'}),
                    html.Div([dcc.Graph(id='RESULTS_INF', figure=fig_results_inf)], style={'width': '100%'})
                ])

            return tab1, [0], [0], [0], [0], [0], False, False, False, False, False, False
        elif tab == 'tab-2':
            global fig_3d, tab2
            fig_3d = Graph_3d(df, df_id, list_of_files)

            tab2 = \
                html.Div([
                    dcc.Graph(id='3D', figure=fig_3d)], style={'width': '100%'})

            return [0], tab2, [0], [0], [0], [0], False, False, False, False, False, False
        elif tab == 'tab-3':
            global fig_mu_press, tab3
            fig_mu_press = Mu_Press_Graph(df, df_id, list_of_files, mu_press_slider_ranges)

            tab3 = \
                html.Div([
                    html.Div([
                        html.Blockquote(),
                        html.H2(id='tittle_press_graph',
                                children='Effect of Temperature on Mu for different Pressure targets',
                                style={'text-align': 'center', 'fontSize': 20}),
                        html.Blockquote()]),

                    html.Div([
                        html.Blockquote(),
                        dcc.RangeSlider(id='slider_press_1', min=10, max=100, value=[mu_press_slider_ranges[0][0],
                                                                                     mu_press_slider_ranges[0][1]],
                                        tooltip={"placement": "bottom", "always_visible": True}),
                        html.Blockquote(),
                        dcc.RangeSlider(id='slider_press_2', min=10, max=100, value=[mu_press_slider_ranges[1][0],
                                                                                     mu_press_slider_ranges[1][1]],
                                        tooltip={"placement": "bottom", "always_visible": True}),
                        html.Blockquote(),
                        dcc.RangeSlider(id='slider_press_3', min=10, max=100, value=[mu_press_slider_ranges[2][0],
                                                                                     mu_press_slider_ranges[2][1]],
                                        tooltip={"placement": "bottom", "always_visible": True}),
                        html.Blockquote(),
                        dcc.RangeSlider(id='slider_press_4', min=10, max=100, value=[mu_press_slider_ranges[3][0],
                                                                                     mu_press_slider_ranges[3][1]],
                                        tooltip={"placement": "bottom", "always_visible": True}),
                        html.Blockquote(),
                    ], style={"display": "grid", "grid-template-columns": "2% 20% 1% 20% 1% 20% 1% 20% 15%"}),
                    html.Blockquote(),

                    html.Div([
                        dcc.Graph(id='Mu-P', figure=fig_mu_press)], style={'width': '100%'})
                ])

            return [0], [0], tab3, [0], [0], [0], False, False, False, False, False, False
        elif tab == 'tab-4':
            global fig_mu_temp, tab4
            fig_mu_temp = Mu_Temp_Graph(df, df_id, list_of_files, mu_temp_slider_ranges)

            tab4 = \
                html.Div([
                    html.Div([
                        html.Blockquote(),
                        html.H2(id='tittle_press_graph', children='Effect of Pressure on Mu for different Temp Windows',
                                style={'text-align': 'center', 'fontSize': 20}),
                        html.Blockquote()]),

                    html.Div([
                        html.Blockquote(),
                        dcc.RangeSlider(id='slider_temp_1', min=80, max=1000, value=[mu_temp_slider_ranges[0][0],
                                                                                     mu_temp_slider_ranges[0][1]],
                                        tooltip={"placement": "bottom", "always_visible": True}),
                        html.Blockquote(),
                        dcc.RangeSlider(id='slider_temp_2', min=80, max=1000, value=[mu_temp_slider_ranges[1][0],
                                                                                     mu_temp_slider_ranges[1][1]],
                                        tooltip={"placement": "bottom", "always_visible": True}),
                        html.Blockquote(),
                        dcc.RangeSlider(id='slider_temp_3', min=80, max=1000, value=[mu_temp_slider_ranges[2][0],
                                                                                     mu_temp_slider_ranges[2][1]],
                                        tooltip={"placement": "bottom", "always_visible": True}),
                        html.Blockquote(),
                        dcc.RangeSlider(id='slider_temp_4', min=80, max=1000, value=[mu_temp_slider_ranges[3][0],
                                                                                     mu_temp_slider_ranges[3][1]],
                                        tooltip={"placement": "bottom", "always_visible": True}),
                        html.Blockquote(),
                    ], style={"display": "grid", "grid-template-columns": "2% 20% 1% 20% 1% 20% 1% 20% 15%"}),
                    html.Blockquote(),
                    html.Div([
                        dcc.Graph(id='Mu-Temp', figure=fig_mu_temp)], style={'width': '100%'})
                ])

            return [0], [0], [0], tab4, [0], [0], False, False, False, False, False, False
        elif tab == 'tab-5':
            global fig_xy, tab5
            fig_xy = graph_X_Y(df, df_id, list_of_files)

            tab5 = \
                html.Div([
                    dcc.Graph(id='X-Y', figure=fig_xy)], style={'width': '100%'})

            return [0], [0], [0], [0], tab5, [0], False, False, False, False, False, False
        else:
            return [0], [0], [0], [0], [0], tab6, False, False, False, False, False, False
    else:
        return [0], [0], [0], [0], [0], instructions_brakevisualizer, True, True, True, True, True, False


# dropdown files list tab1
@app.callback(
    [dash.dependencies.Output('graph_selected', "options"),
     dash.dependencies.Output('graph_selected', "value")],
    [dash.dependencies.Input('tabs', 'value'),
     dash.dependencies.Input("memory-dataframe", "data")], prevent_initial_call=True)
def enable_dropdown_list(tab, df_id):
    if df_id > 0 and tab == 'tab-1':
        list_of_files_temp1 = list(dict.fromkeys(list_of_files))
        return list_of_files_temp1, list_of_files_temp1[0]
    else:
        return [0], [0]


# Slider options tab1
@app.callback(
    [dash.dependencies.Output('slider', "min"),
     dash.dependencies.Output('slider', "max"),
     dash.dependencies.Output('slider', "step"),
     dash.dependencies.Output('slider', "marks"),
     dash.dependencies.Output('slider', "value")],
    dash.dependencies.Input("slide_move", "value"),
    dash.dependencies.State('graph_selected', "value"), prevent_initial_call=True)
def slider_range(dropdown_value, graph_selected):
    for i in range(len(slider_list)):
        if slider_list[i][0] == graph_selected:
            slider_list[i][1] = dropdown_value

    if dropdown_value == 1:
        return -dropdown_value * 25, dropdown_value * 25, dropdown_value, \
               {i: '{}'.format(i) for i in range(-dropdown_value * 25, (dropdown_value * 25) + 1, dropdown_value)}, 0
    elif dropdown_value == 0.1:
        dicc = {}
        for i in range(-21, 21):
            if str(i / 10)[-1] == '0':
                dicc[int(i / 10)] = str(i / 10)
            else:
                dicc[i / 10] = str(i / 10)
        return -dropdown_value * 20, dropdown_value * 20, dropdown_value, dicc, 0
    elif dropdown_value == 5 or dropdown_value == 25:
        return -dropdown_value * 20, dropdown_value * 20, dropdown_value, \
               {i: '{}'.format(i) for i in range(-dropdown_value * 20, (dropdown_value * 20) + 1,
                                                 dropdown_value * 2)}, 0


# Slider update tab1
@app.callback(
    dash.dependencies.Output('slide_move', "value"),
    dash.dependencies.Input('graph_selected', "value"), prevent_initial_call=True)
def update_slider(graph_selected):
    if len(slider_list) > 0:
        for i in range(len(slider_list)):
            if slider_list[i][0] == graph_selected:
                return slider_list[i][1]
    else:
        return 1


# Update results graph
@app.callback(
    dash.dependencies.Output("RESULTS", "figure"),
    [dash.dependencies.Input('slider', 'value'),
     dash.dependencies.Input("memory-dataframe", "data")],
    [dash.dependencies.State('graph_selected', "value"),
     dash.dependencies.State("RESULTS", "figure")], prevent_initial_call=True)
def results_graph_update(slider_value, df_id, graph_selected, figure_actual):
    global df

    if figure_actual is None and df_id != 0:
        return fig_results

    elif len(figure_actual['data']) != len(slider_list) * 6:
        return fig_results

    elif slider_value != 0:
        for element in range(0, len(figure_actual['data'])):
            for i in range(len(slider_list)):
                if slider_list[i][0] == graph_selected:
                    if figure_actual['data'][element]['name'] == slider_list[i][0]:
                        figure_actual['data'][element]['x'] = \
                            [i if i is not None else 0 for i in figure_actual['data'][element]['x']]
                        figure_actual['data'][element]['x'] = np.array(figure_actual['data'][element]['x']) + \
                            slider_value - slider_list[i][2]

        new_dataframe = pd.DataFrame()
        for i in range(1, df_id):
            dataframe_temp = df.loc[df['df_id'] == i]
            for idx in range(len(slider_list)):
                if slider_list[idx][0] == graph_selected:
                    if idx == i:
                        for element in range(0, len(dataframe_temp['Timestamp'])):
                            dataframe_temp.at[element, 'Timestamp'] = dataframe_temp.at[element, 'Timestamp'] + \
                                slider_value - slider_list[idx][2]
            new_dataframe = pd.concat([new_dataframe, dataframe_temp])

        df = new_dataframe.copy()

        for i in range(len(slider_list)):
            if slider_list[i][0] == graph_selected:
                slider_list[i][2] = slider_value

        return figure_actual

    else:
        for i in range(len(slider_list)):
            if slider_list[i][0] == graph_selected:
                slider_list[i][2] = slider_value
        return figure_actual


# Update results inf graph
@app.callback(
    dash.dependencies.Output("RESULTS_INF", "figure"),
    [dash.dependencies.Input("RESULTS", "relayoutData"),
     dash.dependencies.Input("memory-dataframe", "data")],
    dash.dependencies.State("RESULTS", "figure"), prevent_initial_call=True)
def results_inf_graph_update(results_change, df_id, figure_states_results):
    global results_range, fig_results_inf, df
    if figure_states_results is None and df_id != 0 and results_change is not None:
        return fig_results_inf
    else:
        results_range = figure_states_results['layout']['xaxis']['range']
        results_range = [int(x*100) for x in results_range]
        fig_results_inf = Mu_Results_Tab(df, df_id, list_of_files, results_range)

        return fig_results_inf


# Update press-mu graph slider1
@app.callback(
    dash.dependencies.Output('Mu-P', "figure"),
    dash.dependencies.Input("slider_press_1", "value"),
    [dash.dependencies.State('Mu-P', "figure"),
     dash.dependencies.State("memory-dataframe", "data")], prevent_initial_call=True)
def update_graph_press_slider1(slider1, figure_actual, df_id):
    global df
    if figure_actual is None:
        return fig_mu_press
    else:
        for i in range(0, df_id):
            dataframe_temp = df.loc[df['df_id'] == i + 1]
            dataframe_temp.reset_index(drop=True, inplace=True)
            lr = pd.DataFrame()
            dataframe_temp['Mu_Press_1'] = None
            for idx in range(1, len(dataframe_temp['Timestamp'])):

                if dataframe_temp.at[idx, 'Pressure'] is not None and dataframe_temp.at[idx, 'Pressure'] > 0 and \
                        dataframe_temp.at[idx, 'Mu'] is not None and dataframe_temp.at[idx, 'Mu'] is not np.nan:

                    if slider1[0] < dataframe_temp.at[idx, 'Pressure'] < slider1[1] and \
                            dataframe_temp.at[idx, 'Temperature'] > 80 and dataframe_temp.at[idx, 'Mu'] > 0:
                        dataframe_temp.at[idx, 'Mu_Press_1'] = dataframe_temp.at[idx, 'Mu']
                        lr.at[idx, 'Mu'] = dataframe_temp.at[idx, 'Mu']
                        lr.at[idx, 'Temperature'] = dataframe_temp.at[idx, 'Temperature']

            lr['Mu'], lr['X'] = polynomical_regression(lr, 'Temperature')

            act = [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80]
            figure_actual['data'][act[i]]['y'] = np.array(dataframe_temp['Mu_Press_1'])
            figure_actual['data'][act[i] + 1]['x'] = np.array(lr['X'])
            figure_actual['data'][act[i] + 1]['y'] = np.array(lr['Mu'])

        mu_press_slider_ranges[0] = slider1
        figure_actual['layout']['annotations'][0]['text'] = str(slider1[0]) + "-" + str(slider1[1]) + " [bar]"
        return figure_actual


# Update press-mu graph slider2
@app.callback(
    dash.dependencies.Output('Mu-P', "figure"),
    dash.dependencies.Input("slider_press_2", "value"),
    [dash.dependencies.State('Mu-P', "figure"),
     dash.dependencies.State("memory-dataframe", "data")], prevent_initial_call=True)
def update_graph_press_slider2(slider2, figure_actual, df_id):
    global df
    if figure_actual is None:
        return fig_mu_press
    else:
        for i in range(0, df_id):
            dataframe_temp = df.loc[df['df_id'] == i + 1]
            dataframe_temp.reset_index(drop=True, inplace=True)
            lr = pd.DataFrame()
            dataframe_temp['Mu_Press_2'] = None
            for idx in range(1, len(dataframe_temp['Timestamp'])):

                if dataframe_temp.at[idx, 'Pressure'] is not None and dataframe_temp.at[idx, 'Pressure'] > 0 and \
                        dataframe_temp.at[idx, 'Mu'] is not None and dataframe_temp.at[idx, 'Mu'] is not np.nan:

                    if slider2[0] < dataframe_temp.at[idx, 'Pressure'] < slider2[1] and \
                            dataframe_temp.at[idx, 'Temperature'] > 80 and dataframe_temp.at[idx, 'Mu'] > 0:
                        dataframe_temp.at[idx, 'Mu_Press_2'] = dataframe_temp.at[idx, 'Mu']
                        lr.at[idx, 'Mu'] = dataframe_temp.at[idx, 'Mu']
                        lr.at[idx, 'Temperature'] = dataframe_temp.at[idx, 'Temperature']

            lr['Mu'], lr['X'] = polynomical_regression(lr, 'Temperature')

            act = [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80]
            figure_actual['data'][act[i] + 2]['y'] = np.array(dataframe_temp['Mu_Press_2'])
            figure_actual['data'][act[i] + 3]['x'] = np.array(lr['X'])
            figure_actual['data'][act[i] + 3]['y'] = np.array(lr['Mu'])

        mu_press_slider_ranges[1] = slider2
        figure_actual['layout']['annotations'][1]['text'] = str(slider2[0]) + "-" + str(slider2[1]) + " [bar]"
        return figure_actual


# Update press-mu graph slider3
@app.callback(
    dash.dependencies.Output('Mu-P', "figure"),
    dash.dependencies.Input("slider_press_3", "value"),
    [dash.dependencies.State('Mu-P', "figure"),
     dash.dependencies.State("memory-dataframe", "data")], prevent_initial_call=True)
def update_graph_press_slider3(slider3, figure_actual, df_id):
    global df
    if figure_actual is None:
        return fig_mu_press
    else:
        for i in range(0, df_id):
            dataframe_temp = df.loc[df['df_id'] == i + 1]
            dataframe_temp.reset_index(drop=True, inplace=True)
            lr = pd.DataFrame()
            dataframe_temp['Mu_Press_3'] = None
            for idx in range(1, len(dataframe_temp['Timestamp'])):

                if dataframe_temp.at[idx, 'Pressure'] is not None and dataframe_temp.at[idx, 'Pressure'] > 0 and \
                        dataframe_temp.at[idx, 'Mu'] is not None and dataframe_temp.at[idx, 'Mu'] is not np.nan:

                    if slider3[0] < dataframe_temp.at[idx, 'Pressure'] < slider3[1] and \
                            dataframe_temp.at[idx, 'Temperature'] > 80 and dataframe_temp.at[idx, 'Mu'] > 0:
                        dataframe_temp.at[idx, 'Mu_Press_3'] = dataframe_temp.at[idx, 'Mu']
                        lr.at[idx, 'Mu'] = dataframe_temp.at[idx, 'Mu']
                        lr.at[idx, 'Temperature'] = dataframe_temp.at[idx, 'Temperature']

            lr['Mu'], lr['X'] = polynomical_regression(lr, 'Temperature')

            act = [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80]
            figure_actual['data'][act[i] + 4]['y'] = np.array(dataframe_temp['Mu_Press_3'])
            figure_actual['data'][act[i] + 5]['x'] = np.array(lr['X'])
            figure_actual['data'][act[i] + 5]['y'] = np.array(lr['Mu'])

        mu_press_slider_ranges[2] = slider3
        figure_actual['layout']['annotations'][2]['text'] = str(slider3[0]) + "-" + str(slider3[1]) + " [bar]"
        return figure_actual


# Update press-mu graph slider4
@app.callback(
    dash.dependencies.Output('Mu-P', "figure"),
    dash.dependencies.Input("slider_press_4", "value"),
    [dash.dependencies.State('Mu-P', "figure"),
     dash.dependencies.State("memory-dataframe", "data")], prevent_initial_call=True)
def update_graph_press_slider4(slider4, figure_actual, df_id):
    global df
    if figure_actual is None:
        return fig_mu_press
    else:
        for i in range(0, df_id):
            dataframe_temp = df.loc[df['df_id'] == i + 1]
            dataframe_temp.reset_index(drop=True, inplace=True)
            lr = pd.DataFrame()
            dataframe_temp['Mu_Press_4'] = None
            for idx in range(1, len(dataframe_temp['Timestamp'])):

                if dataframe_temp.at[idx, 'Pressure'] is not None and dataframe_temp.at[idx, 'Pressure'] > 0 and \
                        dataframe_temp.at[idx, 'Mu'] is not None and dataframe_temp.at[idx, 'Mu'] is not np.nan:

                    if slider4[0] < dataframe_temp.at[idx, 'Pressure'] < slider4[1] and \
                            dataframe_temp.at[idx, 'Temperature'] > 80 and dataframe_temp.at[idx, 'Mu'] > 0:
                        dataframe_temp.at[idx, 'Mu_Press_4'] = dataframe_temp.at[idx, 'Mu']
                        lr.at[idx, 'Mu'] = dataframe_temp.at[idx, 'Mu']
                        lr.at[idx, 'Temperature'] = dataframe_temp.at[idx, 'Temperature']

            lr['Mu'], lr['X'] = polynomical_regression(lr, 'Temperature')

            act = [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80]
            figure_actual['data'][act[i] + 6]['y'] = np.array(dataframe_temp['Mu_Press_4'])
            figure_actual['data'][act[i] + 7]['x'] = np.array(lr['X'])
            figure_actual['data'][act[i] + 7]['y'] = np.array(lr['Mu'])

        mu_press_slider_ranges[3] = slider4
        figure_actual['layout']['annotations'][3]['text'] = str(slider4[0]) + "-" + str(slider4[1]) + " [bar]"
        return figure_actual


# Update temp-mu graph slider1
@app.callback(
    dash.dependencies.Output('Mu-Temp', "figure"),
    dash.dependencies.Input("slider_temp_1", "value"),
    [dash.dependencies.State('Mu-Temp', "figure"),
     dash.dependencies.State("memory-dataframe", "data")], prevent_initial_call=True)
def update_graph_temp_slider1(slider1, figure_actual, df_id):
    global df
    if figure_actual is None:
        return fig_mu_temp
    else:
        for i in range(0, df_id):
            dataframe_temp = df.loc[df['df_id'] == i + 1]
            dataframe_temp.reset_index(drop=True, inplace=True)
            lr = pd.DataFrame()
            dataframe_temp['Mu_Temp_1'] = None
            for idx in range(1, len(dataframe_temp['Timestamp'])):

                if dataframe_temp.at[idx, 'Temperature'] is not None and \
                        dataframe_temp.at[idx, 'Mu'] is not None and dataframe_temp.at[idx, 'Mu'] is not np.nan:

                    if slider1[0] < dataframe_temp.at[idx, 'Temperature'] < slider1[1] and \
                            10 < dataframe_temp.at[idx, 'Pressure'] and dataframe_temp.at[idx, 'Mu'] > 0:
                        dataframe_temp.at[idx, 'Mu_Temp_1'] = dataframe_temp.at[idx, 'Mu']
                        lr.at[idx, 'Mu'] = dataframe_temp.at[idx, 'Mu']
                        lr.at[idx, 'Pressure'] = dataframe_temp.at[idx, 'Pressure']

            lr['Mu'], lr['X'] = polynomical_regression(lr, 'Pressure')

            act = [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80]
            figure_actual['data'][act[i]]['y'] = np.array(dataframe_temp['Mu_Temp_1'])
            figure_actual['data'][act[i] + 1]['x'] = np.array(lr['X'])
            figure_actual['data'][act[i] + 1]['y'] = np.array(lr['Mu'])

        mu_temp_slider_ranges[0] = slider1
        figure_actual['layout']['annotations'][0]['text'] = str(slider1[0]) + "-" + str(slider1[1]) + " [ºC]"
        return figure_actual


# Update temp-mu graph slider2
@app.callback(
    dash.dependencies.Output('Mu-Temp', "figure"),
    dash.dependencies.Input("slider_temp_2", "value"),
    [dash.dependencies.State('Mu-Temp', "figure"),
     dash.dependencies.State("memory-dataframe", "data")], prevent_initial_call=True)
def update_graph_temp_slider2(slider2, figure_actual, df_id):
    global df
    if figure_actual is None:
        return fig_mu_temp
    else:
        for i in range(0, df_id):
            dataframe_temp = df.loc[df['df_id'] == i + 1]
            dataframe_temp.reset_index(drop=True, inplace=True)
            lr = pd.DataFrame()
            dataframe_temp['Mu_Temp_2'] = None
            for idx in range(1, len(dataframe_temp['Timestamp'])):

                if dataframe_temp.at[idx, 'Temperature'] is not None and \
                        dataframe_temp.at[idx, 'Mu'] is not None and dataframe_temp.at[idx, 'Mu'] is not np.nan:

                    if slider2[0] < dataframe_temp.at[idx, 'Temperature'] < slider2[1] and \
                            10 < dataframe_temp.at[idx, 'Pressure'] and dataframe_temp.at[idx, 'Mu'] > 0:
                        dataframe_temp.at[idx, 'Mu_Temp_2'] = dataframe_temp.at[idx, 'Mu']
                        lr.at[idx, 'Mu'] = dataframe_temp.at[idx, 'Mu']
                        lr.at[idx, 'Pressure'] = dataframe_temp.at[idx, 'Pressure']

            lr['Mu'], lr['X'] = polynomical_regression(lr, 'Pressure')

            act = [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80]
            figure_actual['data'][act[i] + 2]['y'] = np.array(dataframe_temp['Mu_Temp_2'])
            figure_actual['data'][act[i] + 3]['x'] = np.array(lr['X'])
            figure_actual['data'][act[i] + 3]['y'] = np.array(lr['Mu'])

        mu_temp_slider_ranges[1] = slider2
        figure_actual['layout']['annotations'][1]['text'] = str(slider2[0]) + "-" + str(slider2[1]) + " [ºC]"
        return figure_actual


# Update temp-mu graph slider3
@app.callback(
    dash.dependencies.Output('Mu-Temp', "figure"),
    dash.dependencies.Input("slider_temp_3", "value"),
    [dash.dependencies.State('Mu-Temp', "figure"),
     dash.dependencies.State("memory-dataframe", "data")], prevent_initial_call=True)
def update_graph_temp_slider3(slider3, figure_actual, df_id):
    global df
    if figure_actual is None:
        return fig_mu_temp
    else:
        for i in range(0, df_id):
            dataframe_temp = df.loc[df['df_id'] == i + 1]
            dataframe_temp.reset_index(drop=True, inplace=True)
            lr = pd.DataFrame()
            dataframe_temp['Mu_Temp_3'] = None
            for idx in range(1, len(dataframe_temp['Timestamp'])):

                if dataframe_temp.at[idx, 'Temperature'] is not None and \
                        dataframe_temp.at[idx, 'Mu'] is not None and dataframe_temp.at[idx, 'Mu'] is not np.nan:

                    if slider3[0] < dataframe_temp.at[idx, 'Temperature'] < slider3[1] and \
                            10 < dataframe_temp.at[idx, 'Pressure'] and dataframe_temp.at[idx, 'Mu'] > 0:
                        dataframe_temp.at[idx, 'Mu_Temp_3'] = dataframe_temp.at[idx, 'Mu']
                        lr.at[idx, 'Mu'] = dataframe_temp.at[idx, 'Mu']
                        lr.at[idx, 'Pressure'] = dataframe_temp.at[idx, 'Pressure']

            lr['Mu'], lr['X'] = polynomical_regression(lr, 'Pressure')

            act = [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80]
            figure_actual['data'][act[i] + 4]['y'] = np.array(dataframe_temp['Mu_Temp_3'])
            figure_actual['data'][act[i] + 5]['x'] = np.array(lr['X'])
            figure_actual['data'][act[i] + 5]['y'] = np.array(lr['Mu'])

        mu_temp_slider_ranges[2] = slider3
        figure_actual['layout']['annotations'][2]['text'] = str(slider3[0]) + "-" + str(slider3[1]) + " [ºC]"
        return figure_actual


# Update temp-mu graph slider4
@app.callback(
    dash.dependencies.Output('Mu-Temp', "figure"),
    dash.dependencies.Input("slider_temp_4", "value"),
    [dash.dependencies.State('Mu-Temp', "figure"),
     dash.dependencies.State("memory-dataframe", "data")], prevent_initial_call=True)
def update_graph_temp_slider4(slider4, figure_actual, df_id):
    global df
    if figure_actual is None:
        return fig_mu_temp
    else:
        for i in range(0, df_id):
            dataframe_temp = df.loc[df['df_id'] == i + 1]
            dataframe_temp.reset_index(drop=True, inplace=True)
            lr = pd.DataFrame()
            dataframe_temp['Mu_Temp_4'] = None
            for idx in range(1, len(dataframe_temp['Timestamp'])):

                if dataframe_temp.at[idx, 'Temperature'] is not None and \
                        dataframe_temp.at[idx, 'Mu'] is not None and dataframe_temp.at[idx, 'Mu'] is not np.nan:

                    if slider4[0] < dataframe_temp.at[idx, 'Temperature'] < slider4[1] and \
                            10 < dataframe_temp.at[idx, 'Pressure'] and dataframe_temp.at[idx, 'Mu'] > 0:
                        dataframe_temp.at[idx, 'Mu_Temp_4'] = dataframe_temp.at[idx, 'Mu']
                        lr.at[idx, 'Mu'] = dataframe_temp.at[idx, 'Mu']
                        lr.at[idx, 'Pressure'] = dataframe_temp.at[idx, 'Pressure']

            lr['Mu'], lr['X'] = polynomical_regression(lr, 'Pressure')

            act = [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80]
            figure_actual['data'][act[i] + 6]['y'] = np.array(dataframe_temp['Mu_Temp_4'])
            figure_actual['data'][act[i] + 7]['x'] = np.array(lr['X'])
            figure_actual['data'][act[i] + 7]['y'] = np.array(lr['Mu'])

        mu_temp_slider_ranges[3] = slider4
        figure_actual['layout']['annotations'][3]['text'] = str(slider4[0]) + "-" + str(slider4[1]) + " [ºC]"
        return figure_actual


# Download modal
@app.callback(
    [dash.dependencies.Output("modal", "is_open"),
     dash.dependencies.Output('path', "value"),
     dash.dependencies.Output("file_name", "value")],
    dash.dependencies.Input("download", "n_clicks"),
    [dash.dependencies.State("modal", "is_open")], prevent_initial_call=True)
def download_modal(n1, is_open):
    path = GetFolderPath()
    file_name = 'Results'
    if n1:
        return not is_open, path, file_name
    return is_open, "", ""


# Download button
@app.callback(
    dash.dependencies.Output("modal", "is_open"),
    [dash.dependencies.Input("btn_dwn", "n_clicks"),
     dash.dependencies.State('path', "value"),
     dash.dependencies.State("file_name", "value"),
     dash.dependencies.State("memory-dataframe", "data")], prevent_initial_call=True)
def download(download_btn, path, filename, df_id):
    results_filename = 'Results_temp.html'
    results_inf_filename = 'Results_inf_temp.html'
    _3d_filename = '3D_temp.html'
    mu_press_filename = 'mu_press_temp.html'
    mu_temp_filename = 'mu_temp_temp.html'
    brake_filename = 'brake_temp.html'
    complete_filename = filename + '.html'

    if download_btn is not None:
        fig1 = Results_Graph(df, df_id, list_of_files, results_range)
        fig1_1 = Mu_Results_Tab(df, df_id, list_of_files, results_range)
        fig2 = Graph_3d(df, df_id, list_of_files)
        fig3 = Mu_Press_Graph(df, df_id, list_of_files, mu_press_slider_ranges)
        fig4 = Mu_Temp_Graph(df, df_id, list_of_files, mu_temp_slider_ranges)
        fig5 = graph_X_Y(df, df_id, list_of_files)

        fig1.write_html(path + '/' + results_filename)
        fig1_1.write_html(path + '/' + results_inf_filename)
        fig2.write_html(path + '/' + _3d_filename)
        fig3.write_html(path + '/' + mu_press_filename)
        fig4.write_html(path + '/' + mu_temp_filename)
        fig5.write_html(path + '/' + brake_filename)

        with open(path + '/' + results_filename) as fp:
            file1 = fp.read()

        with open(path + '/' + results_inf_filename) as fp:
            file1_1 = fp.read()

        with open(path + '/' + _3d_filename) as fp:
            file2 = fp.read()

        with open(path + '/' + mu_press_filename) as fp:
            file3 = fp.read()

        with open(path + '/' + mu_temp_filename) as fp:
            file4 = fp.read()

        with open(path + '/' + brake_filename) as fp:
            file5 = fp.read()

        file_complete = file1 + file1_1 + file2 + file3 + file4 + file5

        with open(path + '/' + complete_filename, 'w') as fp:
            fp.write(file_complete)

        os.remove(path + '/' + results_filename)
        os.remove(path + '/' + results_inf_filename)
        os.remove(path + '/' + _3d_filename)
        os.remove(path + '/' + mu_press_filename)
        os.remove(path + '/' + mu_temp_filename)
        os.remove(path + '/' + brake_filename)

        return False


# =============================================================================
# FUNCTION MAIN
# =============================================================================


if __name__ == '__main__':
    app.run_server(debug=False, use_reloader=False)
