from dash import Dash, html, dcc, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import datetime
import os
import ifcfg  # does not work on Windows
import gcs  # shared module from bird classifier project


#   html.Div(children=last_refresh(),
#            style={
#           'textAlign': 'center',
#           'color': colors['text']
#       }
#       ),


def last_refresh():
    return 'Page last updated: ' + str(datetime.datetime.now().strftime('%H:%M:%S'))


def load_message_stream():
    # https://storage.googleapis.com/tweeterssp-web-site-contents/2022-12-29-11-57-29227.jpg
    try:
        display_list = ['spotted', 'possible']
        df = GCS_STORAGE.get_df(DATES[0]+'webstream.csv')
        df = df.drop('Unnamed: 0', axis="columns")
        df = df.reset_index(drop=True)
        df = df.sort_values(by='Date Time', ascending=False)
        df = df[df['Event Num'] != 0]
        df = df[df['Message Type'].isin(display_list)]
    except FileNotFoundError:
        print('No web stream found, creating empty stream')
        df = pd.DataFrame({
            'Event Num': pd.Series(dtype='int'),
            'Message Type': pd.Series(dtype='str'),
            'Date Time': pd.Series(dtype='str'),
            'Message': pd.Series(dtype='str'),
            'Image Name': pd.Series(dtype='str')})
        pass
    return df


def load_bird_occurrences():
    cname_list = []
    try:
        df = GCS_STORAGE.get_df(DATES[0]+'web_occurrences.csv')
        df['Date Time'] = pd.to_datetime(df['Date Time'])
        df['Hour'] = pd.to_numeric(df['Date Time'].dt.strftime('%H')) + \
            pd.to_numeric(df['Date Time'].dt.strftime('%M')) / 60
        for sname in df['Species']:
            sname = sname[sname.find(' ') + 1:] if sname.find(' ') >= 0 else sname  # remove index number
            cname = sname[sname.find('(') + 1: sname.find(')')] if sname.find('(') >= 0 else sname  # common name
            cname_list.append(cname)
        df['Common Name'] = cname_list
    except FileNotFoundError:
        print('no web occurences found, loading empty occurences')
        df = pd.DataFrame({
            'Species': pd.Series(dtype='str'),
            'Date Time': pd.Series(dtype='str'),
            'Hour': pd.Series(dtype='int')})
        df['Common Name'] = cname_list  # null list
    return df


def load_chart():
    df = load_bird_occurrences()
    fig1 = px.histogram(df, x="Hour", color='Common Name', range_x=[4, 22], nbins=36, width=1000, height=300)
    fig1.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )
    return fig1


def find_last(file_name_list, search_str):
    last_name = ''
    for file_name in file_name_list:
        if file_name.find(search_str) != -1:
            last_name = file_name
            break
    return last_name


# ******************** start dash app *****************
URL_PREFIX = '//storage.googleapis.com/tweeterssp-web-site-contents/'
PORT = 0
app = Dash(__name__)
server = app.server  # get container reference

GCS_STORAGE = gcs.Storage()
CSV_LIST = GCS_STORAGE.get_csv_list()

# build list of dates with data
DATES = []
for csv_name in CSV_LIST:
    csv_date = csv_name[0:csv_name.find('web')]
    if csv_date not in DATES:
        DATES.append(csv_date)  # get dates with info
DATES.reverse()  # newest to oldest info

DF = load_bird_occurrences()  # test stream of bird occurrences for graph
DF_STREAM = load_message_stream()  # message stream from device
IMAGE_NAMES = GCS_STORAGE.get_img_list()
IMAGE_NAMES.reverse() # reverse
LAST_GIF_NAME = find_last(IMAGE_NAMES,'.gif')
# IMAGES = load_images()  # load list of images


# ************* Web Layout *********************
colors = {
    'background': '#111111',
    'text': '#FFFFFF'
}

app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    html.H1(children='Tweeters - Sun Prairie, WI USA', style={
            'textAlign': 'center',
            'color': colors['text']
            }),

    html.Div(children='''
       Select the time range to display.
   '''),
    html.Div([
        dcc.RangeSlider(min=5, max=22,
                        id='time_range_slider',
                        step=None,
                        marks={
                           5: '05 AM',
                           6: '06 AM',
                           7: '07 AM',
                           8: '08 AM',
                           9: '09 AM',
                           10: '10 AM',
                           11: '11 AM',
                           12: '12 PM',
                           13: '01 PM',
                           14: '02 PM',
                           15: '03 PM',
                           16: '04 PM',
                           17: '05 PM',
                           18: '06 PM',
                           19: '07 PM',
                           20: '08 PM',
                           21: '09 PM',
                           22: '10 PM'
                        },
                        value=[6, 20]), html.Div(id='output-container-range-slider')
    ]),
    html.Div(children='''
    Select species:
    '''),
    html.Div([
        dcc.Dropdown(DF['Common Name'].unique(), DF['Common Name'].at[0], id='dropdown'),
        html.Div(id='dd-output-container')
        ],
        style={'width': '240px'},
    ),
    # flex container
    html.Div([
        # image container
        html.Div([
            html.A([
                html.Img(src=URL_PREFIX+LAST_GIF_NAME, id='animated_gif',
                         style={'height': '320px', 'width': '240px'})
            ], href=URL_PREFIX+LAST_GIF_NAME, target="_blank"),
        ]),
        # graph container
        html.Div([
            dcc.Graph(id='example-graph', figure=load_chart(), config={'displayModeBar': False})
        ]),
    ], style={'display': 'flex'}),

    html.Br(),

    html.Div(children=[
        html.A([
            html.Img(src=URL_PREFIX+IMAGE_NAMES[0], style={'height': '213px', 'width': '160px'})
        ], href=URL_PREFIX+IMAGE_NAMES[0], target="_blank"),
        html.A([
            html.Img(src=URL_PREFIX+IMAGE_NAMES[1], style={'height': '213px', 'width': '160px'},)
        ], href=URL_PREFIX+IMAGE_NAMES[1], target="_blank"),
        html.A([
            html.Img(src=URL_PREFIX+IMAGE_NAMES[2], style={'height': '213px', 'width': '160px'},)
        ], href=URL_PREFIX+IMAGE_NAMES[2], target="_blank"),
        html.A([
            html.Img(src=URL_PREFIX+IMAGE_NAMES[3], style={'height': '213px', 'width': '160px'},)
        ], href=URL_PREFIX+IMAGE_NAMES[3], target="_blank"),
        html.A([
            html.Img(src=URL_PREFIX+IMAGE_NAMES[4], style={'height': '213px', 'width': '160px'},)
        ], href=URL_PREFIX+IMAGE_NAMES[4], target="_blank"),
        html.A([
            html.Img(src=URL_PREFIX + IMAGE_NAMES[5], style={'height': '213px', 'width': '160px'}, )
        ], href=URL_PREFIX + IMAGE_NAMES[5], target="_blank"),
    ]
    ),

    dash_table.DataTable(
        data=DF_STREAM.to_dict('records'),
        # columns=[{'name': i, 'id': i} for i in df_stream.columns],
        columns=[
                {"id": "Event Num", "name": "Event Num"},
                {"id": "Date Time", "name": "Date Time"},
                {"id": "Message Type", "name": "Message Type"},
                {"id": "Message", "name": "Message"},
                {"id": "Image Name", "name": "Image Name", "presentation": "markdown"},
            ],
        markdown_options={"html": True},
        style_header={
            'backgroundColor': 'white',
            'color': 'black',
            'fontWeight': 'bold'
        },
        style_data={
            'color': colors['text'],
            'backgroundColor': colors['background']
        },
        style_cell_conditional=[
            {'if': {'column_id': 'Event Num'},
             'width': '5px'},
            {'if': {'column_id': 'Date Time'},
             'width': '15px'},
            {'if': {'column_id': 'Message Type'},
             'textAlign': 'left',
             'width': '15px'},
            {'if': {'column_id': 'Message'},
             'textAlign': 'left',
             'width': '80px'},
            {'if': {'column_id': 'Image Name'},
             'width': '30px', "presentation": "markdown"},
        ],
        style_as_list_view=True,
        id='web_stream',
        filter_action="native",
        sort_action="native",
        # sort_mode="multi",
        page_action="native",
        page_current=0,
        page_size=10,
            ),

    dcc.Interval(id='interval', interval=300000, n_intervals=0)  # update every 300 seconds
    ])


@app.callback(
    Output('output-container-range-slider', 'children'),
    [Input('time_range_slider', 'value')])
def update_output_slider(value):
    return 'You have selected "{}"'.format(value)


@app.callback(
    Output('dd-output-container', 'children'),
    Input('dropdown', 'value')
)
def update_output_dropdown(value):
    return f'You have selected {value}'


@app.callback(Output('web_stream', 'data'),
              [Input('interval', 'n_intervals')])
def update_rows(n_intervals):
    data = load_message_stream()
    msg_dict = data.to_dict('records')
    return msg_dict


@app.callback(Output('web_stream', 'columns'),
              [Input('interval', 'n_intervals')])
def update_cols(n_intervals):
    data = load_message_stream()
    columns = [{'id': i, 'name': i} for i in data.columns]
    return columns


@app.callback(Output('example-graph', 'figure'),
              [Input('interval', 'n_intervals')])
def update_chart(n_intervals):
    return load_chart()


if __name__ == "__main__":
    # grab interface with an ip address and print the ip
    print(ifcfg.interfaces().items())
    for name, interface in ifcfg.interfaces().items():
        if str(interface['device']) == 'wlan0' and str(interface['inet']) != 'None':
            print(interface['device'])
            print(interface['inet'])
            URL_PREFIX = str(interface['inet'])

    PORT = 8080
    # app.run_server(debug=True, host=URL_PREFIX, port=PORT)
    app.run_server(debug=True, port=PORT)
