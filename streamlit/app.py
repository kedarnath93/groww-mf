#  pip install -r requirements.txt
#  streamlit run app.py

import streamlit as st
import pandas as pd
import requests
from collections import defaultdict
from functools import reduce
import operator

# ----------------- Page Config -----------------
st.set_page_config(page_title="Groww Mutual Fund Explorer", layout="wide")
st.title("📊 Groww Mutual Fund Explorer")

# ----------------- Fetch Data -----------------
@st.cache_data(ttl=3600)
def fetch_data():
    url = "https://groww.in/v1/api/search/v1/derived/scheme?available_for_investment=true&doc_type=scheme&max_aum=&page=0&plan_type=Direct&q=&size=1500&sort_by=1"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()["content"]

# Reload button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()

data = fetch_data()

# ----------------- Process Data -----------------
df = pd.DataFrame(data)

# Group subcategories under their main categories
category_map = defaultdict(set)
for fund in data:
    category = fund.get("category", "Unknown")
    sub_category = fund.get("sub_category", "Unknown")
    category_map[category].add(sub_category)

# ----------------- Sidebar Filters -----------------
st.sidebar.title("🔎 Filters")

selected_categories = []
selected_subcategories = defaultdict(list)

for main_cat in sorted(category_map.keys()):
    show_main = st.sidebar.checkbox(main_cat, key=main_cat)

    if show_main:
        selected_categories.append(main_cat)
        with st.sidebar.expander(f"{main_cat} Subcategories", expanded=True):
            for sub_cat in sorted(category_map[main_cat]):
                if st.checkbox(sub_cat, key=f"{main_cat}_{sub_cat}"):
                    selected_subcategories[main_cat].append(sub_cat)

# ----------------- Apply Filters -----------------
filtered_df = df.copy()

if selected_categories:
    filtered_df = filtered_df[filtered_df['category'].isin(selected_categories)]

    if any(selected_subcategories.values()):
        filter_conditions = []
        for main_cat, subcats in selected_subcategories.items():
            if subcats:
                filter_conditions.append(
                    (filtered_df['category'] == main_cat) & (filtered_df['sub_category'].isin(subcats))
                )
        if filter_conditions:
            filtered_df = filtered_df[reduce(operator.or_, filter_conditions)]

# ----------------- Display Table -----------------
st.subheader("📋 Mutual Fund List")

# Create a clickable name column
filtered_df['Fund'] = filtered_df.apply(
    lambda row: f'<a href="https://groww.in/mutual-funds/{row["id"]}" target="_blank">{row["scheme_name"]}</a>',
    axis=1
)

# Columns to show
columns_to_show = [
    "Fund", "fund_manager", "category", "sub_category",
    "risk", "groww_rating", "aum",
    "return1y", "return3y", "return5y",
    "min_investment_amount", "min_sip_investment"
]

# Rename for display
rename_columns = {
    "Fund": "Fund Name",
    "fund_manager": "Fund Manager(s)",
    "category": "Category",
    "sub_category": "Sub Category",
    "risk": "Risk Level",
    "groww_rating": "Groww Rating",
    "aum": "AUM (Cr)",
    "return1y": "1Y Return (%)",
    "return3y": "3Y Return (%)",
    "return5y": "5Y Return (%)",
    "min_investment_amount": "Min Lumpsum (₹)",
    "min_sip_investment": "Min SIP (₹)"
}

styled_df = filtered_df[columns_to_show].rename(columns=rename_columns)

# Display as interactive HTML table
st.write(
    styled_df.to_html(escape=False, index=False),
    unsafe_allow_html=True
)
