"""
Name: Daniel Atie
CS230: Section 3
Data: Starbucks Locations Worldwide (filtered to USA)
URL: https://starbucks-final-gwtrrrqox9ish3zemmbcme.streamlit.app/
Description:
This program reads Starbucks store data and lets the user explore US
Starbucks locations through filters, charts, and a map. The user can
pick a state, set a minimum number of stores per city, and filter by
ownership type to see different views of the data.

References:
Streamlit docs: https://docs.streamlit.io
PyDeck docs: https://deckgl.readthedocs.io
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pydeck as pdk


# page setup (wide layout, coffee cup icon in the tab)
st.set_page_config(
    page_title="US Starbucks Explorer",
    page_icon="☕",
    layout="wide"
)


# read the file and only keep US stores
def load_data():
    df = pd.read_csv("starbucks.csv", encoding="latin-1")
    df = df[df["Country"] == "US"]
    # brand column is just "Starbucks" for every row so drop it
    df = df.drop(columns=["Brand"])                      #[COLUMNS]
    return df


# grab all the states and put them in alphabetical order
def get_states(df):
    states = df["State/Province"].unique()
    states = sorted(states)                              #[SORT]
    return states


# filter to just one state and also count how many there are
def stores_in_state(df, state):                          #[FUNCRETURN2]
    filtered = df[df["State/Province"] == state]        #[FILTER1]
    count = len(filtered)
    return filtered, count


# filter by state AND ownership type (two conditions)
def filter_state_and_type(df, state, ownership):
    filtered = df[
        (df["State/Province"] == state) &
        (df["Ownership Type"] == ownership)
    ]                                                    #[FILTER2]
    return filtered


# count stores per city, only keep ones above the minimum
def busy_cities(df, minimum=10):                         #[FUNC2P]
    counts = df["City"].value_counts()
    counts = counts[counts >= minimum]
    return counts


# find the city with the most stores
def top_city(df):
    counts = df["City"].value_counts()
    if len(counts) == 0:
        return None, 0
    biggest = counts.idxmax()                            #[MAXMIN]
    biggest_count = counts.max()
    return biggest, biggest_count


# make the map with green dots and hover tooltips
def make_map(stores):
    # pydeck is picky and needs lowercase column names
    map_data = stores.rename(
        columns={"Latitude": "latitude", "Longitude": "longitude"}
    )

    # center the map on the average of all the dots
    center_lat = map_data["latitude"].mean()
    center_lon = map_data["longitude"].mean()

    view = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=6
    )

    # the green dots layer
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position=["longitude", "latitude"],
        get_radius=400,
        get_color=[0, 98, 65],
        pickable=True
    )

    # the little box that pops up when you hover
    tooltip = {
        "html": "<b>{Store Name}</b><br/>{Street Address}<br/>{City}",
        "style": {"backgroundColor": "white", "color": "black"}
    }

    chart = pdk.Deck(
        map_style="light",
        initial_view_state=view,
        layers=[layer],
        tooltip=tooltip
    )
    return chart


def main():
    # title and intro
    st.title("☕ US Starbucks Explorer")
    st.write("Explore over 13,000 Starbucks locations across the US. "
             "Use the sidebar to pick a state, ownership type, and city size.")
    st.markdown("---")

    df = load_data()

    # sidebar with all the controls                       #[ST3]
    st.sidebar.title("☕ Controls")
    st.sidebar.write("Use these to change what you see")

    states = get_states(df)
    chosen_state = st.sidebar.selectbox(                 #[ST1]
        "Pick a state:", states
    )
    min_stores = st.sidebar.slider(                      #[ST2]
        "Minimum stores per city (for chart):",
        min_value=5, max_value=100, value=20
    )
    ownership = st.sidebar.radio(
        "Ownership type:",
        ["Company Owned", "Licensed"]
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("Data: Starbucks worldwide directory (US only)")

    # quick stats section
    st.header("📊 Quick Stats for " + chosen_state)

    filtered, count = stores_in_state(df, chosen_state)

    # call top_city twice (once for nation, once for state)
    national_city, national_count = top_city(df)         #[FUNCCALL2]
    biggest_city, biggest_count = top_city(filtered)

    # 4 number boxes in a row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Stores in " + chosen_state, count)
    if biggest_city is not None:
        col2.metric("Top City in " + chosen_state, biggest_city,
                    str(biggest_count) + " stores")
    else:
        col2.metric("Top City in " + chosen_state, "N/A")
    col3.metric("Total US Stores", len(df))
    col4.metric("Nationwide #1 City", national_city,
                str(national_count) + " stores")

    st.markdown("---")

    # summary dictionary part
    if biggest_city is not None:
        # making a little dictionary to show summary stuff   #[DICTMETHOD]
        summary = {}
        summary["State"] = chosen_state
        summary["Total Stores"] = count
        summary["Top City"] = biggest_city
        summary["Stores in Top City"] = biggest_count

        st.subheader("📋 Summary")
        # loop through and print each key/value           #[ITERLOOP]
        for key in summary.keys():
            st.write(key + ": " + str(summary[key]))

    st.markdown("---")

    # map and table side by side
    map_col, table_col = st.columns([2, 1])

    map_col.subheader("🗺️ Map of Starbucks in " + chosen_state)
    map_col.caption("Hover over a dot for the store name and address")
    if count > 0:
        chart = make_map(filtered)                       #[MAP]
        map_col.pydeck_chart(chart)
    else:
        map_col.write("No stores to map.")

    table_col.subheader("📍 Store List")
    table_col.caption("Showing all " + str(count) + " stores")
    table_col.dataframe(
        filtered[["Store Name", "City", "Street Address"]],
        height=500
    )

    st.markdown("---")

    # charts side by side
    bar_col, pie_col = st.columns(2)

    # bar chart on the left
    bar_col.subheader("🏙️ Cities With Most Starbucks")
    bar_col.caption("Cities with at least " + str(min_stores) + " stores (whole US)")
    counts = busy_cities(df, min_stores)
    if len(counts) == 0:
        bar_col.write("No cities meet that minimum. Try lowering the slider.")
    else:
        # bar chart                                      #[CHART1]
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(counts.index, counts.values, color="#006241")
        ax.set_xlabel("City")
        ax.set_ylabel("Number of Stores")
        ax.set_title("US Cities With the Most Starbucks")
        plt.xticks(rotation=75)
        bar_col.pyplot(fig)

    # pie chart on the right
    pie_col.subheader("🥧 Ownership Split")
    pie_col.caption("Company Owned vs Licensed in " + chosen_state)
    own_counts = filtered["Ownership Type"].value_counts()
    if len(own_counts) > 0:
        # pie chart                                      #[CHART2]
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        ax2.pie(
            own_counts.values,
            labels=own_counts.index,
            autopct="%1.1f%%",
            colors=["#006241", "#a8d5ba"],
            startangle=90
        )
        ax2.set_title("Ownership in " + chosen_state)
        pie_col.pyplot(fig2)

    st.markdown("---")

    # combined filter section
    st.subheader("🔍 " + ownership + " Stores in " + chosen_state)
    combined = filter_state_and_type(df, chosen_state, ownership)
    st.write("Found " + str(len(combined)) + " stores")
    st.dataframe(combined[["Store Name", "City", "Street Address"]])

    # footer
    st.markdown("---")
    st.caption("Made for CS 230 · Spring 2026")


main()
