# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import math
import os
import base64
import datetime

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

###################################
# Private function
###################################


def load_data(file_name, column_name):
    data = (
        pd.read_csv(base_URL + file_name)
        .melt(
            id_vars=["Province/State", "Country/Region", "Lat", "Long"],
            var_name="date",
            value_name=column_name,
        )
        .astype({"date": "datetime64[ns]", column_name: int}, errors="ignore")
    )
    data["Province/State"].fillna("<all>", inplace=True)
    data[column_name].fillna(0, inplace=True)
    return data


def create_card(title, content, change, currently, color):
    card = dbc.Card(
        dbc.CardBody(
            [
                html.H6(title, className="card-subtitle"),
                html.H4(content, className="card-subtitle"),
                html.P(change, className="card-subtitle"),
                html.P(currently, className="card-subtitle"),
            ],
            className="text-center",
        ),
        style={"color": color},
    )
    return card


def sum_data(data_frame, date, days_offset, column):
    sum = data_frame.loc[
        data_frame["date"] == date + pd.DateOffset(days_offset), column
    ].sum()
    return sum


################################################################################
# Data processing
################################################################################

# Data and files working with
base_URL = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/"
confirmed_cases = "time_series_covid19_confirmed_global.csv"
confirmed_deaths = "time_series_covid19_deaths_global.csv"
confirmed_recovered = "time_series_covid19_recovered_global.csv"

# Merge data frames into one
all_data = (
    load_data(confirmed_cases, "confirmed")
    .merge(load_data(confirmed_deaths, "deaths"))
    .merge(load_data(confirmed_recovered, "recovered"))
)

countries = all_data["Country/Region"].unique()
countries.sort()

# Save numbers into variables
latest_date = all_data["date"].max()

# number of cases
confirmed_cases_sum = sum_data(all_data, latest_date, 0, "confirmed")
cases_day_before = sum_data(all_data, latest_date, -1, "confirmed")
cases_difference = confirmed_cases_sum - cases_day_before
cases_operand = "+" if cases_difference > 0 else "-"
cases_percent_change = round((cases_difference / cases_day_before) * 100, 2)

# number of deaths
confirmed_deaths_sum = sum_data(all_data, latest_date, 0, "deaths")
deaths_day_before = sum_data(all_data, latest_date, -1, "deaths")
deaths_difference = confirmed_deaths_sum - deaths_day_before
deaths_operand = "+" if deaths_difference > 0 else "-"
deaths_percent_change = round((deaths_difference / deaths_day_before) * 100, 2)


# number of recovered cases
confirmed_recovered_sum = sum_data(all_data, latest_date, 0, "recovered")
recovered_day_before = sum_data(all_data, latest_date, -1, "recovered")
recovered_difference = confirmed_recovered_sum - recovered_day_before
recovered_operand = "+" if recovered_difference > 0 else "-"
recovered_percent_change = round((recovered_difference / recovered_day_before) * 100, 2)


# number of active cases
confirmed_active_cases = (
    confirmed_cases_sum - confirmed_deaths_sum - confirmed_recovered_sum
)

# other key numbers
outbreak_beginning = datetime.date(2019, 12, 31)
days_since_outbreak = (datetime.date.today() - outbreak_beginning).days
incident_fatality_rate = round((confirmed_deaths_sum / confirmed_cases_sum) * 100, 2)
recovery_rate = round((confirmed_recovered_sum / confirmed_cases_sum) * 100, 2)

# infected countries
infected_countries = len(all_data["Country/Region"].unique())

#############################################################################################
# Start to make plots
#############################################################################################

# Cards plot
card_days = create_card(
    "Days since outbreak",
    days_since_outbreak,
    f"Countries infected: {infected_countries}/195",
    f"Last updated: {latest_date:%d-%m-%Y}",
    "blue",
)
card_cases = create_card(
    "Total Confirmed",
    f"{confirmed_cases_sum:,}",
    f"New: {cases_operand}{cases_difference} / {cases_percent_change}%",
    [
        html.Span("Active Cases: ", style={"font-weight": "bold"}),
        html.Span(f"{confirmed_active_cases:,}"),
    ],
    "red",
)
card_deaths = create_card(
    "Total Deaths",
    f"{confirmed_deaths_sum:,}",
    f"New: {deaths_operand}{deaths_difference} / {deaths_percent_change}%",
    f"IFR: {incident_fatality_rate}%",
    "gray",
)
card_recovered = create_card(
    "Total Recovered",
    f"{confirmed_recovered_sum:,}",
    f"New: {recovered_operand}{recovered_difference} / {recovered_percent_change}%",
    f"RR: {recovery_rate}%",
    "green",
)
cards = dbc.CardDeck(
    [card_days, card_cases, card_deaths, card_recovered], className="mb-2"
)

# cases over time figure
time_series_grouped = all_data.groupby(["date"]).sum().reset_index()
time_series_controls = html.Div(
    [
        # dcc.Dropdown(
        #     id="yaxis-column",
        #     options=[{"label": i, "value": i} for i in countries],
        #     value="",
        #     multi=True,
        #     placeholder="Select a country",
        # ),
        dbc.RadioItems(
            id="yaxis-type",
            options=[{"label": i, "value": i} for i in ["Linear", "Log"]],
            value="Linear",
            inline=True,
        )
    ],
    style={"width": "100%", "display": "inline-block"},
)

# Map figure
map_all_data = (
    all_data[all_data["date"] == latest_date]
    .groupby(["Country/Region", "Lat", "Long"])
    .sum()
    .reset_index()
)

map_tabs = dcc.Tabs(
    id="map-tabs",
    value="confirmed",
    children=[
        dcc.Tab(label="Confirmed", value="confirmed"),
        dcc.Tab(label="Deaths", value="deaths"),
        dcc.Tab(label="Recovered", value="recovered"),
    ],
)

# Data table
table_all_data = (
    all_data[all_data["date"] == latest_date]
    .groupby(["Country/Region", "Province/State", "Lat", "Long"])
    .sum()
    .reset_index()
    .rename(
        columns={"confirmed": "Confirmed", "deaths": "Deaths", "recovered": "Recovered"}
    )
    .sort_values(by=["Confirmed"], ascending=False)
    .reset_index(drop=True)
)

data_table = html.Div(
    [
        dash_table.DataTable(
            id="datatable-interactivity",
            columns=[
                {"name": i, "id": i, "deletable": False, "selectable": True}
                for i in table_all_data.columns
                if i != "Long"
                if i != "Lat"
                if i != "Province/State"
            ],
            data=table_all_data.to_dict("records"),
            filter_action="native",
            sort_action="native",
            row_selectable="multi",
            fixed_rows={"headers": True, "data": 0},
            style_as_list_view=True,
            style_cell={"font_family": "Helvetica Neue"},
            style_table={
                "maxHeight": "800px",
                "height": "800px",
                "overflowY": "scroll",
            },
            style_header={
                "backgroundColor": "#f4f4f2",
                "fontWeight": "bold",
                "padding": "0.4rem",
            },
            virtualization=True,
            page_action="none",
            style_cell_conditional=[
                {"if": {"column_id": "Country/Region"}, "width": "23%"},
                {"if": {"column_id": "Confirmed"}, "width": "23%"},
                {"if": {"column_id": "Recovered"}, "width": "23%"},
                {"if": {"column_id": "Deaths"}, "width": "23%"},
                {"if": {"column_id": "Confirmed"}, "color": "#d7191c"},
                {"if": {"column_id": "Recovered"}, "color": "#1a9622"},
                {"if": {"column_id": "Deaths"}, "color": "#6c6c6c"},
                {"textAlign": "center"},
            ],
        )
    ],
    className="container mb-2",
)

##################################################################################################
# Start dash app
##################################################################################################

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Covid-19 tracker"
server = app.server

app.index_string = """<!DOCTYPE html>
<html>
    <head>
        <script data-name="BMC-Widget" src="https://cdnjs.buymeacoffee.com/1.0.0/widget.prod.min.js" data-id="borisgarcevic" data-description="Please support the app server for running" data-message="Support the app server for running!" data-color="#5F7FFF" data-position="right" data-x_margin="18" data-y_margin="18"></script>
        <!-- Global site tag (gtag.js) - Google Analytics -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=UA-154901818-2"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'UA-154901818-2');
        </script>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""

modal = html.Div(
    [
        dbc.Button("Info", id="open", className="btn-info mt-1 mb-1"),
        dbc.Modal(
            [
                dbc.ModalHeader("Welcome to my project"),
                dbc.ModalBody(
                    [
                        html.P(
                            f"On Dec 31, 2019, the World Health Organization (WHO) was informed of \
                    an outbreak of “pneumonia of unknown cause” detected in Wuhan City, Hubei Province, China – the \
                    seventh-largest city in China with 11 million residents. As of {latest_date:%d-%m-%Y}, \
                    there are over {confirmed_cases_sum:,} cases of COVID-19 confirmed globally.\
                    This dash board is developed to visualise and track the recent reported \
                    cases."
                        ),
                        html.P(
                            f"I have developed many dashboards in Power BI and Excel. \
                            having a lot of free time during the Corona crisis I decided \
                            to learn dashboard development in Plotly Dash. This is my work \
                            in progress so far."
                        ),
                        html.B(html.P("Data sources and inspiration: ")),
                        html.P(
                            [
                                "CSSE at Johns Hopkins University: ",
                                html.A(
                                    "For providing the data repository",
                                    href="https://github.com/CSSEGISandData/COVID-19",
                                ),
                            ]
                        ),
                        html.P(
                            [
                                "Jun: ",
                                html.A(
                                    "Coronavirus (COVID-19) Outbreak Global Cases Monitor",
                                    href="https://dash-coronavirus-2020.herokuapp.com/",
                                ),
                            ]
                        ),
                        html.P(
                            [
                                html.A(
                                    "COVID-19 Tracker",
                                    href="https://trackthevirus.info/",
                                )
                            ]
                        ),
                        html.P(
                            [
                                "Orhan Gazi Yalçın: ",
                                html.A(
                                    "How I Built a Dashboard with Dash and Plotly after being stuck in Europe’s Worst Coronavirus Outbreak",
                                    href="https://towardsdatascience.com/how-i-built-a-dashboard-with-dash-and-plotly-after-being-stuck-in-europes-worst-coronavirus-dc41aaeeca4b",
                                ),
                            ]
                        ),
                        html.P(
                            [
                                "Built using ",
                                html.A("Dash", href="https://dash.plotly.com/"),
                            ]
                        ),
                    ]
                ),
                dbc.ModalFooter(dbc.Button("Close", id="close", className="ml-auto")),
            ],
            id="modal",
        ),
    ]
)

navbar = dbc.NavbarSimple(
    children=[dbc.NavItem([modal])],
    brand="Coronavirus (COVID-19) Outbreak Global Cases Monitor",
    brand_href="#",
    color="dark",
    dark=True,
    fluid=True,
    className="mb-2",
)


# left column with information, tables and newsfeed
left_column = dbc.Col([html.Div([data_table])], md=4, width={"order": 1})

# right column with visuals
right_column = dbc.Col(
    html.Div(
        [
            html.Div([map_tabs, html.Div(id="map-figure")], className="mb-2 border"),
            html.Div(
                [time_series_controls, html.Div(id="time-series-cases")],
                className="border bg-white",
            ),
        ]
    ),
    md=8,
    width={"order": 2},
)


body_row = html.Div([dbc.Row([left_column, right_column])])

def serve_layout():
    return dbc.Container(
        [html.Div(navbar), html.Div([cards, body_row])],
        fluid=True,
        className="bg-light",
    )


app.layout = serve_layout

# Modal control
@app.callback(
    Output("modal", "is_open"),
    [Input("open", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


# Map Tabs control
@app.callback(Output("map-figure", "children"), [Input("map-tabs", "value")])
def map_figure(tab):
    if tab == "confirmed":
        color_discrete_sequence = "red"
        size = "confirmed"
        opacity = 0.5
    elif tab == "deaths":
        color_discrete_sequence = "gray"
        size = "deaths"
        opacity = 0.7
    elif tab == "recovered":
        color_discrete_sequence = "green"
        size = "recovered"
        opacity = 0.5

    map_figure = px.scatter_mapbox(
        map_all_data,
        lat="Lat",
        lon="Long",
        hover_name="Country/Region",
        hover_data=["confirmed", "deaths", "recovered"],
        color_discrete_sequence=[color_discrete_sequence],
        labels={
            "confirmed": "Confirmed",
            "deaths": "Deaths",
            "recovered": "Recovered",
            "Lat": "Latitude",
            "Long": "Longitude",
        },
        size=size,
        opacity=opacity,
        zoom=1.5,
        size_max=50,
        height=350,
    )
    map_figure.update_layout(mapbox_style="open-street-map")
    map_figure.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return html.Div([dcc.Graph(figure=map_figure)])


# Time series control
@app.callback(Output("time-series-cases", "children"), [Input("yaxis-type", "value")])
def time_series_control(radio_items_value):
    if radio_items_value == "Linear":
        log_y = False
    elif radio_items_value == "Log":
        log_y = True

    def time_series(y, label_name, log_y, title, color):
        time_series_figure = px.line(
            time_series_grouped,
            x="date",
            y=y,
            labels={"date": "Date", y: label_name},
            log_y=log_y,
            title=title,
            color_discrete_sequence=[color],
            render_mode="svg",
            height=350,
        )
        time_series_figure.update_layout(
            margin={"r": 0, "t": 40, "l": 0, "b": 0},
            xaxis_title="",
            yaxis_title="",
            hovermode="x",
        )

        return time_series_figure

    times_series_cases = time_series(
        "confirmed", "Confirmed", log_y, "Confirmed/Deaths/Recovered Timeline", "red"
    )
    times_series_cases.add_trace(
        time_series("deaths", "Deaths", log_y, "Confirmed Case Timeline", "gray").data[
            0
        ]
    )
    times_series_cases.add_trace(
        time_series(
            "recovered", "Recovered", log_y, "Confirmed Case Timeline", "green"
        ).data[0]
    )
    times_series_cases.update_traces(mode="lines+markers")

    return dcc.Graph(figure=times_series_cases)


if __name__ == "__main__":
    app.run_server(debug=True)
