#!/usr/bin/env python
# coding: utf-8

# # VirtuOffice Analytics - A `dash` app
# By [Tom Keith](https://github.com/tomkeith) and [Angel Phanthanourak](https://github.com/angelphanth)

# Import the usual libraries 
import datetime as dt
import numpy as np
import pandas as pd

# Making the plots 
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# Importing dash libraries 
import dash
from dash.dependencies import Input, Output, State#, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

# Reading in the csv 
survey = pd.read_csv('survey_data.csv')

# Changing 'date' column to date object
survey['date'] = [dt.datetime.strptime(x, '%Y-%m-%d').date() for x in survey['date']]

# A list of the columns to change scale 
ratings = list(survey.columns[-8:])

# Iterate through each column
for question in ratings: 
    survey[question] = survey[question] / 5 * 100

# Changing employee_id to object type
survey['employee_id'] = survey['employee_id'].astype('str')

# Average as mode for every week (all teams/entire company) 
modes_by_date = survey.groupby(['date']).agg(lambda x:x.value_counts().index[0]).reset_index()


# Adding a column of hover_texts

# Empty list
hover_text = []

# Iterating through every row of the df 'modes_by_date'
for index, row in modes_by_date.iterrows():
    hover_text.append(('Week of {date}<br>'+
                       'Days WFH: {homedays}<br>'+
                       'Productivity: {product}%<br>'+
                       'Team Connection: {connect}%<br>'+
                       'Loneliness: {lonely}%<br>').format(date=row['date'], homedays=row['home_days'],
                                                           product=row['productivity'], connect=row['connections'],
                                                           lonely=row['lonliness']))

# Saving as new column 'text'
modes_by_date['text'] = hover_text


# Creating a dictionary of dataframes for each team

# List of teams
team_names = survey['team'].unique()

# Creating the dataframes 
team_data = {team : survey.query("team == '%s'" %team).groupby(['date']).agg(lambda x:x.value_counts().index[0]).reset_index()
                 for team in team_names}

for team in team_names:
    
    # Empty list
    hover_text = []
    
    # Iterating through every row of the df 
    for index, row in team_data[team].iterrows():
        hover_text.append(('Week of {date}<br>'+
                           'Days WFH: {homedays}<br>'+
                           'Productivity: {product}%<br>'+
                           'Team Connection: {connect}%<br>'+
                           'Loneliness: {lonely}%<br>').format(date=row['date'], homedays=row['home_days'],
                                                               product=row['productivity'],
                                                               connect=row['connections'],
                                                               lonely=row['lonliness']))
    # Saving as new column 'text'
    team_data[team]['text'] = hover_text


# Getting a list of dropdown options 
features = list(team_names)

# Adding option for entire company
features.append('All')

# Dropdown options
opts = [{'label': i, 'value': i} for i in features]

# Range slider options saved to 'dates'
dates = list(modes_by_date['date'][::3])



# Initialize the app
app = dash.Dash(external_stylesheets=['https://stackpath.bootstrapcdn.com/bootswatch/4.4.1/materia/bootstrap.min.css'])

# Creating a subplot
fig = make_subplots(2, 1, shared_xaxes=True, vertical_spacing=0.08)

# To scale marker sizes by days WFH
sizeref = 2.*modes_by_date['home_days'].max()/(10**2)

# The traces
trace_1 = go.Scatter(x=modes_by_date['date'], y=modes_by_date['productivity'], mode='lines+markers', 
                     text=modes_by_date['text'], line=dict(width=3,color='#2d5986'), 
                     marker=dict(size=10, line=dict(color='#ffffff', width=1)),
                     name='<b>Company</b> Productivity')

trace_2 = go.Scatter(x=modes_by_date['date'], y=modes_by_date['lonliness'], mode='lines+markers', 
                     text=[str(x)+' WFH days' for x in modes_by_date['home_days']],
                     marker=dict(size=modes_by_date['home_days'],
                                 sizeref=sizeref, color='#00b3b3'), name='Loneliness')

trace_3 = go.Bar(x=modes_by_date['date'], y=modes_by_date['connections'], opacity=0.8, 
                 name='Team Connection', marker=dict(color='#9fbfdf', line=dict(color='#ffffff', width=1)))

# Adding traces to subplot
fig.append_trace(trace_1, 2, 1)
fig.append_trace(trace_3, 2, 1)
fig.append_trace(trace_2, 1, 1)

# Update subplot layout
fig.update_layout(legend_orientation='h', legend=dict(x=0, y=1.1), hovermode='closest', autosize=True, 
                  yaxis=dict(range=[0, 100], side="right", type="linear", zeroline=False),
                  yaxis2=dict(range=[0, 100], side="right", type="linear", zeroline=False), 
                  width=1200, height=600, font=dict(size=16))

# Creating sunburst plots for employee satisfaction

# List of most frequent scores 
sun_vals = [modes_by_date['office_env'].value_counts().index[0], 
            modes_by_date['home_env'].value_counts().index[0], 
            modes_by_date['relationships'].value_counts().index[0], 
            modes_by_date['role'].value_counts().index[0]]

# List of colours
sun_color = ['#000000', '#99ccff', '#ace600', '#ffe6ff', '#cc99ff']

# Creating dictionaries of data for sunbursts
sun_data = [dict(character = [sun_vals[i], ' '], parent = ['', sun_vals[i]], value = [100, sun_vals[i]]) 
                              for i in range(0,4)]

# Creating the sunburst plots 
sun0, sun1, sun2, sun3 = [px.sunburst(sun_data[i], names='character', parents='parent', values='value', 
                                      branchvalues='total', color='character', 
                                      color_discrete_map={sun_data[i]['character'][0]:sun_color[0], 
                                                          sun_data[i]['character'][1]:sun_color[i+1]}) 
                          for i in range(0,4)]

# Saving plots to a list 
sun_charts = [sun0, sun1, sun2, sun3]

# Updating the layouts of the plots 
for i in range(0,4):
    sun_charts[i].update_traces(textfont_size=50, textfont_color=sun_color[i+1])
    sun_charts[i].update_layout(height=200, margin=dict(l=20, r=20, t=20, b=20))

    
# Create the dash layout
app.layout = html.Div([
                # Header
                html.Div([
                    html.H1("VirtuOffice Analytics", style={'fontSize':'50px','color':'#ffffff'}),
                    html.P("BrainStation x Microsoft Hackathon", style={'color':'#ffffff'})
                         ], style = {'padding' : '50px', 'backgroundColor' : '#264d73'}),
                # Satisfaction charts title
                html.Div([
                    html.H2("Employee Satisfaction with the following:")], style = {'padding' : '20px'}),
                # Sunbursts
                dbc.Row(
                    [dbc.Col(html.Div([
                        html.H5('Office Culture', style={'textAlign':'center'}),
                        dcc.Graph(id='g1', figure=sun0, config={'displayModeBar': False})
                    ]), width={'size':3}),

                     dbc.Col(html.Div([
                        html.H5('WFH Environment', style={'textAlign':'center'}),
                        dcc.Graph(id='g2', figure=sun1, config={'displayModeBar': False})
                    ]), width={'size':3}),

                     dbc.Col(html.Div([
                        html.H5('Working Relationships', style={'textAlign':'center'}),
                        dcc.Graph(id='g3', figure=sun2, config={'displayModeBar': False})
                    ]), width={'size':3}),

                    dbc.Col(html.Div([
                        html.H5('Work Roles', style={'textAlign':'center'}),
                        dcc.Graph(id='g4', figure=sun3, config={'displayModeBar': False})
                    ]), width={'size':3})]),
                # xy subplot
                dbc.Row(
                    [dbc.Col(html.Div([
                        html.H2('Lonliness and Days WFH, Productivity and Team Connection over Time'),
                        html.P("Interact with all charts by selecting a team and/or a date range of interest below."),
                        dcc.Graph(id='plot',figure=fig, config={'displayModeBar': False}), 
            
                        # Dropdown menu
                        html.P([
                            html.Label("Choose a Team", style={'fontSize':'20px'}),
                            dcc.Dropdown(id = 'opt', options = opts, value = features[-1])
                                ], style = {'width': '400px', 'fontSize' : '14px',
                                            'padding-left' : '100px', 'display': 'inline-block'}),

                        # Range slider
                        html.P([
                            html.Label("Time Period", style={'fontSize':'20px'}),
                            dcc.RangeSlider(id = 'slider',
                                            marks = {i : {'label':dates[i], 
                                                          'style':{'fontSize':'9px', 
                                                                   'color':'#b3b3b3',
                                                                   'transform':'rotate(45deg)'}} 
                                                     for i in range(0, 18)},
                                            min = 0,
                                            max = 17,
                                            value = [1, 16])
                                ], style = {'width' : '80%',
                                            'padding-left' : '100px',
                                            'display': 'inline-block'})], 
                        style = {'padding-left':'50px'}), width={'size':12})])])        


# Multi-Output Callback functions
@app.callback([Output('plot', 'figure'), Output('g1', 'figure'), 
               Output('g2', 'figure'), Output('g3', 'figure'), Output('g4', 'figure')],
              [Input('opt', 'value'), Input('slider', 'value')])
   
def update_figure(input1, input2):
    
    # When a team is selected from the dropdown 
    if input1 != 'All':
        
        # Filter the selected team's df
        st2 = team_data[input1][(team_data[input1]['date'] > dates[input2[0]]) & (team_data[input1]['date'] < dates[input2[1]])]
        
        # Filter the entire company's df
        st1 = modes_by_date[(modes_by_date['date'] > dates[input2[0]]) & (modes_by_date['date'] < dates[input2[1]])]
        
        # Updating the traces of the subplot 
        trace_1 = go.Scatter(x=st2['date'], y=st2['productivity'], mode='lines+markers', 
                             text=st2['text'], line=dict(width=3,color='#2d5986'), 
                             marker=dict(size=10, line=dict(color='#ffffff', width=1)),
                             name='<b>Team</b> Productivity')

        trace_2 = go.Scatter(x=st2['date'], y=st2['lonliness'], mode='lines+markers', 
                             text=[str(x)+' WFH days' for x in st2['home_days']],
                             marker=dict(size=modes_by_date['home_days'],
                                         sizeref=sizeref, color='#00b3b3'), name='Loneliness')

        trace_3 = go.Bar(x=st2['date'], y=st2['connections'], opacity=0.8, 
                         name='Team Connection', marker=dict(color='#9fbfdf', line=dict(color='#ffffff', width=1)))
        
        # Compile the subplots
        fig = make_subplots(2, 1, shared_xaxes=True, vertical_spacing=0.08)
        fig.append_trace(trace_1, 2, 1)
        fig.append_trace(trace_3, 2, 1)
        fig.append_trace(trace_2, 1, 1)
        fig.update_layout(legend_orientation='h', legend=dict(x=0, y=1.1), hovermode='closest', autosize=True, 
                          yaxis=dict(range=[0, 100], side="right", type="linear", zeroline=False),
                          yaxis2=dict(range=[0, 100], side="right", type="linear", zeroline=False), 
                          width=1200, height=600, font=dict(size=16))
    
        # Updating the sunbursts 
        sun_vals2 = [st2['office_env'].value_counts().index[0], 
                     st2['home_env'].value_counts().index[0], 
                     st2['relationships'].value_counts().index[0], 
                     st2['role'].value_counts().index[0]]
        
        # Creating dictionaries of data for sunbursts
        sun_data2 = [dict(character = [sun_vals2[i], ' '], parent = ['', sun_vals2[i]], value = [100, sun_vals2[i]]) 
                     for i in range(0,4)]
        # Updated plots
        sun0, sun1, sun2, sun3 = [px.sunburst(sun_data2[i], names='character', parents='parent', values='value', 
                                              branchvalues='total', color='character', 
                                              color_discrete_map={sun_data2[i]['character'][0]:sun_color[0], 
                                                                  sun_data2[i]['character'][1]:sun_color[i+1]}) 
                                  for i in range(0,4)]
        
        # Saving plots to a list 
        sun_charts2 = [sun0, sun1, sun2, sun3]

        # Updating the layouts of the plots 
        for i in range(0,4):
            sun_charts2[i].update_traces(textfont_size=50, textfont_color=sun_color[i+1])
            sun_charts2[i].update_layout(height=200, margin=dict(l=20, r=20, t=20, b=20))
    
    # If 'All' selected from dropdown
    else:
        
        # Filter the selected team's df
        st2 = modes_by_date[(modes_by_date['date'] > dates[input2[0]]) & (modes_by_date['date'] < dates[input2[1]])]
        
        # Updating dates of original traces
        trace_1 = go.Scatter(x=st2['date'], y=st2['productivity'], mode='lines+markers', 
                             text=st2['text'], line=dict(width=3,color='#2d5986'), 
                             marker=dict(size=10, line=dict(color='#ffffff', width=1)),
                             name='<b>Company</b> Productivity')

        trace_2 = go.Scatter(x=st2['date'], y=st2['lonliness'], mode='lines+markers', 
                             text=[str(x)+' WFH days' for x in st2['home_days']],
                             marker=dict(size=modes_by_date['home_days'],
                                         sizeref=sizeref, color='#00b3b3'), name='Loneliness')

        trace_3 = go.Bar(x=st2['date'], y=st2['connections'], opacity=0.8, 
                         name='Team Connection', marker=dict(color='#9fbfdf', line=dict(color='#ffffff', width=1)))

        # Compiling the new subplots
        fig = make_subplots(2, 1, shared_xaxes=True, vertical_spacing=0.08)
        fig.append_trace(trace_1, 2, 1)
        fig.append_trace(trace_3, 2, 1)
        fig.append_trace(trace_2, 1, 1)
        fig.update_layout(legend_orientation='h', legend=dict(x=0, y=1.1), hovermode='closest', autosize=True, 
                          yaxis=dict(range=[0, 100], side="right", type="linear", zeroline=False),
                          yaxis2=dict(range=[0, 100], side="right", type="linear", zeroline=False), 
                          width=1200, height=600, font=dict(size=16))

        # Updating sunbursts 
        sun_vals2 = [st2['office_env'].value_counts().index[0], 
                     st2['home_env'].value_counts().index[0], 
                     st2['relationships'].value_counts().index[0], 
                     st2['role'].value_counts().index[0]]
        
        # Creating dictionaries of data for sunbursts
        sun_data2 = [dict(character = [sun_vals2[i], ' '], parent = ['', sun_vals2[i]], value = [100, sun_vals2[i]]) 
                     for i in range(0,4)]
        
        # Update plots
        sun0, sun1, sun2, sun3 = [px.sunburst(sun_data2[i], names='character', parents='parent', values='value', 
                                              branchvalues='total', color='character', 
                                              color_discrete_map={sun_data2[i]['character'][0]:sun_color[0], 
                                                                  sun_data2[i]['character'][1]:sun_color[i+1]}) 
                                  for i in range(0,4)]
        
        # Saving plots to a list 
        sun_charts2 = [sun0, sun1, sun2, sun3]

        # Updating the layouts of the plots 
        for i in range(0,4):
            sun_charts2[i].update_traces(textfont_size=50, textfont_color=sun_color[i+1])
            sun_charts2[i].update_layout(height=200, margin=dict(l=20, r=20, t=20, b=20))

    return fig, sun0, sun1, sun2, sun3

  
# Server clause
if __name__ == '__main__':
    app.run_server(debug = True)

