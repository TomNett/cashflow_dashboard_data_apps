#TODO: kolacovy bar na cerpanu 
#TODOL dalsi grafy a casove rady (kumulace)git s

# TODO Dispaly only campaigns, which are not selected
# TODO filter per client
# TODO client and budget ( editace)
# TODO filters depending on tabs of page
# TODO utracena % z kamp
# TODO tabulka budget kterou nalinkuju na kampani

#
# TODO scenare pro kampan  - pridat ?
# TODO Vypocet budgetu pro kampan - not needed
# TODO add columns in snowflake corresponding to client for a futher filtration

# mesice a vypotrebovany budget
# pak bude analyza konkrenti kampani

import streamlit as st
import warnings
from streamlit_option_menu import option_menu
import calendar
import pandas as pd
import numpy as np
import os
import datetime
import plotly.express as px
import time
from datetime import date
from datetime import timedelta
import plotly.graph_objects as go
from urllib.error import URLError
from plotly.subplots import make_subplots
# import arrow
import snowflake.connector
pd.options.mode.chained_assignment = None  # default='warn'
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)

from my_package.html import html_code, html_footer, title
from my_package.style import apply_css
from my_package.snowflake_related import insert_rows_to_snowflake, fetch_data_from_snowflake


# Layout settings ---------------
page_title = "Ad Expenses Tracker"
page_icon = ":bar_chart:"
layout = "wide"

#--------------------------------
st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)

# --- NAVIGATION MENU --- #
app_mode =option_menu(
    menu_title=None,
    options=['Expenses', 'Budgets', 'Analytics'],
    icons=["cash-coin","bar-chart-line", "wallet-fill"],
    orientation="horizontal"
)


def delete_row_from_df(df, index):
    if df.empty:
        return df.reset_index(drop=True)
    else:
        return df.drop(index, inplace=True).reset_index(drop=True)

# Functions get unique years form source data
def get_years(df):
    years = []
    df['start_date'] = pd.to_datetime(df['start_date'])
    return df["start_date"].dt.year.drop_duplicates()
# Functions creates list of months and years form source data


def create_month_year_list(m_ord, df):
    y_dist = get_years(df)
    month_year_list = []
    for y in y_dist:
        for m in m_ord:
            month_year_list.append(str(y) + '-' + str(m))
    return month_year_list


def custom_str_to_date(date_str, format_str='%d %B, %Y'):
    return datetime.datetime.strptime(date_str, format_str).date()


def first_day_month(selected_year_month):
    first_d = '1 ' + selected_year_month[5:] + ', 2023'
    first_date = custom_str_to_date(first_d)
    return first_date


def last_day_month(selected_year_month):
    day_count = calendar.monthrange(2023, datetime.datetime.strptime(
        selected_year_month[5:], '%B').month)[1]
    last_d = str(day_count) + ' ' + \
        selected_year_month[5:] + ', ' + selected_year_month[:4]
    last_date = custom_str_to_date(last_d)
    return last_date



# file_path = "/data/in/tables/input_table.csv"
file_path_local = "data/ads_insight_fact.csv"
df = pd.read_csv(file_path_local)
# CREATED_DATE	start_date	MODIFIED_DATE	END_DATE
df["created_date"] = pd.to_datetime(df["created_date"]).dt.date
df["start_date"] = pd.to_datetime(df["start_date"]).dt.date
df["modified_date"] = pd.to_datetime(df["modified_date"]).dt.date
df["end_date"] = pd.to_datetime(df["end_date"]).dt.date


df["impressions"] = pd.to_numeric(df["impressions"])
df["link_clicks"] = pd.to_numeric(df["link_clicks"])
df['start_date'] = pd.to_datetime(df['start_date'])
df['campaign_name'] = df.apply(
    lambda row: row['platform_id'][:9] + '-' + row['campaign_name'], axis=1)

# app_mode = st.sidebar.selectbox(
#     'Select Page', ['Expenses', 'Analytics', 'Campaigns'])  # two pages
distinct_campaigns = df['campaign_name'].unique()
distinct_source = df["platform_id"].unique()
# Get current month and year
current_month = datetime.datetime.now().month
current_year = datetime.datetime.now().year
current_day = datetime.datetime.now().day
current_date = pd.to_datetime(date.today().strftime('%Y-%m-%d'))
current_month_name = datetime.datetime.now().strftime("%B")
current_year_month = str(current_year) + '-' + current_month_name

months_order = ['January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December']

month_year_list = create_month_year_list(months_order, df)

dates = [datetime.datetime.strptime(date, '%Y-%B') for date in month_year_list]

# Separate the list by year
dates_2022 = sorted([date for date in dates if date.year == 2022])
dates_2023 = sorted([date for date in dates if date.year == 2023])

# Find the index of the current month and year in the 2023 list
current_index = dates_2023.index(datetime.datetime(2023, 8, 1))  # 2023-August

# Reorder the 2023 list
ordered_dates_2023 = dates_2023[:current_index +
                                1] + dates_2023[current_index + 1:]

# Concatenate the lists
ordered_dates = dates_2022 + ordered_dates_2023

# Convert back to the original string format
ordered_list_year_month = [date.strftime('%Y-%B') for date in ordered_dates]

# Define default filter values
default = {
    'since_date': datetime.date(current_year, 1, 1),
    'until_date': datetime.date(current_year, current_month, 1),
    'source': [],
    'campaign': []
}


if app_mode == 'Analytics':
    st.title('Analytical page')

    with st.container():
        st.text("Filter")
        # Extract unique values for campaigns and domains

        # Create two columns for filter controls
        col1, col2 = st.columns((1.5, 1.5))
        col11, col12 = st.columns((1.5, 1.5))

        # Create filter controls for date range in the first column
        with col1:
            since_date = st.date_input("Select a start date:",
                                       datetime.date(current_year, current_month-3, 1), key="since_date")

        # Create filter controls for source and campaign selection in the second column
        with col2:
            until_date = st.date_input("Select an end date:",
                                       datetime.date(current_year, current_month, current_day), key="until_date")

        with col11:
            selected_sources = st.multiselect('Select a source:',
                                              distinct_source, default=None, placeholder="All sources", key="source")

        with col12:
            selected_campaigns = st.multiselect('Select a campaign:',
                                                distinct_campaigns, default=None, placeholder="All campaigns", key="campaign")

        # Convert into same format to compare
        since_date = pd.Timestamp(st.session_state.since_date)
        until_date = pd.Timestamp(st.session_state.until_date)

        filtered_df = df[(df['start_date'] >= since_date) &
                         (df['start_date'] <= until_date)]

        if len(st.session_state.source) != 0:
            filtered_df = filtered_df[filtered_df['platform_id'].isin(
                st.session_state.source)]

        if len(st.session_state.campaign) != 0:
            filtered_df = filtered_df[filtered_df['campaign_name'].isin(
                st.session_state.campaign)]

        st.markdown(title["charts"], unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(
            ["Best performing Campaigns", "Visualizations per Campaigns", "Raw data"])
        grouped = filtered_df.groupby(['campaign_name', 'start_date']).agg(
            {'link_clicks': 'sum', 'impressions': 'sum'}).reset_index()
        grouped['ctr'] = (grouped['link_clicks'] /
                          grouped['impressions']) * 100
        Campaigns_df = grouped.copy()
        max_campaign = Campaigns_df["ctr"].max()

        with tab1:
            st.markdown(title["topcampains"], unsafe_allow_html=True)
            df_top_campaing = filtered_df.groupby(['platform_id', 'campaign_name', 'start_date']).agg(
                {'impressions': 'sum', 'link_clicks': 'sum', }).reset_index()
            st.write(df_top_campaing.head(5))
            col1, col2 = st.columns(2)
            ctr_mean = round(np.mean(filtered_df["ctr"]), 2)*100
            col1.metric("Average Clickthrough rate", str(ctr_mean) + ' %')
            target_value = col1.slider('Target Clickthrough Rate', 0, 100, 40)

            fig = px.bar(x=[ctr_mean],
                         y=['ctr'],
                         orientation='h',
                         labels={'x': '%', 'y': ''},
                         title='Average Clickthrough rate')
            fig.update_layout(xaxis=dict(range=[0, 100]), height=200)
            fig.update_traces(marker_color='rgb(255, 75, 75)')
            fig.add_annotation(x=ctr_mean * 100, y='ctr',
                               # format the number to 2 decimal places
                               text=f"{ctr_mean * 100:.2f}%",
                               showarrow=False,
                               yshift=20)
            fig.add_shape(type="line",
                          x0=target_value, y0=0, x1=target_value, y1=1,
                          line=dict(color='rgb(64, 224, 208)', width=6),
                          xref='x', yref='paper')
            col1.plotly_chart(fig, use_container_width=True)

            cpm_mean = round(np.mean(filtered_df["cpm"]), 2)
            max_cpm = np.max(filtered_df["cpm"])
            col2.metric("Cost per mille", str(cpm_mean) + ' EUR')
            cpm_mean = round(np.mean(filtered_df["cpm"]), 2)
            max_cpm_range = cpm_mean + 10
            fig = px.bar(x=[cpm_mean],
                         y=['cpm'],
                         orientation='h',
                         labels={'x': 'EUR', 'y': ''},
                         title='Average Clickthrough rate')
            fig.update_layout(xaxis=dict(range=[0, max_cpm_range]), height=200)
            fig.update_traces(marker_color='rgb(255, 75, 75)')
            fig.add_annotation(x=cpm_mean, y='cpm',
                               # format the number to 2 decimal places
                               text=f"{cpm_mean:.2f} EUR",
                               showarrow=False,
                               yshift=20)

            col2.plotly_chart(fig, use_container_width=True)

        with tab2:
            # # Display title for the "Campaigns" section
            st.markdown(title["impressions"], unsafe_allow_html=True)
            fig = px.bar(Campaigns_df, x="start_date",
                         y="impressions", color="campaign_name")
            # st.bar_chart(data = Campaigns_df, x="start_date", y="impressions",use_container_width=True)
            # fig = px.bar(Campaigns_df, x="start_date", y="impressions", color="campaign_name") # , color="source"
            fig.update_layout(xaxis_title='Date', yaxis_title='impressions')
            # # Display the bar chart
            st.plotly_chart(fig, use_container_width=True)

            # Clicks
            st.markdown(title["clicks"], unsafe_allow_html=True)
            fig = px.bar(Campaigns_df, x="start_date", y="link_clicks",
                         color="campaign_name")  # , color="source"
            fig.update_layout(
                xaxis_title='Date',
                yaxis_title='Clicks',
            )
            # Display the bar chart
            st.plotly_chart(fig, use_container_width=True)

            st.markdown(title["clicktr"], unsafe_allow_html=True)
            fig = px.line(Campaigns_df, x="start_date", y="ctr",
                          color="campaign_name")  # , color="source"

            # # Update layout
            fig.update_layout(
                xaxis_title='Date',
                yaxis_title='Click-Through Rate %',
            )
            fig.update_yaxes(range=[0, max_campaign+5])
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            st.markdown('Dataset :')
            st.write(df.head())


elif app_mode == 'Expenses':

    ##################
    # Filter section #
    ##################
    with st.container():
        st.title("Expenses overview")
        st.header("Filters: ")
        st.session_state.campaigns = distinct_campaigns
        with st.container():

            try:
                # Create two columns for filter controls
                col1, col2 = st.columns((1.5, 1.5))
                col11, col12 = st.columns((1.5, 1.5))

                # Create filter controls for date range in the first column
                with col1:
                    since_date = st.date_input("Select a start date:",
                                               datetime.date(current_year, current_month-3, 1), key="since_date")

                # Create filter controls for source and campaign selection in the second column
                with col2:
                    until_date = st.date_input("Select an end date:",
                                               datetime.date(current_year, current_month, current_day), key="until_date")
                since_date = pd.Timestamp(st.session_state.since_date)
                until_date = pd.Timestamp(st.session_state.until_date)
                filtered_df = df[(df['start_date'] >= since_date) & (
                    df['start_date'] <= until_date)]

                with col11:
                    selected_sources = st.multiselect('Select Platform',
                                                      distinct_source, default=distinct_source, placeholder="Select  platforms from the list", key="source")
                if not selected_sources:
                    col12.error("Please select a platform.")
                else:
                    if len(st.session_state.source) != 0:
                        filtered_df = filtered_df[filtered_df['platform_id'].isin(
                            st.session_state.source)]
                        distinct_campaigns_by_platform = filtered_df['campaign_name'].unique(
                        )
                        with col12:
                            selected_campaigns = st.multiselect('Select a campaign:',
                                                                distinct_campaigns_by_platform, default=None, placeholder="All campaigns", key="campaign")

                ###################
                # Metrics section #
                ###################

                # Columns and data creation

                df_current_month = df[(df['start_date'] >= (
                    current_date - timedelta(days=30))) & (df['start_date'] <= current_date)]
                df_last_month = df[(df['start_date'] >= (current_date - timedelta(days=60))) & (
                    df['start_date'] <= (current_date - timedelta(days=60)))]  # TODO change to current month
                df_filtered_months = df[(df['start_date'] >= (
                    current_date - timedelta(days=150))) & (df['start_date'] <= current_date)]
                df_filtered_months["month_column"] = df_filtered_months.start_date.dt.month
                df_filtered_months["month_name"] = df_filtered_months.start_date.dt.strftime(
                    "%B")
                spend_current_month = round(
                    np.sum(df_current_month["spent_amount"]), 2)

                current_month_name = datetime.datetime.now().strftime("%B")
                if len(st.session_state.source) != 0:
                    df_filtered_months = df_filtered_months[df_filtered_months['platform_id'].isin(
                        st.session_state.source)]

                if (len(st.session_state.campaign) != 0):
                    df_filtered_months = df_filtered_months[df_filtered_months['campaign_name'].isin(
                        st.session_state.campaign)]

            except URLError as e:
                st.error()
        # Columns for metrics
        st.divider()
        col1, col2 = st.columns(2)

        # Column 1

        # target_value = col1.number_input('Target Spend Amount')
        # TODO - devision by 0 , str(spend_current_month/spend_current_month)
        col1.metric("Spend this month", str(spend_current_month) + ' EUR')

        # Initialize the figure
        fig = go.Figure()
        try:
            month_spend = df_filtered_months.groupby(['month_name']).agg(
                {'spent_amount': 'sum'}).reset_index()
            month_spend['month_name'] = pd.Categorical(
                month_spend['month_name'], categories=months_order, ordered=True)

            # Sort the dataframe by 'month_name'
            month_spend = month_spend.sort_values(
                'month_name').reset_index(drop=True)
            if month_spend.empty:
                col1.error(
                    "Please check filters - Selected platform does not have selected campaigns")
            else:
                # Add the bars
                for index, row in month_spend.iterrows():
                    fig.add_trace(go.Bar(
                        x=[row['spent_amount']],
                        y=[row['month_name']],
                        orientation='h',
                        # this will be the individual value now
                        text=[row['spent_amount']],
                        textposition='outside',
                        marker_color=px.colors.qualitative.Plotly[index % len(
                            px.colors.qualitative.Plotly)]  # cycling through colors
                    ))

                fig.update_layout(title='Last five month spendings',
                                  xaxis=dict(range=[0, max(
                                      month_spend["spent_amount"])*1.15], title='Spend in EUR', showgrid=True),
                                  yaxis_title='Month',
                                  showlegend=False)

                # fig.add_shape(type="line",
                #             x0=target_value, y0=0, x1=target_value, y1=1,
                #             line=dict(color='rgb(64, 224, 208)', width=3),
                #             xref='x', yref='paper')

                col1.plotly_chart(fig, use_container_width=True)
        except URLError as e:
            st.error()

        # Column 2

        platform_id_spend = df_current_month.groupby(
            ['platform_id']).agg({'spent_amount': 'sum'}).reset_index()

        # target_value_platform_id = col2.number_input('Target Spend Amount For platform_id')
        col2.metric("Average Spend By platform_id", str(
            round(np.mean(platform_id_spend["spent_amount"]), 2)) + ' EUR')

        fig_spend = go.Figure()

        # Add the bars
        for index, row in platform_id_spend.iterrows():
            fig_spend.add_trace(go.Bar(
                x=[row['spent_amount']],
                y=[row['platform_id']],
                orientation='h',
                # this will be individual value now
                text=[row['spent_amount']],
                textposition='outside',
                marker_color=px.colors.qualitative.Plotly[index % len(
                    px.colors.qualitative.Plotly)]  # cycling through colors
            ))

        fig_spend.update_layout(title='Current month expanses by platform_id',
                                xaxis=dict(
                                    range=[0, spend_current_month*1.15], title='EUR'),
                                yaxis_title='',
                                showlegend=False)

        # fig_spend.add_shape(type="line",
        #                     x0=target_value_platform_id, y0=0, x1=target_value_platform_id, y1=1,
        #                     line=dict(color='rgb(64, 224, 208)', width=6),
        #                     xref='x', yref='paper')

        col2.plotly_chart(fig_spend, use_container_width=True)
        st.divider()
        ####################
        # Charts  sections #
        ####################
        tab1, tab2 = st.tabs(
            ["Expenses per platform_id", "Expenses per Campaign"])
        try:

            if len(st.session_state.source) != 0:
                filtered_df = filtered_df[filtered_df['platform_id'].isin(
                    st.session_state.source)]

            if len(st.session_state.campaign) != 0:
                filtered_df = filtered_df[filtered_df['campaign_name'].isin(
                    st.session_state.campaign)]
            if filtered_df.empty:
                st.error(
                    "Please check filters - Selected platform does not have selected campaigns")
            else:
                grouped = filtered_df.groupby(['campaign_name', 'start_date'])\
                    .agg({'spent_amount': 'sum'}).reset_index()
                Campaigns_df = grouped.copy()
                grouped = filtered_df.groupby(['platform_id', 'start_date'])\
                    .agg({'spent_amount': 'sum'}).reset_index()
                platform_id_df = grouped.copy()

                with tab1:
                    # , color="source"
                    fig = px.bar(platform_id_df, x="start_date",
                                 y="spent_amount", color="platform_id")

                    fig.update_layout(
                        xaxis_title='Date',
                        yaxis_title='Expenses',
                    )
                    st.plotly_chart(fig, use_container_width=True)
                with tab2:
                    # , color="source"
                    fig = px.bar(Campaigns_df, x="start_date",
                                 y="spent_amount", color="campaign_name")

                    fig.update_layout(
                        xaxis_title='Date',
                        yaxis_title='Expenses'

                    )
                    st.plotly_chart(fig, use_container_width=True)
        except URLError as e:
            st.error()


elif app_mode == 'Budgets':

    with st.container():
        col1, col2, col3 = st.columns(3, gap="small")
        with col2:
            st.title("Budget overview")
    apply_css()
    with st.expander("Show budget settings"):

        # df_current_month = df[(df['start_date'] >= (current_date - timedelta(days=30))) & (df['start_date'] <= current_date)]
        col1, col2 = st.columns(2, gap="small")
        col11, col12 = st.columns((1.5, 1.5))

        col1, col2, col3 = st.columns((2, 1, 1))
        col11.subheader('Budget editing :')

        df['month_name'] = pd.DatetimeIndex(df['start_date']).strftime("%B")
        current_month_name = datetime.datetime.now().strftime("%B")
        default_ix = months_order.index(current_month_name)

        #############################
        ######## Filters ############
        #############################
        currency_distinct = ["EUR", "CZK", "USD"]

        # Container for budget df
        # Define column names for the empty dataframe
        columns = ["Client", "Budget", "Budget amount",
                   "Currency", "Since date", "Until date", "Campaigns"]
        columns = np.array(columns, dtype=str)
        

        # Create an empty session state variable
        session_state = st.session_state
        # Check if the session state variable is already defined

        if "df" not in session_state:
            # Assign the initial data to the session state variable
            session_state.df = fetch_data_from_snowflake()
            session_state.row = pd.Series(index=columns)

        # Create a selectbox for each column in the current row
        for col in columns:
            # Get unique values from the corresponding column in the resource_data dataframe
            if col == "Client":
                session_state.row[col] = col11.text_input(
                    col, '', placeholder='Enter a client name', key=col)

            elif col == "Budget":
                session_state.row[col] = col11.text_input(
                    col, '', placeholder='Enter a budget name', key=col)

            elif col == "Budget amount":
                session_state.row[col] = col11.number_input(
                    col, value=1000)
            elif col == "Currency":
                session_state.row[col] = col11.selectbox(
                    col, currency_distinct, index=0, key='currency_budget')
            elif col == "Since date":
                session_state.row[col] = col11.date_input("Select a start date for budget:",
                                                          datetime.date(current_year, current_month-1, 1), key="since_date_budget")
            elif col == "Until date":
                session_state.row[col] = col11.date_input("Select a start date for budget:",
                                                          datetime.date(current_year, current_month, current_day), key="until_date_budget")
            elif col == "Campaigns":  # TODO controll, that cahrts don't show expenses for the ads before the period !
                try:

                    with col11:
                        selected_sources = st.multiselect('Select Platform:',
                                                          distinct_source, default=distinct_source, placeholder="All platform_ids", key="source")
                    if not selected_sources:
                        col11.error("Please select a platform.")
                        selected_year_month = col11.selectbox('Select Campaign Start Date (Year & Month)',
                                                              ordered_list_year_month, index=default_ix,  placeholder="All months", disabled=True, key="month_camp")
                        session_state.row[col] = col11.multiselect('Select a campaign:',
                                                                   distinct_campaigns, default=None, placeholder="All campaigns", disabled=True,  key="campaign")
                    else:

                        selected_year_month = col11.selectbox('Select Campaign Start Date (Year & Month)',
                                                              ordered_list_year_month, index=default_ix,  placeholder="All months", key="month_camp")
                        if len(st.session_state.month_camp) != 0:
                            filtered_df = df[(df['start_date'] >= pd.to_datetime(first_day_month(selected_year_month))) & (
                                df['start_date'] <= pd.to_datetime(last_day_month(selected_year_month)))]
                        if len(st.session_state.source) != 0:
                            filtered_df = filtered_df[filtered_df['platform_id'].isin(
                                st.session_state.source)]
                            distinct_campaigns_by_platform = filtered_df['campaign_name'].unique(
                            )
                        session_state.row[col] = col11.multiselect('Select a campaign:',
                                                                   distinct_campaigns_by_platform, default=None, placeholder="All campaigns", key="campaign")
                except URLError as e:
                    st.error()
                col1, col2 = st.columns(2)
                # Add a button to add a new empty row to the dataframe and clear the values of the selectboxes for the current row
                with col12:
                    st.subheader("Entered data preview  : ")
                    st.table(session_state.row)

                    col21, col22, col23, col24, col25 = st.columns(
                        (0.3, 0.3, 0.3, 0.3, 0.8), gap="small")
                    if col21.button("Add Row"):
                        session_state.df.loc[len(
                            session_state.df)] = session_state.row
                        session_state.row = pd.Series(index=columns)
                    if col22.button("Change Row", key='rowchange'):
                        # TODO
                        print('Hi')
                    if col23.button("Delete Row", key="deleterow"):
                        col11, col12 = st.columns(2)
                        col11.warning("🚨 Specify row you want to be deleted")
                        index_to_delete = col11.number_input(
                            'ID of row', value=0)

                        if "delete_pressed" not in session_state:
                            session_state.delete_pressed = False

                        if col11.button("Delete", key="deleter"):
                            session_state.delete_pressed = True

                        if session_state.delete_pressed:
                            session_state.df = delete_row_from_df(
                                session_state.df, index_to_delete)
                            session_state.delete_pressed = False
                    if col24.button("Clear DF"):
                        #session_state.df = empty_df
                        print("empty")
                st.header("Budgets and their limits")
                st.table(session_state.df)

        # st.dataframe(session_state.df)
        # st.data_editor(budget_df, num_rows="static")

    # filtered_df = df[(df['start_date'] >= since_date) & (df['start_date'] <= until_date)]

    df_last_month = df[(df['start_date'] >= (current_date - timedelta(days=60))) & (
        df['start_date'] <= (current_date - timedelta(days=60)))]  # TODO change to current month
    df_filtered_months = df[(df['start_date'] >= (
        current_date - timedelta(days=150))) & (df['start_date'] <= current_date)]
    df_filtered_months["month_column"] = df_filtered_months.start_date.dt.month
    df_filtered_months["month_name"] = df_filtered_months.start_date.dt.strftime(
        "%B")
    # spend_current_month = round(np.sum(filtered_df["spent_amount"]), 2)
    # spend_last_month = round(np.sum(df_last_month["spent_amount"]), 2)

    # Dummy df for representation
    data = {"Client": ["MOL"], "Budget": [1500,], "Campaign": [
        ["FACEBOOK-MOL - link clicks - FB+IG - MOL MOVE kampaň - 05-07/2023", "LINKEDIN-MOL - link clicks - LI - Provozovatelé - 2023"]]}
    df_dummy = pd.DataFrame(data)

    with st.container():
        st.markdown(
            """
                        <style>
                            div[data-testid="column"]:nth-of-type(1)
                            {

                            }

                            div[data-testid="column"]:nth-of-type(2)
                            {
                                margin: auto;
                                width: 50%;
                                text-align: center;
                            }
                        </style>
                        """, unsafe_allow_html=True
        )

        # Data from snowflake
        data_from_snowflake = fetch_data_from_snowflake()
        data_from_snowflake.columns = data_from_snowflake.columns.str.lower()
        data_from_snowflake.columns = data_from_snowflake.columns.str.title()
        data_from_snowflake['Since_Date'] = pd.to_datetime(data_from_snowflake['Since_Date'])
        data_from_snowflake['Until_Date'] = pd.to_datetime(data_from_snowflake['Until_Date'])
        client_list = data_from_snowflake["Client"].unique()
        default_ix_for_filter = months_order.index(min(data_from_snowflake['Since_Date']).strftime("%B"))
        
        ##
        
        # Tabs for visuals
        tab1, tab2, tab3 = st.tabs(
            ["Cleent overview", "Detailed Budget Examination", "Raw data"])
        with tab1:
            st.header("Filters: ")
            # Create two columns for filter controls
            #data_from_snowflake = data_from_snowflake[data_from_snowflake['Since_Date'] >= pd.to_datetime(first_day_month())]
            filtered_clients= data_from_snowflake
            with st.form("entry_form_budget_filter", clear_on_submit=False):
                col1f, col2f = st.columns((1.5, 3))
                col1f.selectbox('Select Year and Month:',
                                                  ordered_list_year_month, index=default_ix_for_filter,  placeholder="All months", key="monthfiltercharts")
                col2f.multiselect('Select a source:',
                                                    client_list, default=client_list, placeholder="Client", key="clientunique")
                
                submitted = st.form_submit_button("Filter data")
                if submitted:
                    data_from_snowflake = data_from_snowflake[data_from_snowflake['Since_Date'] >= pd.to_datetime(first_day_month(st.session_state["monthfiltercharts"]))]
                    filtered_clients= data_from_snowflake[data_from_snowflake['Client'].isin(st.session_state["clientunique"])]
                    

            col1, col2 = st.columns((2, 1), gap="large")


            # --- Data for a chart --- #

            ####
            budget_by_client = filtered_clients.groupby(['Client']).agg(
                        {'Budget_Amount': 'sum'}).reset_index().sort_values(by='Budget_Amount', ascending=False)
            filtered_df = df 
             #camp_df = filtered_df.loc[filtered_df["campaign_name"] in ]
            def camp_for_sorting(df):
                campaigns_for_sorting = []
                for campaigns_list in df['Campaings']:
                    for campaign in campaigns_list:
                        campaigns_for_sorting.append(campaign)
                campaigns_for_sorting = list(set(campaigns_for_sorting))
                return campaigns_for_sorting
            
            campaigns_for_sorting = camp_for_sorting(filtered_clients)
            
            filtered_df_2 = filtered_df[filtered_df['campaign_name'].isin(campaigns_for_sorting)]
            campaign_spend = filtered_df_2.groupby(['campaign_name']).agg(
                                {'spent_amount': 'sum'}).reset_index().sort_values(by='spent_amount', ascending=False)
            platform_campaign_spend = filtered_df_2.groupby(['platform_id','campaign_name']).agg(
                        {'spent_amount': 'sum'}).reset_index().sort_values(by='spent_amount', ascending=False)

            mapping = data_from_snowflake.explode('Campaings')[['Client', 'Campaings']].rename(columns={'Campaings': 'campaign_name'})
            merged = pd.merge(mapping, campaign_spend, on='campaign_name', how='left').fillna(0)
            total_spent_per_client = merged.groupby('Client')['spent_amount'].sum().reset_index()
            final_df = pd.merge(budget_by_client, total_spent_per_client, on='Client', how='left')
            final_df.rename(columns={'spent_amount': 'Total_Spent'}, inplace=True)
            final_df['Unspent'] = final_df['Budget_Amount'] - final_df['Total_Spent']
            final_df['Percentage_spend']  = round(final_df['Total_Spent']/ final_df['Budget_Amount']*100,2)
            final_df = final_df.rename(columns={"Budget_Amount": "Budget amount", "Total_Spent": "Total spend","Percentage_spend": "Percentage spend"}) 

            
            
            # --- Printing filtered data in second column --- #
            col2.markdown(title["inputdata"], unsafe_allow_html=True)
            col2.write(final_df)

            # --- Creating plot for client's budget --- #
            if final_df.empty:
                col1.warning(":face_with_monocle:" + " There is no data for this period")
                # Adding bars for Unspent
            else: 
                # Adding bars for Total Spent
                fig_spend = go.Figure()
                for index, row in final_df.iterrows():
                    fig_spend.add_trace(go.Bar(
                            x=[row['Total spend']],
                            y=[row['Client']],
                            name='Spent',
                            orientation='h',
                            text=f"{row['Percentage spend']:.2f} %",
                            textposition='auto',
                            textfont_color = 'white',
                            marker_color='#d33682'
                        ))
                for index, row in final_df.iterrows():
                        fig_spend.add_trace(go.Bar(
                            x=[row['Unspent']],
                            y=[row['Client']],
                            #name='Unspent',
                            orientation='h',
                            text=f"{row['Budget amount']} EUR",
                            textposition='outside',
                            marker_color=px.colors.qualitative.Plotly[2]  # Using a fixed color for Unspent
                        ))
                   # Update layout settings
                max_budget = final_df['Budget amount'].max()
                fig_spend.update_layout(title='Client Spent vs Budget',
                                            xaxis=dict(
                                                range=[0, max_budget * 1.10], title='EUR'),
                                            yaxis_title='',
                                            barmode='stack',
                                            showlegend=False)
                    #fig.for_each_trace(lambda t: t.update(textfont_color=t.marker.color, textposition='top center')) 
                col1.plotly_chart(fig_spend, use_container_width=True)
                
                #########################
                # ---  Sankey Chart --- # #TODO: controll if the value may-2023 and MOL-2 bug 
                #########################
                col11, col12 = st.columns((2, 1), gap="large")
                
                color_cycle = ['blue', 'red', 'green', 'yellow', 'purple', 'cyan']  # Define more colors if needed

                # Map clients to specific colors from the color_cycle
                client_colors = {client: color_cycle[i % len(color_cycle)] for i, client in enumerate(filtered_clients['Client'].unique())}

                # Get all platforms from the campaign names in filtered_df
                unique_platforms = list(filtered_df['campaign_name'].str.split('-').str[0].unique())

                labels = list(filtered_clients['Budget'].unique()) + list(filtered_clients['Client'].unique()) + unique_platforms

                # Budget to Client links are unchanged
                source = [labels.index(budget) for budget in filtered_clients['Budget']]
                target = [labels.index(client) for client in filtered_clients['Client']]
                value = filtered_clients['Budget_Amount'].tolist()

                colors = ['gray' for _ in filtered_clients['Budget']]

                # Client to Platform links
                for index, row in filtered_clients.iterrows():
                    platform_spends = {}  # To track spend for each platform within the loop
                    for campaign in row['Campaings']:
                        platform = campaign.split('-')[0]
                        
                        # Check if the campaign exists in campaign_spend
                        campaign_data = campaign_spend[campaign_spend['campaign_name'] == campaign]['spent_amount']
                        if not campaign_data.empty:
                            spend = campaign_data.iloc[0]
                        else:
                            spend = 0
                        
                        # Add or update the platform spend for this loop iteration
                        platform_spends[platform] = platform_spends.get(platform, 0) + spend

                    for platform, spend in platform_spends.items():
                        source.append(labels.index(row['Client']))
                        target.append(labels.index(platform))
                        value.append(spend)
                        colors.append(client_colors[row['Client']])

                # Build the Sankey chart
                fig = go.Figure(data=[go.Sankey(
                    node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=labels),
                    link=dict(source=source, target=target, value=value, color=colors)
                )])
                fig.update_layout(title="Flow of Funds: From Budgets to Platforms via Clients")
                fig.add_annotation(
                    text = "This diagram visualizes the flow of money from various budgets, through different clients, and finally to distinct advertising platforms.",                                        
                    showarrow=False,
                    yshift=-160,
                    font=dict(
                            family="sans serif",
                            size=18,
                            color="#F1F3F4"
                        )                     
                    )

                col11.plotly_chart(fig, use_container_width=True)   

                
                 

                st.divider()  

               
                
                
                
                # for budget in budgets:
                #     # Filter campaigns associated with the current budget
                #     related_campaigns = data_from_snowflake[data_from_snowflake['Budget'] == budget]['Campaings'].explode().unique()

                #     # Filter the daily_spend dataframe for those campaigns
                #     budget_daily_spend = daily_spend[daily_spend['campaign_name'].isin(related_campaigns)]

                #     # Plot the area chart for the current budget
                #     fig = px.area(budget_daily_spend, x='start_date', y='spent_amount', color='campaign_name', 
                #                 title=f"Daily Spend Over Time for Budget: {budget}", 
                #                 labels={'spent_amount': 'Amount Spent', 'start_date': 'Start Date'},
                #                 category_orders={'campaign_name': sorted(budget_daily_spend['campaign_name'].unique())})

                #     col12.plotly_chart(fig, use_container_width=True)

                
               

            # --- TAB 2 FOR BUDGETS --- #
            
            with tab2:
                 #################################
                 # --- Budget over time look --- #
                 #################################
                consolidated_daily_spend = pd.DataFrame()
                daily_spend = filtered_df.groupby(['start_date', 'campaign_name']).agg({'spent_amount': 'sum'}).reset_index()
                budgets = data_from_snowflake['Budget'].unique()
                full_date_range = pd.date_range(start=daily_spend['start_date'].min(), end=daily_spend['start_date'].max())
                consolidated_daily_spend = pd.DataFrame({'Date': full_date_range})
                # Create a complete date range from the earliest to the latest date in the dataset
                ind = 1
                fig = go.Figure()
                for budget in budgets:
                        related_campaigns = data_from_snowflake[data_from_snowflake['Budget'] == budget]['Campaings'].explode().unique()

                                    # Filter the daily_spend dataframe for those campaigns
                        budget_daily_spend = daily_spend[daily_spend['campaign_name'].isin(related_campaigns)].copy()
                                    
                        campaign_cumsums = []  # A list to hold the cumulative sums for each campaign
                                    
                        for campaign in related_campaigns:
                                campaign_data = budget_daily_spend[budget_daily_spend['campaign_name'] == campaign].set_index('start_date')
                                        
                                        # Fill missing dates with zeros for this campaign
                                campaign_data = campaign_data.reindex(full_date_range, fill_value=0).reset_index()
                                campaign_data['cumulative_spent'] = campaign_data['spent_amount'].cumsum()
                                        
                                campaign_cumsums.append(campaign_data['cumulative_spent'])

                                    # Sum the cumulative sums for each campaign to get the cumulative sum for the entire budget
                                
                        consolidated_daily_spend[budget] = sum(campaign_cumsums)

                        fig.add_trace(go.Scatter(x=consolidated_daily_spend["Date"], y=consolidated_daily_spend.iloc[:,ind],name=budget, fill = 'tozeroy'))
                        ind = ind + 1      
                                # Plot the stacked area chart
                fig.update_layout(title='Budget Spent In Time ',
                    height=500 ,   # Adjust the figure height; 600 is arbitrary, you can set this to whatever you like
                    yaxis=dict(
                    range=[0, consolidated_daily_spend.iloc[:, 1:].max().max() * 1.2], title='EUR'))
                st.plotly_chart(fig, use_container_width=True)     
                
                ##############################################            
                 # --- Pie charts for budget distributtion --- #
                 ##############################################

                budget_groups = data_from_snowflake.groupby('Budget')

                num_budgets = len(budget_groups)
                sqrt_budgets = int(np.sqrt(num_budgets))
                cols = sqrt_budgets if num_budgets == sqrt_budgets**2 else sqrt_budgets + 1
                rows = num_budgets // cols + (num_budgets % cols > 0)  # ceil operation

                subplot_titles = [name for name, _ in budget_groups]

                fig = make_subplots(rows=rows, cols=cols, subplot_titles=subplot_titles, specs=[[{'type':'domain'} for _ in range(cols)] for _ in range(rows)])

                for index, (budget_name, group) in enumerate(budget_groups):
                    platform_spendings = {}  # Dictionary to hold platform and their corresponding spending
                    
                    for _, row in group.iterrows():
                        for campaign in row['Campaings']:
                            filtered = campaign_spend[campaign_spend['campaign_name'] == campaign]['spent_amount']

                            if not filtered.empty:
                                spent = filtered.iloc[0]
                            else:
                                spent = None  # or some default value or handling you'd like                            
                            
                            if campaign in platform_spendings:
                                platform_spendings[campaign] += spent
                            else:
                                platform_spendings[campaign] = spent
                    
                    labels = list(platform_spendings.keys())
                    values = list(platform_spendings.values())
                    
                    row_position = index // cols + 1
                    col_position = index % cols + 1
                    fig.add_trace(
                        go.Pie(labels=labels, values=values, name=budget_name),
                        row=row_position, col=col_position
                    )

                # Adjusting the figure layout
                fig.update_layout(
                    title_text="Pie charts for each budget",
                    height=600 * rows,   # Adjust the figure height; 600 is arbitrary, you can set this to whatever you like
                    width=600 * cols,    # Adjust the figure width
                    margin=dict(t=50, l=50, r=50, b=50)   # Adjust the margins if needed
                )

                st.plotly_chart(fig, use_container_width=True)         
                
            ###########
            ###########
            ##########
            # with col1:
                
            #     # budget_by_clietn = df_from_snowflake.groupby(['Client']).agg(
            #     # {'spent_amount': 'sum', 'cpm': 'mean'}).reset_index().sort_values(by='spent_amount', ascending=True)
            #     # st.write(df_from_snowflake)

            #     # Sample dataframe
            #     data = {'Client': ['MOL', 'WMC'],
            #             'Budget': [1500, 1200],
            #             'Spend': [1300, 900]}
            #     df = pd.DataFrame(data)
            #     col1.subheader('Current budget situation by Client')
            #     for _, row in df.iterrows():
            #         spend_current_month = row['Spend']
            #         month_budget = row['Budget']

            #         fig = px.bar(x=[spend_current_month],
            #                      y=[row['Client']],
            #                      orientation='h',
            #                      labels={'x': 'EUR', 'y': ''})

            #         fig.update_layout(xaxis=dict(
            #             range=[0, month_budget]), height=200)
            #         fig.update_traces(marker_color='rgb(105, 205, 251)')

            #         percentage_spend = spend_current_month/month_budget*100

            #         fig.add_annotation(x=spend_current_month,
            #                            y=row['Client'],
            #                            text=f"{percentage_spend:.2f}%",
            #                            showarrow=False,
            #                            yshift=10, xshift=30)

            #         col1.plotly_chart(fig, use_container_width=True)

            # col22.metric("Advertising -  total budget Utilization",str(spend_current_month) + ' EUR')
            # month_budget = 1000 #TODO add input

            # fig = px.bar(x=[spend_current_month],
            #             y=[str(spend_current_month) + ' EUR'],
            #             orientation='h',
            #             labels={'x': 'EUR', 'y': ''})
            #             #title='Average Clickthrough rate')
            # fig.update_layout(xaxis=dict(range=[0, month_budget]),height=200)
            # fig.update_traces(marker_color='rgb(105, 205, 251)')

            # fig.add_annotation(x=spend_current_month, y='EUR',
            #                 text=f"{spend_current_month/month_budget*100:.2f} %",  # format the number to 2 decimal places
            #                 showarrow=False,
            #                 height=10,
            #                 yshift=10)

            # col1.plotly_chart(fig, use_container_width=True)
            # with col2:
            #     fig_spend = go.Figure()
            #     df_current_month = filtered_df[(
            #         filtered_df[['spent_amount', 'impressions', 'cpm']] != 0).all(axis=1)]
            #     platform_id_spend = df_current_month.groupby(['platform_id']).agg(
            #         {'spent_amount': 'sum', 'cpm': 'mean'}).reset_index().sort_values(by='spent_amount', ascending=True)

            #     if platform_id_spend["spent_amount"].empty:
            #         max_spend = 0
            #     else:
            #         max_spend = max(platform_id_spend["spent_amount"])

            #         # Add the bars
            #     for index, row in platform_id_spend.iterrows():
            #         fig_spend.add_trace(go.Bar(
            #             x=[row['spent_amount']],
            #             y=[row['platform_id']],
            #             orientation='h',
            #             # this will be individual value now
            #             text=[row['spent_amount']],
            #             textposition='outside',
            #             marker_color=px.colors.qualitative.Plotly[index % len(
            #                 px.colors.qualitative.Plotly)]  # cycling through colors
            #         ))

                    # fig_spend.update_layout(title='Current month expanses by platform',
                    # xaxis = dict(
                    #     range=[0, max_spend*1.30], title='EUR'),
                    # yaxis_title = '',
                    # showlegend = False)

                    # st.plotly_chart(fig_spend, use_container_width=True)
                # with col22:
                #     platform_id_spend["spent_amount"] = round(
                #         platform_id_spend["spent_amount"], 2)
                #     st.table(platform_id_spend.rename(columns={
                #         "platform_id": "Platform", "spent_amount": "Spendings", "cpm": "CPM"}).sort_values(by='Spendings', ascending=False))
        

    # Campaigns abobve the budget, where budget comes from csv file #TODO
    # with st.container():
    #     # campaign_limit = st.number_input('Set a campaign limit')
    #     campains_grouped_budget = df_current_month.groupby(
    #         ['campaign_name']).agg({'spent_amount': 'sum'}).reset_index()
    #     campains_grouped_budget["budget"] = np.nan
    #     edited_df = st.data_editor(campains_grouped_budget, num_rows="dynamic")
    #     campaigns_above_budget = edited_df[edited_df['spent_amount']
    #                                        > edited_df['budget']]

    #     col1, col2 = st.columns(2)

    #     col1.metric("Number of campaigns above the limit ", '❗' +
    #                 str(campaigns_above_budget.shape[0]) + ' Campaigns above budget')  # TODO
    #     #col1.write(campaigns_above_budget.rename(
    #         #columns={"campaign_name": "Campaign", "spent_amount": "Spendings"}))

    #     if col1.button('Generate plot'):
    #         fig = go.Figure()
    #         fig.add_trace(go.Bar(
    #             y=campaigns_above_budget['campaign_name'],
    #             x=campaigns_above_budget['spent_amount'],
    #             orientation='h',
    #             name='Cost',
    #             marker_color='red',
    #             # <-- Add text values here
    #             text=campaigns_above_budget['spent_amount'],
    #             textposition='outside'
    #         ))

    #         # Add Budget bars
    #         fig.add_trace(go.Bar(
    #             y=campaigns_above_budget['campaign_name'],
    #             x=campaigns_above_budget['budget'],
    #             orientation='h',
    #             name='Budget',
    #             marker_color='blue',
    #             # <-- Add text values here
    #             text=campaigns_above_budget['budget'],
    #             textposition='outside'  # <-- Specify text position
    #         ))

    #         # Update layout
    #         fig.update_layout(
    #             title='Campaign Cost vs Budget',
    #             xaxis_title='Value',
    #             yaxis_title='Campaign Name',
    #             barmode='group'
    #         )

    #         col2.plotly_chart(fig, use_container_width=True)

    #st.dataframe(filtered_df.head(5))  # TODO tabulka nezarazenych kampani
