import requests
import pandas as pd
from dash import Dash, html, dcc, Input, Output, dash_table
from dash.dependencies import Input, Output, State, ALL

def fetch_data():
    # Fetch the data
    API_URL = "https://groww.in/v1/api/search/v1/derived/scheme?available_for_investment=true&doc_type=scheme&max_aum=&page=0&plan_type=Direct&q=&size=1500&sort_by=1"
    response = requests.get(API_URL)
    return response.json()["content"]

# Convert to DataFrame
data = fetch_data()
df = pd.DataFrame(data)

# Prepare unique filters
categories = sorted(df["category"].dropna().unique())
subcategories_by_category = {
    cat: sorted(df[df["category"] == cat]["sub_category"].dropna().unique())
    for cat in categories
}

# Prepare hyperlink column
df["Fund Name"] = df.apply(
    lambda row: f"[{row['scheme_name']}](https://groww.in/mutual-funds/{row['id']})", axis=1
)

# Select columns to display
display_df = df[["Fund Name", "fund_manager", "category", "sub_category", "return1y", "return3y", "return5y", "aum", "risk", "groww_rating"]].copy()
display_df.columns = ["Fund Name", "Fund Manager", "Category", "Sub Category", "1Y Return", "3Y Return", "5Y Return", "AUM", "Risk", "Rating"]

# App Setup
app = Dash(__name__)
app.title = "Mutual Fund Explorer"

app.layout = html.Div([
    html.Div([
        html.H2("Filters", style={"margin-top": "0", "fontFamily": "Segoe UI, sans-serif"}),

        html.H3("Category", style={
            "padding": "10px 0",
            "borderBottom": "2px solid #ccc",
            "fontFamily": "Segoe UI, sans-serif",
            "fontSize": "18px"
        }),

        html.Div([
            dcc.Checklist(
                id="category-filter",
                options=[{"label": cat, "value": cat} for cat in categories],
                value=[],
                labelStyle={"display": "block", "margin": "4px 0", "fontWeight": "500"},
                inputStyle={"margin-right": "10px"}
            ),
        ]),

        html.Div(id="subcategory-filters")
    ], style={
        "width": "12%",
        "float": "left",
        "padding": "20px",
        "backgroundColor": "#f9f9f9",
        "height": "100vh",
        "overflowY": "auto",
        "borderRight": "1px solid #ccc",
        "fontFamily": "Segoe UI, sans-serif",
        "fontSize": "14px",
    }),

    html.Div([
        html.H1("Mutual Fund Explorer", style={"fontFamily": "Segoe UI, sans-serif"}),

        dash_table.DataTable(
            id="fund-table",
            columns=[
                {"name": col, "id": col, "presentation": "markdown"}
                if col == "Fund Name" else {"name": col, "id": col}
                for col in display_df.columns
            ],
            data=display_df.to_dict("records"),
            sort_action="native",
            filter_action="native",
            page_action="none",
            style_table={"overflowX": "auto"},
            style_cell={
                "textAlign": "left",
                "padding": "8px",
                "whiteSpace": "normal",
                "height": "auto",
                "fontFamily": "Segoe UI, sans-serif"
            },
            style_header={"backgroundColor": "#e1e1e1", "fontWeight": "bold"},
        )
    ], style={"margin-left": "14%", "padding": "20px"})
])


@app.callback(
    Output("subcategory-filters", "children"),
    Input("category-filter", "value")
)
def update_subcategories(selected_categories):
    sub_filters = []
    for cat in selected_categories:
        subs = subcategories_by_category.get(cat, [])
        if not subs:
            continue
        sub_filters.append(html.Div(f"Subcategories under {cat}", style={
                "marginTop": "20px",
                "marginBottom": "8px",
                "fontWeight": "600",
                "fontSize": "15px",
                "color": "#333",
                "fontFamily": "Segoe UI, sans-serif"
            })
        )
        sub_filters.append(
            dcc.Checklist(
                id={"type": "subcategory-filter", "index": cat},
                options=[{"label": sub, "value": sub} for sub in subs],
                value=[],
                labelStyle={"display": "block"},
                inputStyle={"margin-right": "10px","margin-top": "5px"}
            )
        )
    return sub_filters

@app.callback(
    Output("fund-table", "data"),
    Input("category-filter", "value"),
    Input({"type": "subcategory-filter", "index": ALL}, "value")
)
def filter_table(selected_categories, selected_subcategory_lists):
    filtered = display_df.copy()

    if selected_categories:
        filtered = filtered[filtered["Category"].isin(selected_categories)]

        # Flatten selected subcategories
        selected_subs = [sub for subs in selected_subcategory_lists for sub in subs if sub]
        if selected_subs:
            filtered = filtered[filtered["Sub Category"].isin(selected_subs)]

    return filtered.to_dict("records")


if __name__ == "__main__":
    app.run(debug=True)
