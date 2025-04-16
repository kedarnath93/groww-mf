import streamlit as st
import pandas as pd
import requests
from st_aggrid import AgGrid, GridOptionsBuilder
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

API_URL = "https://groww.in/v1/api/search/v1/derived/scheme?available_for_investment=true&doc_type=scheme&max_aum=&page=0&plan_type=Direct&q=&size=1500&sort_by=1"

@st.cache_data(show_spinner=False)
def fetch_data():
    response = requests.get(API_URL)
    data = response.json()["content"]
    return pd.DataFrame(data)

st.title("📈 Mutual Funds Explorer (Groww)")

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()

df = fetch_data()

# Filters
with st.sidebar:
    st.header("🔍 Filters")
    categories = st.multiselect("Category", df["category"].dropna().unique(), default=df["category"].dropna().unique())
    subcategories = st.multiselect("Sub Category", df["sub_category"].dropna().unique(), default=df["sub_category"].dropna().unique())
    risks = st.multiselect("Risk", df["risk"].dropna().unique(), default=df["risk"].dropna().unique())

# Apply filters
filtered_df = df[
    df["category"].isin(categories) &
    df["sub_category"].isin(subcategories) &
    df["risk"].isin(risks)
]

# Create Groww link
filtered_df["groww_link"] = filtered_df["id"].apply(lambda x: f"https://groww.in/mutual-funds/{x}")

# Select columns to display
display_df = filtered_df[[
    "scheme_name", "fund_house", "sub_category", "category", "risk",
    "return1y", "return3y", "return5y", "aum", "min_investment_amount", "groww_link"
]]

# AgGrid Setup
gb = GridOptionsBuilder.from_dataframe(display_df)
gb.configure_pagination()
gb.configure_side_bar()
gb.configure_selection('single')  # only allow single row selection
grid_options = gb.build()

st.subheader(f"Showing {len(display_df)} funds")
grid_response = AgGrid(
    display_df,
    gridOptions=grid_options,
    height=600,
    enable_enterprise_modules=False,
    theme="streamlit",
    update_mode="SELECTION_CHANGED",
)

selected_row = grid_response['selected_rows']

# Redirect if a row is selected
if not pd.DataFrame(selected_row).empty:
    selected_fund = selected_row.iloc[0]
    link = selected_fund["groww_link"]
    st.success(f"Redirecting to: {link}")

    components.html(f"""
        <script>
            window.open("{link}", "_blank");
        </script>
    """, height=0)
