import pandas as pd
import numpy as np
import os
import refinitiv.dataplatform.eikon as ek
import refinitiv.data as rd
from dash import Dash, html, dcc, dash_table, Input, Output, State
from datetime import datetime, date, timedelta
import dash_bootstrap_components as dbc
import plotly.express as px
import warnings
warnings.filterwarnings("ignore")

#####################################################

ek.set_app_key(os.getenv('EIKON_API'))

# ----html starts----

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

percentage = dash_table.FormatTemplate.percentage(3)

controls = dbc.Card(
    [
        dcc.Input(id='asset-id', type='text', value="IVV",
                      style={'display': 'inline-block',
                             'border': '1px solid black'}),
        dbc.Row([
            dcc.DatePickerRange(
                id='my-date-picker-range',
                min_date_allowed=date(2015, 1, 1),
                max_date_allowed=datetime.now().strftime("%Y-%m-%d"),
                # initial_visible_month=date(2023, 1, 30),
                start_date=date(2023, 1, 30),
                end_date=date(2023, 2, 8)
            )
        ]),
        dbc.Row(html.Button('QUERY Refinitiv', id='run-query', n_clicks=0)),
        dbc.Row([
            html.H5('Asset:',
                    style={'display': 'inline-block', 'margin-right': 20}),
            dbc.Table(
                [
                    html.Thead(html.Tr([html.Th("α1"), html.Th("n1")])),
                    html.Tbody([
                        html.Tr([
                            html.Td(
                                dbc.Input(
                                    id='alpha1-id',
                                    type='number',
                                    value=-0.01,
                                    max=1,
                                    min=-1,
                                    step=0.01
                                )
                            ),
                            html.Td(
                                dcc.Input(
                                    id='day1-id',
                                    type='number',
                                    value=3,
                                    min=1,
                                    step=1
                                )
                            )
                        ])
                    ])
                ],
                bordered=True
            ),
            dbc.Table(
                [
                    html.Thead(html.Tr([html.Th("α2"), html.Th("n2")])),
                    html.Tbody([
                        html.Tr([
                            html.Td(
                                dbc.Input(
                                    id='alpha2-id',
                                    type='number',
                                    value=0.01,
                                    max=1,
                                    min=-1,
                                    step=0.01
                                )
                            ),
                            html.Td(
                                dcc.Input(
                                    id='day2-id',
                                    type='number',
                                    value=5,
                                    min=1,
                                    step=1
                                )
                            )
                        ])
                    ])
                ],
                bordered=True
            )
        ]),
        dbc.Row([
            dcc.Markdown('''Press to display the order info:'''),
            html.Button('Submit', id='update_parameter', n_clicks=0)
        ])
    ],
    body=True
)


app.layout = dbc.Container(
    [
        dbc.Row(
            dcc.Markdown('''Names: Bella Zhao - wz172, Betty Xu - bx34, Jeanette Jian - zj76''')
        ),
        dbc.Row(
            [
                dbc.Col(controls, md=4),
                dbc.Col(
                    # Put your reactive graph here as an image!
                    html.Img(src=app.get_asset_url('reactive_graph.png'),alt="reactive graph",width=720,height=450),
                    md = 8
                )
            ],
            align="center",
        ),
        html.H2('ivv_prc data'),
        dash_table.DataTable(
            id="ivv_prc_data",
            page_action='none',
            style_table={'height': '300px', 'overflowY': 'auto'}
            # ), style={'display': 'none'}
        ),
        html.H2('entry_orders'),
        dash_table.DataTable(
            id="entry_orders-tbl",
            page_action='none',
            style_table={'height': '300px', 'overflowY': 'auto'}
        ),
        html.H2('exit_orders'),
        dash_table.DataTable(
            id="exit_orders-tbl",
            page_action='none',
            style_table={'height': '300px', 'overflowY': 'auto'}
        ),
        html.H2('all_orders'),
        dash_table.DataTable(
            id="all_orders-tbl",
            page_action='none',
            style_table={'height': '300px', 'overflowY': 'auto'}
        ),
    ],
    fluid=True
)

# ----html ends----
# next_business_day = datetime.now().strftime("%Y-%m-%d")
# ivv_prc_data = pd.DataFrame()

# Parameters:
# alpha1 = -0.01
# day1 = 3
# alpha2 = 0.01
# day2 = 5
# asset = "IVV"

@app.callback(
    Output("ivv_prc_data", 'data'),
    Input("run-query", "n_clicks"),
    [State('asset-id', 'value'),
     State('my-date-picker-range', 'start_date'),
     State('my-date-picker-range', 'end_date')],
    prevent_initial_call=True
)
def update_parameters(n_clicks, asset, start_date, end_date):
    ivv_prc, ivv_prc_err = ek.get_data(
        instruments=[asset],
        fields=[
            'TR.OPENPRICE(Adjusted=0)',
            'TR.HIGHPRICE(Adjusted=0)',
            'TR.LOWPRICE(Adjusted=0)',
            'TR.CLOSEPRICE(Adjusted=0)',
            'TR.PriceCloseDate'
        ],
        parameters={
            'SDate': start_date,
            'EDate': end_date,
            'Frq': 'D'
        }
    )

    ivv_prc['Date'] = pd.to_datetime(ivv_prc['Date']).dt.date
    ivv_prc.drop(columns='Instrument', inplace=True)
    # print(ivv_prc.pivot_table(index='Date').to_dict('records'))
    # ivv_prc = ivv_prc.pivot_table(
    #         index='Date', columns='Instrument'
    #     ).to_dict('records')

    return ivv_prc.to_dict('records')


@app.callback(  # when history table changes, return table will change
    Output("entry_orders-tbl", "data"),
    Output("exit_orders-tbl", "data"),
    Output("all_orders-tbl", "data"),
    Input("update_parameter", "n_clicks"),
    [State("ivv_prc_data", 'data'), State('asset-id', 'value'), State('alpha1-id', 'value'),
     State('day1-id', 'value'), State('alpha2-id', 'value'), State('day2-id', 'value')],
    prevent_initial_call=True
)
def output_orders(n_clicks, ivv_prc, asset, alpha1, day1, alpha2, day2):
    # submitted entry orders
    ivv_prc_df = pd.DataFrame(ivv_prc)
    ivv_prc_df['Date'] = pd.to_datetime(ivv_prc_df['Date']).dt.date

    rd.open_session()
    next_business_day = rd.dates_and_calendars.add_periods(
        start_date=ivv_prc_df['Date'].iloc[-1].strftime("%Y-%m-%d"),
        period="1D",
        calendars=["USA"],
        date_moving_convention="NextBusinessDay",
    )
    rd.close_session()

    submitted_entry_orders = pd.DataFrame({
        "trade_id": range(1, ivv_prc_df.shape[0]),
        "date": list(pd.to_datetime(ivv_prc_df["Date"].iloc[1:]).dt.date),
        "asset": asset,
        "trip": 'ENTRY',
        "action": "BUY",
        "type": "LMT",
        "price": round(
            ivv_prc_df['Close Price'].iloc[:-1] * (1 + alpha1),
            2
        ),
        'status': 'SUBMITTED'
    })

    # get the cancelled and filled entry orders
    temp_entry_orders = submitted_entry_orders.copy()
    for i in range(0, len(temp_entry_orders)):

        for j in range(1, day1 + 1):
            if i + j > len(ivv_prc_df) - 1:
                break
            if temp_entry_orders["price"].iloc[i] >= ivv_prc_df["Low Price"].iloc[i + j]:
                temp_entry_orders["status"].iloc[i] = "FILLED"
                temp_entry_orders["date"].iloc[i] = ivv_prc_df["Date"].iloc[i + j]
                break
        if temp_entry_orders["status"].iloc[i] != "FILLED":
            if i + j > len(ivv_prc) - 1:
                continue
            temp_entry_orders["status"].iloc[i] = "CANCELLED"
            temp_entry_orders["date"].iloc[i] = ivv_prc_df["Date"].iloc[i + day1]
    # live entry orders
    live_index = temp_entry_orders.index[temp_entry_orders["status"] == "SUBMITTED"]
    for i in live_index:
        temp_entry_orders["status"].iloc[i] = "LIVE"
        temp_entry_orders["date"].iloc[i] = pd.to_datetime(next_business_day).date()
    latest_live_entry_orders = pd.DataFrame({
        "trade_id": ivv_prc_df.shape[0],
        "date": pd.to_datetime(next_business_day).date(),
        "asset": asset,
        "trip": 'ENTRY',
        "action": "BUY",
        "type": "LMT",
        "price": round(ivv_prc_df['Close Price'].iloc[-1] * (1 + alpha1), 2),
        'status': 'LIVE'
    },
        index=[0]
    )

    entry_orders = pd.concat(
        [
            submitted_entry_orders,
            temp_entry_orders,
            latest_live_entry_orders
        ]
    ).sort_values(["trade_id", 'date'])
    entry_orders.reset_index(drop=True, inplace=True)


    # if the limit order filled, immediately submit exit orders
    submitted_exit_orders = entry_orders[entry_orders["status"] == "FILLED"].copy()
    submitted_exit_orders['trip'] = "EXIT"
    submitted_exit_orders['action'] = 'SELL'
    submitted_exit_orders['price'] = round(
        (1 + alpha2) * submitted_exit_orders['price'],
        2
    )
    submitted_exit_orders['status'] = "SUBMITTED"

    # get the cancelled and filled exit orders
    temp_exit_orders = submitted_exit_orders.copy()
    for i in range(0, len(temp_exit_orders)):
        # get the index in original data for the current date
        ori_index = ivv_prc_df.index[ivv_prc_df["Date"] == temp_exit_orders["date"].iloc[i]][0]

        for j in range(0, day2):
            if ori_index + j > len(ivv_prc_df) - 1:
                break
            if j == 0:
                if temp_exit_orders["price"].iloc[i] <= ivv_prc_df["Close Price"].iloc[ori_index + j]:
                    temp_exit_orders["status"].iloc[i] = "FILLED"
                    temp_exit_orders["date"].iloc[i] = ivv_prc_df["Date"].iloc[ori_index + j]
                    break
            else:
                if temp_exit_orders["price"].iloc[i] <= ivv_prc_df["High Price"].iloc[ori_index + j]:
                    temp_exit_orders["status"].iloc[i] = "FILLED"
                    temp_exit_orders["date"].iloc[i] = ivv_prc_df["Date"].iloc[ori_index + j]
                    break
        if temp_exit_orders["status"].iloc[i] != "FILLED":
            if ori_index + j > len(ivv_prc_df) - 1:
                continue
            temp_exit_orders["status"].iloc[i] = "CANCELLED"
            temp_exit_orders["date"].iloc[i] = ivv_prc_df["Date"].iloc[ori_index + day2 - 1]
    temp_exit_orders.reset_index(drop=True, inplace=True)
    live_index = temp_exit_orders.index[temp_exit_orders["status"] == "SUBMITTED"]
    for i in live_index:
        temp_exit_orders["status"].iloc[i] = "LIVE"
        temp_exit_orders["date"].iloc[i] = pd.to_datetime(next_business_day).date()

    # for the cancelled exit order, immediately issue a market order to sell
    exit_orders = temp_exit_orders.copy()  # define a global exit_orders
    if any(temp_exit_orders['status'] == 'CANCELLED'):
        submitted_exit_market_orders = temp_exit_orders[temp_exit_orders["status"] == "CANCELLED"].copy()
        submitted_exit_market_orders['type'] = "MKT"
        submitted_exit_market_orders['status'] = "SUBMITTED"
        submitted_exit_market_orders.reset_index(drop=True, inplace=True)
        for i in range(len(submitted_exit_market_orders)):
            submitted_exit_market_orders["price"].iloc[i] = ivv_prc_df[
                ivv_prc_df["Date"] == submitted_exit_market_orders['date'][i]
                ].copy()['Close Price']
        # These market order fill on the same day, at closing price
        filled_exit_market_orders = submitted_exit_market_orders.copy()
        filled_exit_market_orders['status'] = "FILLED"
        exit_market_orders = pd.concat(
            [
                submitted_exit_market_orders,
                filled_exit_market_orders
            ]
        ).sort_values(["trade_id", 'date'])
        exit_orders = pd.concat(
            [
                submitted_exit_orders,
                temp_exit_orders,
                exit_market_orders
            ]
        ).sort_values(["trade_id", 'date'])
    else:
        exit_orders = pd.concat(
            [
                submitted_exit_orders,
                temp_exit_orders
            ]
        ).sort_values(["trade_id", 'date'])
    exit_orders.reset_index(drop=True, inplace=True)


    # join entry_order, exit_order, exit_market_order together
    all_orders = pd.concat(
        [
            entry_orders,
            exit_orders
        ]
    ).sort_values(["trade_id", 'date'])
    all_orders.reset_index(drop=True, inplace=True)


    return entry_orders.to_dict("records"), exit_orders.to_dict("records"), all_orders.to_dict("records")


if __name__ == '__main__':
    app.run_server(debug=True)
