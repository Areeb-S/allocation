import pandas as pd
import numpy as np
from dash import (
    Dash,
    dcc,
    html,
    Input,
    Output,
    State,
    callback,
)
import dash_ag_grid as dag
from rand_desks import get_rotation

app = Dash()

app.layout = html.Div(
    [
        dcc.RadioItems(
            id="filter_dates",
            options=["Filter Dates", "Don't filter dates"],
            value="Filter Dates",
        ),
        html.Div("Number of weeks to generate:"),
        dcc.Input(
            id="num_weeks",
            type="number",
            placeholder="Number of weeks",
            value=10,
        ),
        html.Div("Always include every week:"),
        dcc.Input(
            id="always",
            type="text",
            placeholder="Always: name1, name2",
            debounce=True,
        ),
        html.Div(
            "Tethered. They will appear together or not at all:"
        ),
        dcc.Input(
            id="tethers",
            type="text",
            placeholder="tethers: tether1a, tether1b; tether2a, tether2b",
            debounce=True,
        ),
        dcc.Textarea(
            id="textarea-example",
            value="Textarea content initialized\nwith multiple lines of text",
            style={"width": "100%", "height": 300},
            persistence=True,
        ),
        dag.AgGrid(
            id="dataframe_web",
            rowData=[{"Empty": 0}],
            defaultColDef={"editable": True},
            columnDefs=[{"field": "Empty"}],
            columnSize="sizeToFit",
            dashGridOptions={"animateRows": False},
        ),
        html.Button(
            id="generate-button-state",
            n_clicks=0,
            children="Generate",
        ),
        dcc.Clipboard(
            id="table_copy",
            style={"fontSize": 20},
        ),
        dag.AgGrid(
            id="output_df",
            rowData=[{"Empty": 0}],
            defaultColDef={"editable": True},
            columnDefs=[{"field": "Empty"}],
            columnSize="sizeToFit",
            dashGridOptions={"animateRows": False},
        ),
    ]
)


@callback(
    Output("dataframe_web", "columnDefs"),
    Output("dataframe_web", "rowData"),
    Input("textarea-example", "value"),
)
def process_df(text):
    vals = [v.split("\t") for v in text.split("\n")]
    col_defs = [{"field": i} for i in vals[0]]
    df = pd.DataFrame(vals[1:], columns=vals[0])
    df["Date (Monday)"] = pd.to_datetime(
        df["Date (Monday)"],
        dayfirst=True,
    )
    return col_defs, df.to_dict("records")


@callback(
    Output("table_copy", "content"),
    Input("table_copy", "n_clicks"),
    State("output_df", "rowData"),
)
def custom_copy(_, data):
    dff = pd.DataFrame(data)
    # See options for .to_csv() or .to_excel() or .to_string() in the  pandas documentation
    return dff.to_csv(
        index=False, header=False, sep="\t"
    )  # includes headers


@callback(
    Output("output_df", "columnDefs"),
    Output("output_df", "rowData"),
    Input("generate-button-state", "n_clicks"),
    Input("num_weeks", "value"),
    Input("always", "value"),
    Input("tethers", "value"),
    Input("filter_dates", "value"),
    State("dataframe_web", "rowData"),
    State("dataframe_web", "columnDefs"),
)
def process_df(
    _, num_weeks, always, tethers, filter_dates, rows, cols
):

    input_df = pd.DataFrame(
        rows, columns=[c["field"] for c in cols]
    )
    if len(input_df) == 1:
        return rows, cols
    if always is not None and always != "":
        always = tuple(always.split(","))
    else:
        always = None
    if tethers is not None and tethers != "":
        tethers = tethers.replace(" ", "")
        tethers = tuple(
            tuple(t.split(",")) for t in tethers.split(";")
        )
    else:
        tethers = None

    output_df = get_rotation(
        input_df,
        always,
        tethers,
        num_weeks,
        filter_dates == "Filter Dates",
    )

    col_defs = [
        {"field": str(i)} for i in output_df.columns
    ]
    return col_defs, output_df.to_dict("records")


if __name__ == "__main__":
    app.run(debug=False)
