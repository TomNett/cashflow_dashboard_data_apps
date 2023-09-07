# TODO Dispaly only campaigns, which are not selected
# TODO scenare pro kampan  - pridat ?
# TODO: create a filter which will show only campaigns which are not related to a specific budget 
# TODO: Zobrazit kampani ktere bezi v vyprsenem budgetu 
# TODO vsechno v eurech
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
import base64
# import arrow
import snowflake.connector
pd.options.mode.chained_assignment = None  # default='warn'
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)

from my_package.html import html_code, html_footer, title
from my_package.style import apply_css
from my_package.style import css_style
from my_package.snowflake_related import insert_rows_to_snowflake, fetch_data_from_snowflake, delete_row_from_snowflake_by_row_id


# Layout settings ---------------
page_title = "Ad Expenses Tracker"
page_icon = ":bar_chart:"
layout = "wide"

#--------------------------------
st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)
apply_css()
# --- NAVIGATION MENU --- #
app_mode =option_menu(
    menu_title=None,
    options=['Spend',  'Analytics', 'Budgets', "Budget set up"],
    icons=["cash-coin", "bar-chart-line", "wallet-fill", "pencil-square"],
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

def first_day_month_from_name(month_name):
    first_d = '1 ' + month_name + ', 2023'
    first_date = custom_str_to_date(first_d)
    return first_date
    

def last_day_month_from_name(month_name,current_year):
    day_count = calendar.monthrange(2023, datetime.datetime.strptime(
        month_name, '%B').month)[1]
    last_d = str(day_count) + ' ' + \
        month_name + ', ' + str(current_year)
    last_date = custom_str_to_date(last_d)
    return last_date

def last_day_month(selected_year_month):
    day_count = calendar.monthrange(2023, datetime.datetime.strptime(
        selected_year_month[5:], '%B').month)[1]
    last_d = str(day_count) + ' ' + \
        selected_year_month[5:] + ', ' + selected_year_month[:4]
    last_date = custom_str_to_date(last_d)
    return last_date

# --- Function create a list of distinct campaigns which are not related to a specific budget --- #
def get_ditinct_campaigns_from_snowflake():
    campaigns_from_snowflake = []
    data_from_snowflake = fetch_data_from_snowflake()
    for l in data_from_snowflake["CAMPAIGNS"]:
        for c in l:
            campaigns_from_snowflake.append(c)
    return campaigns_from_snowflake

def camp_for_sorting(df):
    campaigns_for_sorting = []
    for campaigns_list in df['Campaigns']:
        for campaign in campaigns_list:
            campaigns_for_sorting.append(campaign)
    campaigns_for_sorting = list(set(campaigns_for_sorting))
    return campaigns_for_sorting



# file_path = "/data/in/tables/input_table.csv"
file_path = "/data/in/tables/ads_insight_fact.csv"
file_path_local = os.path.abspath(f"./app/data/ads_insight_fact.csv")
df = pd.read_csv(file_path)
# CREATED_DATE	start_date	MODIFIED_DATE	END_DATE
df["created_date"] = pd.to_datetime(df["created_date"]).dt.date
df["start_date"] = pd.to_datetime(df["start_date"]).dt.date
df["modified_date"] = pd.to_datetime(df["modified_date"]).dt.date
df["end_date"] = pd.to_datetime(df["end_date"]).dt.date


df["impressions"] = pd.to_numeric(df["impressions"])
df["link_clicks"] = pd.to_numeric(df["link_clicks"])
df['start_date'] = pd.to_datetime(df['start_date'])
df = df.dropna(subset=['start_date'])
df['campaign_name'] = df.apply(
    lambda row: row['platform_id'][:9] + '-' + row['campaign_name'], axis=1)
df["month_name"] = df.start_date.dt.strftime("%B")

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

metrics_list = [ 'reach', 'impressions', 'frequency', 'cpm',
       'link_clicks', 'ctr', 'post_comments', 'post_reactions', 'post_shares',
       'video_views', 'six_sec_video_view', 'full_video_view',
        'landing_page_clicks', 'paid_comments',
       'paid_likes', 'paid_shares']
most_frequent_metrics = [ 'reach', 'impressions','link_clicks',  'cpm',
        'ctr', 'frequency']

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
        st.subheader("Filter")
        # Extract unique values for campaigns and domains

        # Create two columns for filter controls
        # col1, col2 = st.columns((1.5, 1.5))
        # col11, col12 = st.columns((1.5, 1.5))

        # # Create filter controls for date range in the first column
        # with col1:
        #     since_date = st.date_input("Select a start date:",
        #                                datetime.date(current_year, current_month-3, 1), key="since_date")

        # # Create filter controls for source and campaign selection in the second column
        # with col2:
        #     until_date = st.date_input("Select an end date:",
        #                                datetime.date(current_year, current_month, current_day), key="until_date")
        # # Convert into same format to compare
        # since_date = pd.Timestamp(st.session_state.since_date)
        # until_date = pd.Timestamp(st.session_state.until_date)
        # filtered_df = df[(df['start_date'] >= since_date) &
        #                  (df['start_date'] <= until_date)]

        # with col11:
        #     selected_sources = st.multiselect('Select a source:',
        #                                       distinct_source, default=distinct_source, placeholder="All sources", key="source")
        # if len(st.session_state.source) != 0:
        #     filtered_df = filtered_df[filtered_df['platform_id'].isin(
        #         st.session_state.source)]
        #     distinct_campaigns = filtered_df['campaign_name'].unique()
        #     with col12:
        #         selected_campaigns = st.multiselect('Select a campaign:',
        #                                             distinct_campaigns, default=distinct_campaigns, placeholder="All campaigns", key="campaign")
        #     if len(st.session_state.campaign) != 0:
        #         filtered_df = filtered_df[filtered_df['campaign_name'].isin(
        #             st.session_state.campaign)]
            ##################
            # Filter section #
            ##################
            
        with st.container():
                #--- Data from snowflake for filters ---#        
            data_from_snowflake = fetch_data_from_snowflake()          
            data_from_snowflake.columns = data_from_snowflake.columns.str.lower()
            data_from_snowflake.columns = data_from_snowflake.columns.str.title()
            data_from_snowflake['Since_Date'] = pd.to_datetime(data_from_snowflake['Since_Date'])
            data_from_snowflake['Until_Date'] = pd.to_datetime(data_from_snowflake['Until_Date'])
            client_list = data_from_snowflake["Client"].unique()    
                  
            try:
                # Create two columns for filter controls
                col1, col2 = st.columns((1.5, 1.5))
                

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
                
                
                col11, col12 = st.columns((1.5, 1.5))
                col111, col122 = st.columns((1.5, 1.5))
                with col11:
                        selected_client = st.multiselect('Select a client',
                                                        client_list, default=client_list, placeholder='Clients',
                                                        key = "selected_client_spend"
                                                        )
                filtered_clients= data_from_snowflake[data_from_snowflake['Client'].isin(st.session_state["selected_client_spend"])]    
                campaigns_for_sorting = camp_for_sorting(filtered_clients) 

                if not selected_client:
                    col11.warning("Please select a client")
                else:
                    if len(st.session_state.selected_client_spend) != 0:
                        filtered_df = filtered_df[filtered_df['campaign_name'].isin(campaigns_for_sorting)]
                        distinct_campaigns_by_platform = filtered_df['campaign_name'].unique()
                        budget_list = filtered_clients["Budget"].unique() 
                        selected_budgets = col12.multiselect('Select a budget',budget_list, default=budget_list, key = "selected_budgets_spend")
                    if not selected_budgets:
                        col111.error("Please select budget")
                    else:
                        if len(st.session_state.selected_budgets_spend) != 0:
                            filtered_clients= filtered_clients[filtered_clients['Budget'].isin(st.session_state["selected_budgets_spend"])]    
                            campaigns_for_sorting = camp_for_sorting(filtered_clients)
                            filtered_df = filtered_df[filtered_df['campaign_name'].isin(campaigns_for_sorting)]
                            distinct_platfroms = filtered_df['platform_id'].unique()

                        with col111:
                            selected_sources = st.multiselect('Select Platform',
                                                            distinct_platfroms, default=distinct_platfroms, placeholder="Select  platforms from the list", key="source_spend")
                        if not selected_sources:
                            col122.error("Please select a platform.")
                        else:
                            if len(st.session_state.source_spend) != 0:

                                filtered_df = filtered_df[filtered_df['platform_id'].isin(
                                    st.session_state.source_spend)]
                                distinct_campaigns_by_platform = filtered_df['campaign_name'].unique(
                                )
                                with col122:
                                    selected_campaigns = st.multiselect('Select a campaign:',
                                                                        distinct_campaigns_by_platform, default=distinct_campaigns_by_platform, placeholder="Campaigns", key="campaign_spend")
                                filtered_df = filtered_df[filtered_df["campaign_name"].isin(st.session_state.campaign_spend)]    
            except URLError as e:
                            st.error()
        st.write("---")
        st.markdown(title["statistic"], unsafe_allow_html=True)
        st.markdown(css_style, unsafe_allow_html=True)
        col0 = st.columns(3)
        col1, col2, col3 = st.columns(3)   
            # Define metrics and associated icons

            # prepare data
        total_clicks = filtered_df['link_clicks'].sum()
        total_impressions = filtered_df['impressions'].sum()
        total_spend = filtered_df['spent_amount'].sum()
        total_reach = filtered_df['reach'].sum()
        average_cpm = filtered_df[['cpm']].mean()
        average_ctr = filtered_df[['ctr']].mean()
        def format_data(data):
            if isinstance(data, np.float64):
                formatted_data = format_float(data)
            elif isinstance(data, pd.Series):
                formatted_data = format_series(data)
            else:
                formatted_data = format_float(data)
            return formatted_data

        def format_float(value):
            if value.is_integer():
                return '{:,.0f}'.format(value).replace(',', ' ')
            else:
                 formatted_value = '{:,.1f}'.format(value).replace(',', ' ')
                 return formatted_value


        def format_series(series):
            formatted_series = series.apply(format_float)
            return '\n'.join(formatted_series)

        metrics = [
            ("Impressions:", total_impressions),
            ("Clicks:", total_clicks),
            ("Total spendings:", total_clicks),
            ("Click-Through Rate:", average_ctr),                
            ("Reach ",total_reach ),
            ("Average Cost per Mile:",average_cpm ),
            
        ]

        my_dict = {
            "Clicks": "click.png",
            "Click-Through Rate": "click.png",
            "Total spendings:":"money.png",
            "Impressions": "impression.png",
            "Average Cost per Mile":"money.png",
            "Reach": "reach.png"
        }

            # Iterate over the metrics and display icons and values
        for i, metric in enumerate(metrics):
            column_index = i % 3
            metric_label, metric_value = metric
            number =  format_data(metric_value)
            col = col1 if column_index == 0 else col2 if column_index == 1 else col3
            # Retrieve the icon for the metric label
            for key in my_dict.keys():
                if key in metric_label:
                       icon_path = my_dict[key]

            formated_number = number
            if('cost' in metric_label.lower()):
                formated_number = f'{number} €'
            if('spend' in metric_label.lower()):
                formated_number = f'{number} €'
            if('rate' in metric_label.lower()):
                formated_number = f'{number} %'
                
            number_with_percent = f'{number} %' if 'rate:' in metric_label.lower() else number

            with col:
                 # icon_image = os.path.abspath(f"/home/appuser/app/static/{icon_path}")
                icon_image = os.path.abspath(f"./app/static/{icon_path}")
                st.markdown(f'''
                <div style="margin: 10px auto; width: 70%">
                    <div class="div-container" style="display:flex; margin:10px">
                        <div class="div-icon" style="flex-basis:2">
                            <img class="icon-img"  src="data:image/png;base64,{base64.b64encode(open(icon_image, "rb").read()).decode()}">
                        </div>
                        <div style="flex-shrink:1; margin-left: 8%">
                            <h2 class="header">{metric_label}</h2>
                            <p class="text">{formated_number}</p>
                        </div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
        st.write("---")
        selected_metrics = st.multiselect('Select metrics', metrics_list, default=most_frequent_metrics,key="selectedmetrics")
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Best performing Campaigns","Visualizations per Platform", "Visualizations per Campaigns", "Raw data"])
        
        # grouped['ctr'] = (grouped['link_clicks'] /
        #                   grouped['impressions']) * 100
        # Campaigns_df = grouped.copy()
        # max_campaign = Campaigns_df["ctr"].max()
        
        
        with tab1:
            
            agg_dict = {metric: 'sum' for metric in selected_metrics}
            df_top_campaign = filtered_df.groupby(['platform_id', 'campaign_name', 'start_date']).agg(agg_dict).reset_index()
            
            st.markdown(title["topcampaigns"], unsafe_allow_html=True)
            boolean_list = [False for _ in selected_metrics]
            df_sorted = df_top_campaign.sort_values(by=selected_metrics, ascending=boolean_list)
            st.dataframe(df_sorted.head(5))
            col1, col2 = st.columns(2)
            if 'ctr' in selected_metrics:
                ctr_mean = round(np.mean(df_sorted["ctr"]), 2)
                col1.metric("Average Clickthrough Rate Of Top Performing Campaigns", str(ctr_mean) + ' %')
                target_value = col1.slider('Target Clickthrough Rate', 0.0, 5.0, 0.5)
                target_value = 0.5
                fig = px.bar(x=[ctr_mean],
                            y=['ctr'],
                            orientation='h',
                            labels={'x': '%', 'y': ''},
                            title='Average Clickthrough rate')
                fig.update_layout(xaxis=dict(range=[0, 5]), height=200)
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

            
            if 'cpm' in selected_metrics:
                cpm_mean = round(np.mean(df_sorted["cpm"]), 2)
                max_cpm = np.max(df_sorted["cpm"])
                col2.metric("Cost Per Mille Of Top Performing Campaigns", str(cpm_mean) + ' EUR')
                cpm_mean = round(np.mean(df_sorted["cpm"]), 2)
                max_cpm_range = cpm_mean
                target_value_cpm = col2.slider('Target Clickthrough Rate', 0.0, cpm_mean*1.2, cpm_mean/2)
                fig = px.bar(x=[cpm_mean],
                            y=['cpm'],
                            orientation='h',
                            labels={'x': 'EUR', 'y': ''},
                            title='Average CPM')
                fig.update_layout(xaxis=dict(range=[0, cpm_mean*1.2]), height=200)
                fig.update_traces(marker_color='rgb(255, 75, 75)')
                fig.add_shape(type="line",
                            x0=target_value_cpm, y0=0, x1=target_value_cpm, y1=1,
                            line=dict(color='rgb(64, 224, 208)', width=6),
                            xref='x', yref='paper')
                fig.add_annotation(x=cpm_mean, y='cpm',
                                # format the number to 2 decimal places
                                text=f"{cpm_mean:.2f} EUR",
                                showarrow=False,
                                yshift=20)

                col2.plotly_chart(fig, use_container_width=True)

        with tab2:
            #col1, col2 = st.columns(2)
            #with col1:

            for metric in selected_metrics:
                st.subheader(metric.title() + ' chart')
                if metric in filtered_df.columns:
                    fig = px.bar(filtered_df, x="start_date", y=metric, color="platform_id")
                    fig.update_layout(xaxis_title='Date', yaxis_title=metric)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write(f"The metric '{metric}' is not available in the data.")
        with tab3:
            
            for metric in selected_metrics:
                st.subheader(metric.title() + ' chart')
                if metric in filtered_df.columns:
                    fig = px.bar(filtered_df, x="start_date", y=metric, color="campaign_name")
                    fig.update_layout(xaxis_title='Date', yaxis_title=metric)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write(f"The metric '{metric}' is not available in the data.")
            #with col2:
                # for metric in selected_metrics:
                #     if metric in filtered_df.columns:
                #         fig = px.line(filtered_df, x="start_date", y=metric, color="campaign_name")
                        
                #         # Update layout
                #         fig.update_layout(
                #             xaxis_title='Date',
                #             yaxis_title=metric,
                #         )
                #         fig.update_yaxes(range=[0, filtered_df[metric].max() + 5])
                        
                #         st.plotly_chart(fig, use_container_width=True)
                #     else:
                #         st.write(f"The metric '{metric}' is not available in the data.")
            # # # Display title for the "Campaigns" section
            # st.markdown(title["impressions"], unsafe_allow_html=True)
            # fig = px.bar(Campaigns_df, x="start_date",
            #              y="impressions", color="campaign_name")
            # # st.bar_chart(data = Campaigns_df, x="start_date", y="impressions",use_container_width=True)
            # # fig = px.bar(Campaigns_df, x="start_date", y="impressions", color="campaign_name") # , color="source"
            # fig.update_layout(xaxis_title='Date', yaxis_title='impressions')
            # # # Display the bar chart
            # st.plotly_chart(fig, use_container_width=True)

            # # Clicks
            # st.markdown(title["clicks"], unsafe_allow_html=True)
            # fig = px.bar(Campaigns_df, x="start_date", y="link_clicks",
            #              color="campaign_name")  # , color="source"
            # fig.update_layout(
            #     xaxis_title='Date',
            #     yaxis_title='Clicks',
            # )
            # # Display the bar chart
            # st.plotly_chart(fig, use_container_width=True)

            # st.markdown(title["clicktr"], unsafe_allow_html=True)
            # fig = px.line(Campaigns_df, x="start_date", y="ctr",
            #               color="campaign_name")  # , color="source"

            # # # Update layout
            # fig.update_layout(
            #     xaxis_title='Date',
            #     yaxis_title='Click-Through Rate %',
            # )
            # fig.update_yaxes(range=[0, max_campaign+5])
            # st.plotly_chart(fig, use_container_width=True)

        with tab4:
            st.markdown('Dataset :')
            st.write(df.head())


elif app_mode == 'Spend':
    with st.container():
        col1, col2, col3 = st.columns((1.4,1,1), gap="small")
        col2.title("Spend overview")


    with st.container():
        
        
        ##################################################
        #--- Data for metrics - current month ---#
        ##################################################
        df_current_month = df[(df['start_date'] >= pd.to_datetime(first_day_month_from_name(current_month_name))) & (
            df['start_date'] <= pd.to_datetime(last_day_month_from_name(current_month_name,current_year)))]
        spend_current_month = round(
                    np.sum(df_current_month["spent_amount"]), 2)
        st.subheader("Current month overview")
        col1,col2 = st.columns(2)
        
        if df_current_month.empty:
            col1.warning(f"There are no data for {current_month_name} or there are no active campaigns")
        else:
            col1.metric(f"Total spend in {current_month_name} ", str(spend_current_month) + ' EUR')
        # Column 2

        platform_id_spend = df_current_month.groupby(
            ['platform_id']).agg({'spent_amount': 'sum'}).reset_index()

        # target_value_platform_id = col2.number_input('Target Spend Amount For platform_id')
        if platform_id_spend.empty:
            col2.warning(f"There are no data for {current_month_name}")
        else:    
            col2.metric("Average Spend By platform_id", str(
                round(np.mean(platform_id_spend["spent_amount"]), 2)) + ' EUR')
        st.write("---")
            ##################
            # Filter section #
            ##################
            
        with st.container():
                #--- Data from snowflake for filters ---#        
            data_from_snowflake = fetch_data_from_snowflake()          
            data_from_snowflake.columns = data_from_snowflake.columns.str.lower()
            data_from_snowflake.columns = data_from_snowflake.columns.str.title()
            data_from_snowflake['Since_Date'] = pd.to_datetime(data_from_snowflake['Since_Date'])
            data_from_snowflake['Until_Date'] = pd.to_datetime(data_from_snowflake['Until_Date'])
            client_list = data_from_snowflake["Client"].unique()    
                  
            try:
                # Create two columns for filter controls
                col1, col2 = st.columns((1.5, 1.5))
                

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
                
                
                col11, col12 = st.columns((1.5, 1.5))
                col111, col122 = st.columns((1.5, 1.5))
                with col11:
                        selected_client = st.multiselect('Select a client',
                                                        client_list, default=client_list, placeholder='Clients',
                                                        key = "selected_client_spend"
                                                        )
                filtered_clients= data_from_snowflake[data_from_snowflake['Client'].isin(st.session_state["selected_client_spend"])]    
                campaigns_for_sorting = camp_for_sorting(filtered_clients) 

                if not selected_client:
                    col11.warning("Please select a client")
                else:
                    if len(st.session_state.selected_client_spend) != 0:
                        filtered_df = filtered_df[filtered_df['campaign_name'].isin(campaigns_for_sorting)]
                        distinct_campaigns_by_platform = filtered_df['campaign_name'].unique()
                        budget_list = filtered_clients["Budget"].unique() 
                        selected_budgets = col12.multiselect('Select a budget',budget_list, default=budget_list, key = "selected_budgets_spend")
                    if not selected_budgets:
                        col111.error("Please select budget")
                    else:
                        if len(st.session_state.selected_budgets_spend) != 0:
                            filtered_clients= filtered_clients[filtered_clients['Budget'].isin(st.session_state["selected_budgets_spend"])]    
                            campaigns_for_sorting = camp_for_sorting(filtered_clients)
                            filtered_df = filtered_df[filtered_df['campaign_name'].isin(campaigns_for_sorting)]
                            distinct_platfroms = filtered_df['platform_id'].unique()

                        with col111:
                            selected_sources = st.multiselect('Select Platform',
                                                            distinct_platfroms, default=distinct_platfroms, placeholder="Select  platforms from the list", key="source_spend")
                        if not selected_sources:
                            col122.error("Please select a platform.")
                        else:
                            if len(st.session_state.source_spend) != 0:

                                filtered_df = filtered_df[filtered_df['platform_id'].isin(
                                    st.session_state.source_spend)]
                                distinct_campaigns_by_platform = filtered_df['campaign_name'].unique(
                                )
                                with col122:
                                    selected_campaigns = st.multiselect('Select a campaign:',
                                                                        distinct_campaigns_by_platform, default=distinct_campaigns_by_platform, placeholder="Campaigns", key="campaign_spend")
                                filtered_df = filtered_df[filtered_df["campaign_name"].isin(st.session_state.campaign_spend)]
                        
                                
                        col1, col2 = st.columns(2)
                        # Column 1
                        #current_month_name = datetime.datetime.now().strftime("%B")
                        # Initialize the figure
                        fig = go.Figure()
                        try:
                            month_spend = filtered_df.groupby(['month_name']).agg(
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

                                fig.update_layout(title='Spend by month',
                                                xaxis=dict(range=[0, max(
                                                    month_spend["spent_amount"])*1.15], title='Spend in EUR', showgrid=True),
                                                yaxis_title='Month',
                                                showlegend=False)

                                # fig.add_shape(type="line",
                                #             x0=target_value, y0=0, x1=target_value, y1=1,
                                #             line=dict(color='rgb(64, 224, 208)', width=3),
                                #             xref='x', yref='paper')

                                col1.plotly_chart(fig, use_container_width=True)

                                # Column 2

                                platform_id_spend = filtered_df.groupby(
                                    ['platform_id']).agg({'spent_amount': 'sum'}).reset_index()
                                max_value_by_platform = max(platform_id_spend['spent_amount'])
                                # target_value_platform_id = col2.number_input('Target Spend Amount For platform_id')

                                fig_spend = go.Figure()

                                # Add the bars
                                for index, row in platform_id_spend.iterrows():
                                    fig_spend.add_trace(go.Bar(
                                        x=[row['spent_amount']],
                                        y=[row['platform_id']],
                                        orientation='h',
                                        # this will be individual value now
                                        text=[str(round(row['spent_amount'],2)) + ' EUR'],
                                        textposition='outside',
                                        marker_color=px.colors.qualitative.Plotly[index % len(
                                            px.colors.qualitative.Plotly)]  # cycling through colors
                                    ))

                                fig_spend.update_layout(title='Spend By Platform',
                                                        xaxis=dict(
                                                            range=[0, max_value_by_platform*1.15], title='EUR'),
                                                        yaxis_title='',
                                                        showlegend=False)

                                # fig_spend.add_shape(type="line",
                                #                     x0=target_value_platform_id, y0=0, x1=target_value_platform_id, y1=1,
                                #                     line=dict(color='rgb(64, 224, 208)', width=6),
                                #                     xref='x', yref='paper')

                                col2.plotly_chart(fig_spend, use_container_width=True)
                        except URLError as e:
                            st.error()

                ###################
                # Metrics section #
                ###################

                # Columns and data creation

                # df_current_month = df[(df['start_date'] >= (
                #     current_date - timedelta(days=30))) & (df['start_date'] <= current_date)]
                # df_last_month = df[(df['start_date'] >= (current_date - timedelta(days=60))) & (
                #     df['start_date'] <= (current_date - timedelta(days=60)))]  # TODO change to current month
                
            except URLError as e:
                st.error()

        

        ####################
        # Charts  sections #
        ####################
        tab1, tab2 = st.tabs(
            ["Spend By Platform", "Spend By Campaign"])
     


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
        # except URLError as e:
        #     st.error()

elif app_mode == 'Budget set up':
     with st.container():
        # df_current_month = df[(df['start_date'] >= (current_date - timedelta(days=30))) & (df['start_date'] <= current_date)]
        col1, col2 = st.columns(2, gap="small")
        col11, col12 = st.columns((1.5, 1.5))

        col1, col2, col3 = st.columns((2, 1, 1))
        col11.subheader('Budget set up')

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
                            filtered_df = df[df['start_date'] >= pd.to_datetime(first_day_month(selected_year_month))] #& (
                                #df['start_date'] <= pd.to_datetime(last_day_month(selected_year_month)))
                        if len(st.session_state.source) != 0:
                            filtered_df = filtered_df[filtered_df['platform_id'].isin(
                                st.session_state.source)]
                            
                            distinct_campaigns_by_platform =  filtered_df[~df['campaign_name'].isin(get_ditinct_campaigns_from_snowflake())]
                            distinct_campaigns_by_platform = distinct_campaigns_by_platform['campaign_name'].unique()
                        session_state.row[col] = col11.multiselect('Select a campaign:',
                                                                   distinct_campaigns_by_platform, default=None, placeholder="All campaigns", key="campaign")
                except URLError as e:
                    st.error()
                col1, col2 = st.columns(2)
                # Add a button to add a new empty row to the dataframe and clear the values of the selectboxes for the current row
                fetched_df = fetch_data_from_snowflake()
                row_num = fetched_df.shape[0]
                with col12:
                    st.subheader("Entered data preview ")
                    st.table(session_state.row)
                    
                    
                    if st.button("Add Row", disabled=False): #TODO: Transform it to use snowflake funct
                        insert_rows_to_snowflake(session_state.row)
                        
                        session_state.df.loc[len(
                            session_state.df)] = session_state.row
                        session_state.row = pd.Series(index=columns)
                    
                    st.write("---")
                    
                    index_to_delete = st.number_input(
                            'Budget ID', value=0,min_value=0, max_value = row_num-1)
                    
                    st.warning(""" Specify a budget you want to ***delete*** or ***change*** """)
                    if st.button("Delete Row", key="deleterow", disabled=False):
                        delete_row_from_snowflake_by_row_id(index_to_delete)
                        data_df = pd.DataFrame(fetch_data_from_snowflake())

                        

                        
                    # st.error('Function does not work right now')
                    # if st.button("Change Row", key='rowchange', disabled=True):
                    #     # TODO
                    #     print('Hi')
                st.header("Budgets and their limits")                
                current_budgets = fetch_data_from_snowflake()
                current_budgets['CAMPAIGNS'] = current_budgets['CAMPAIGNS'].apply(lambda x: '<br>'.join(['["' + '",<br>"'.join(x) + '"]']))

                # Convert entire dataframe to HTML and use st.write to display
                st.write(current_budgets.to_html(escape=False, index=False), unsafe_allow_html=True)
                
                

                # data_df = st.data_editor(
                #     data_df,
                #     column_config={
                #         "Selected row": st.column_config.CheckboxColumn(
                #             "Selection column",
                #             help="Select  **column** ",
                #             default=False,
                #         )
                #     },
                #     disabled=["CLIENT", "BUDGET", "BUDGET_AMOUNT", "CURRENCY", "SINCE_DATE", "UNTIL_DATE", "CAMPAIGNS"],
                #     hide_index=True,
                # )
                
                
                

        # st.dataframe(session_state.df)
        # st.data_editor(budget_df, num_rows="static")
         

elif app_mode == 'Budgets':

    with st.container():
        col1, col2, col3 = st.columns(3, gap="small")
        with col2:
            st.title("Budget overview")
    
    

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
        tab1, tab2 = st.tabs(
            ["Client overview", "Detailed Budget Examination"])
        with tab1:
            st.header("Filters: ")
            # Create two columns for filter controls
            #data_from_snowflake = data_from_snowflake[data_from_snowflake['Since_Date'] >= pd.to_datetime(first_day_month())]
            filtered_clients= data_from_snowflake
            
            with st.form("entry_form_budget_filter", clear_on_submit=False):
                
                col1f, col2f = st.columns((1.5, 3))
                col1f.selectbox('Select Year and Month:',
                                                  ordered_list_year_month, index=default_ix_for_filter,  placeholder="All months", key="monthfiltercharts")
                col2f.multiselect('Select a client',
                                                    client_list, default=client_list, placeholder="Client", key="clientunique")
                
                apply_css()
                submitted = st.form_submit_button("Filter data",use_container_width = True)
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

            
            campaigns_for_sorting = camp_for_sorting(filtered_clients)
            
            filtered_df_2 = filtered_df[filtered_df['campaign_name'].isin(campaigns_for_sorting)]
            campaign_spend = filtered_df_2.groupby(['campaign_name']).agg(
                                {'spent_amount': 'sum'}).reset_index().sort_values(by='spent_amount', ascending=False)
            platform_campaign_spend = filtered_df_2.groupby(['platform_id','campaign_name']).agg(
                        {'spent_amount': 'sum'}).reset_index().sort_values(by='spent_amount', ascending=False)

            mapping = data_from_snowflake.explode('Campaigns')[['Client', 'Campaigns']].rename(columns={'Campaigns': 'campaign_name'})
            merged = pd.merge(mapping, campaign_spend, on='campaign_name', how='left').fillna(0)
            total_spent_per_client = merged.groupby('Client')['spent_amount'].sum().reset_index()
            final_df = pd.merge(budget_by_client, total_spent_per_client, on='Client', how='left')
            final_df.rename(columns={'spent_amount': 'Total_Spent'}, inplace=True)
            final_df['Unspent'] = final_df['Budget_Amount'] - final_df['Total_Spent']
            final_df['Percentage_spend']  = round(final_df['Total_Spent']/ final_df['Budget_Amount']*100,2)
            budgets_above_budget = final_df[final_df["Total_Spent"]> final_df['Budget_Amount']]
            budgets_below_budget = final_df[final_df["Total_Spent"] <  final_df['Budget_Amount']]
            budgets_below_budget = budgets_below_budget.rename(columns={"Budget_Amount": "Budget amount", "Total_Spent": "Total spend","Percentage_spend": "Percentage spend"}) 

            
            
            # --- Printing filtered data in second column --- #
            col2.markdown(title["inputdata"], unsafe_allow_html=True)
            col2.table(budgets_below_budget)
            col2.error(" ⬇️ Spendings exceed budget limit")
            col2.table(budgets_above_budget)
            st.write("---")
            # --- Creating plot for client's budget --- #
            if budgets_below_budget.empty:
                col1.warning(":face_with_monocle:" + " There are no data for this date and client")
                # Adding bars for Unspent
            else: 
                # Adding bars for Total Spent
                fig_spend = go.Figure()
                for index, row in budgets_below_budget.iterrows():
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
                for index, row in budgets_below_budget.iterrows():
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
                max_budget = budgets_below_budget['Budget amount'].max()
                max_spend = budgets_below_budget['Total spend'].max()
                if max_budget >= max_spend:
                    max_v = max_budget
                else:
                    max_v = max_spend

                fig_spend.update_layout(title='Client Spend vs Budget',
                                            xaxis=dict(
                                                range=[0, max_v * 1.10], title='EUR'),
                                            yaxis_title='',
                                            barmode='stack',
                                            showlegend=False)
                    #fig.for_each_trace(lambda t: t.update(textfont_color=t.marker.color, textposition='top center')) 
                col1.plotly_chart(fig_spend, use_container_width=True)
                
                #########################
                # ---  Bar chart --- #
                #########################
            col11, col12 = st.columns((2, 1), gap="large")

            spendings_df = pd.DataFrame(columns=['Client', 'Platform', 'Spend'])

                # for index, row in filtered_clients.iterrows():
                #     for campaign in row['Campaings']:
                #         platform = campaign.split('-')[0]

                #         # Check if the campaign exists in campaign_spend
                #         campaign_data = campaign_spend[campaign_spend['campaign_name'] == campaign]['spent_amount']
                #         if not campaign_data.empty:
                #             spend = campaign_data.iloc[0]
                #         else:
                #             spend = 0

                #         # Append the data to the spendings_df
                #         new_row = pd.DataFrame({
                #             'Client': [row['Client']],
                #             'Platform': [platform],
                #             'Spend': [spend]
                #         })
                #         spendings_df = pd.concat([spendings_df, new_row], ignore_index=True)
                # # Aggregate spendings by client and platform
                # spendings_agg = spendings_df.groupby(['Client', 'Platform']).sum().reset_index()
                # # Create a grouped bar chart using Plotly
                # fig = go.Figure()
                # platforms = spendings_agg['Platform'].unique()

                # for platform in platforms:
                #     filtered_data = spendings_agg[spendings_agg['Platform'] == platform]
                #     fig.add_trace(go.Bar(
                #         x=filtered_data['Client'],
                #         y=filtered_data['Spend'],
                #         name=platform,
                        
                #     ))
                # fig.update_layout(
                #     legend_title_text='Platform',                    
                #     legend=dict(
                #         font=dict(
                #             size=20                                                                                    
                #         )
                #     ),
                #     xaxis=dict(
                #         tickfont=dict(
                #             size=20
                #         )
                #     )
                # )                

                # col11.plotly_chart(fig, use_container_width=True) 

                #########################
                #########################
                #########################
            if filtered_clients.empty:
                col11.warning("🧐" +"There are no data for this date and client")  
            else:                 
                for index, row in filtered_clients.iterrows():
                    for campaign in row['Campaigns']:
                        platform = campaign.split('-')[0]

                        # Check if the campaign exists in campaign_spend
                        campaign_data = campaign_spend[campaign_spend['campaign_name'] == campaign]['spent_amount']
                        if not campaign_data.empty:
                            spend = campaign_data.iloc[0]
                        else:
                            spend = 0

                            # Append the data to the spendings_df
                        new_row = pd.DataFrame({
                            'Client': [row['Client']],
                            'Platform': [platform],
                            'Spend': [spend]
                        })
                        spendings_df = pd.concat([spendings_df, new_row], ignore_index=True)
                    
                spendings_df = spendings_df.drop_duplicates()
                    
                # Aggregate spendings by client and platform
                spendings_agg = spendings_df.groupby(['Client', 'Platform']).sum().reset_index()

                max_budget = final_df['Budget_Amount'].max()
                max_spend = final_df['Total_Spent'].max()
                if max_budget >= max_spend:
                    max_v = max_budget
                else:
                    max_v = max_spend
                    
                    
                # Create a grouped bar chart using Plotly
                fig = go.Figure()
                platforms = spendings_agg['Platform'].unique()

                for platform in platforms:
                    filtered_data = spendings_agg[spendings_agg['Platform'] == platform]
                    fig.add_trace(go.Bar(
                        x=filtered_data['Client'],
                        y=filtered_data['Spend'],
                        name=platform
                    ))

                # Update the bar mode to "stack" to get the desired visualization
                fig.update_layout(
                    barmode='stack',
                    legend_title_text='Platform',
                    legend=dict(
                        font=dict(
                            size=20
                        )
                    ),
                    xaxis=dict(
                        tickfont=dict(
                            size=20
                        )
                    ),
                    yaxis=dict(
                    range=[0, max_v * 1.2], title='EUR')
                )
                fig.update_layout(title="Spendings by Platform for Selected Client", )
                col11.plotly_chart(fig, use_container_width=True) 

            st.divider()  

                
               

            # --- TAB 2 FOR BUDGETS --- #
            
            with tab2:
                st.header("Filters: ")

                
                with st.form("entry_form_budget_filter_tab2", clear_on_submit=False):
                    col1f, col2f = st.columns((1.5, 3))
                    col1f.selectbox('Select Year and Month:',
                                                    ordered_list_year_month, index=default_ix_for_filter,  placeholder="All months", key="monthfiltercharts_tab2")
                    col2f.multiselect('Select a source:',
                                                        client_list, default=client_list, placeholder="Client", key="clientunique_tab2")
                    apply_css()
                    submitted = st.form_submit_button("Filter data",use_container_width = True)
                    if submitted:
                        data_from_snowflake = data_from_snowflake[data_from_snowflake['Since_Date'] >= pd.to_datetime(first_day_month(st.session_state["monthfiltercharts_tab2"]))]
                        filtered_clients= data_from_snowflake[data_from_snowflake['Client'].isin(st.session_state["clientunique_tab2"])]
                        filtered_df = df[df["start_date"]>= pd.to_datetime(first_day_month(st.session_state["monthfiltercharts_tab2"]))] 
                 #################################
                 # --- Budget over time look --- #
                 #################################
                consolidated_daily_spend = pd.DataFrame()
                
                daily_spend = filtered_df.groupby(['start_date', 'campaign_name']).agg({'spent_amount': 'sum'}).reset_index()
                budgets = filtered_clients['Budget'].unique()
                full_date_range = pd.date_range(start=daily_spend['start_date'].min(), end=daily_spend['start_date'].max())
                consolidated_daily_spend = pd.DataFrame({'Date': full_date_range})
                # Create a complete date range from the earliest to the latest date in the dataset
                ind = 1
                fig = go.Figure()
                for budget in budgets:
                        related_campaigns = filtered_clients[filtered_clients['Budget'] == budget]['Campaigns'].explode().unique()

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

                
                if filtered_clients.empty:
                    st.warning(":face_with_monocle:" + " There is no data for this period")
                                # Adding bars for Unspent
                else: 
                    budget_groups = filtered_clients.groupby('Budget')                 
                    num_budgets = len(budget_groups)
                    sqrt_budgets = int(np.sqrt(num_budgets))
                    cols = sqrt_budgets if num_budgets == sqrt_budgets**2 else sqrt_budgets + 1
                    rows = num_budgets // cols + (num_budgets % cols > 0)  # ceil operation

                    subplot_titles = [name for name, _ in budget_groups]

                    fig = make_subplots(rows=rows, cols=cols, subplot_titles=subplot_titles, specs=[[{'type':'domain'} for _ in range(cols)] for _ in range(rows)])

                    for index, (budget_name, group) in enumerate(budget_groups):
                        platform_spendings = {}  # Dictionary to hold platform and their corresponding spending
                        
                        for _, row in group.iterrows():
                            for campaign in row['Campaigns']:
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
    #     campaigns_grouped_budget = df_current_month.groupby(
    #         ['campaign_name']).agg({'spent_amount': 'sum'}).reset_index()
    #     campaigns_grouped_budget["budget"] = np.nan
    #     edited_df = st.data_editor(campaigns_grouped_budget, num_rows="dynamic")
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
