import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
import matplotlib.pyplot as plt 
import plotly.express as px

from my_package.style import css_style
from my_package.html import html_code, html_footer, title


st.set_page_config(layout="wide")
file_path = "/data/in/tables/input_table.csv"
file_path_local = "data_apps\data\data.csv"

df = pd.read_csv(file_path_local)
df = df.dropna(axis = 1)
#CREATED_DATE	START_DATE	MODIFIED_DATE	END_DATE
df["CREATED_DATE"] = pd.to_datetime(df["CREATED_DATE"]).dt.date
df["START_DATE"] = pd.to_datetime(df["START_DATE"]).dt.date
df["MODIFIED_DATE"] = pd.to_datetime(df["MODIFIED_DATE"]).dt.date
df["END_DATE"] = pd.to_datetime(df["END_DATE"]).dt.date
df["IMPRESSIONS"] = pd.to_numeric(df["IMPRESSIONS"])
df["LINK_CLICKS"] = pd.to_numeric(df["LINK_CLICKS"])
df['START_DATE'] = pd.to_datetime(df['START_DATE'])

app_mode = st.sidebar.selectbox('Select Page',['Expenses','Analytics']) #two pages
distinct_campaigns = df['CAMPAIGN_NAME'].unique()
distinct_source = df["PLATFORM"].unique()
 # Get current month and year
current_month = datetime.datetime.now().month
current_year = datetime.datetime.now().year
current_day = datetime.datetime.now().day

# Define default filter values
default = {
        'since_date': datetime.date(current_year, 1, 1),
        'until_date': datetime.date(current_year, current_month, 1),
        'source': [],
        'campaign': []
        }

if app_mode=='Analytics':
    st.title('Analytical page')
      
    with st.container():
        st.text("Filter")
        # Extract unique values for campaigns and domains
        
        
        # Create two columns for filter controls
        col1, col2 = st.columns((1.5, 1.5))
        col11,col12 = st.columns((1.5, 1.5))

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
        
        
        filtered_df = df[(df['START_DATE'] >= since_date) & (df['START_DATE'] <= until_date)]
        
        if len(st.session_state.source) != 0:
            filtered_df = filtered_df[filtered_df['PLATFORM'].isin(st.session_state.source)]

        if len(st.session_state.campaign) != 0:
            filtered_df = filtered_df[filtered_df['CAMPAIGN_NAME'].isin(st.session_state.campaign)]

        st.markdown(title["charts"], unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["Visualizations per Campaigns","Visualizations per Platform", "Raw data"])
        grouped = filtered_df.groupby(['CAMPAIGN_NAME', 'START_DATE']).agg({'LINK_CLICKS': 'sum', 'IMPRESSIONS': 'sum'}).reset_index()
        grouped['ctr'] = (grouped['LINK_CLICKS'] / grouped['IMPRESSIONS']) * 100
        campaings_df = grouped.copy()
        max_campaign = campaings_df["ctr"].max()
        #max_campaign = campaings_df["CTR"].max()

        with tab1:
            # # Display title for the "Campaigns" section
            st.markdown(title["impressions"], unsafe_allow_html=True)
            fig = px.bar(campaings_df, x="START_DATE", y="IMPRESSIONS", color="CAMPAIGN_NAME")
            #st.bar_chart(data = campaings_df, x="START_DATE", y="IMPRESSIONS",use_container_width=True)
            # fig = px.bar(campaings_df, x="START_DATE", y="IMPRESSIONS", color="CAMPAIGN_NAME") # , color="source"
            fig.update_layout(xaxis_title='Date', yaxis_title='Impressions')
            # # Display the bar chart
            st.plotly_chart(fig, use_container_width=True)

            # Clicks
            st.markdown(title["clicks"], unsafe_allow_html=True)
            fig = px.bar(campaings_df, x="START_DATE", y="LINK_CLICKS", color="CAMPAIGN_NAME") # , color="source"
            fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Clicks',
            )
            # Display the bar chart
            st.plotly_chart(fig, use_container_width=True)

            st.markdown(title["clicktr"], unsafe_allow_html=True)
            fig = px.line(campaings_df, x="START_DATE", y="ctr", color="CAMPAIGN_NAME") #, color="source"

            # # Update layout
            fig.update_layout(
                xaxis_title='Date',
                yaxis_title='Click-Through Rate %',
            )
            fig.update_yaxes(range = [0,max_campaign+5])
            st.plotly_chart(fig, use_container_width=True)

            # # Display the line chart
            # st.plotly_chart(fig, use_container_width=True)

            # # Display title for the "top 10 campaigns" section
            # st.markdown(title["sourcesPerClick"], unsafe_allow_html=True)

            # # Create columns for layout
            # c10, c11, c1010, c12, c13 = st.columns((0.5, 2.5, 0.5, 2.5, 0.5))
        with tab3:
            st.markdown('Dataset :')    
            st.write(df.head())
        
        
        
        st.stop()
elif app_mode == 'Expenses':
     with st.container():
        st.title("Expenses overview")
        st.sidebar.header("Filters: ")  
        
        with st.container():
           
            
            # Create two columns for filter controls
            col1, col2 = st.sidebar.columns((1.5, 1.5))
            col11,col12 = st.sidebar.columns((1.5, 1.5))

            # Create filter controls for date range in the first column
            with col1:
                since_date = st.sidebar.date_input("Select a start date:",
                                            datetime.date(current_year, current_month-3, 1), key="since_date")
        
            # Create filter controls for source and campaign selection in the second column
            with col2:
                until_date = st.sidebar.date_input("Select an end date:",
                                            datetime.date(current_year, current_month, current_day), key="until_date")
                
            with col11:
                selected_sources = st.sidebar.multiselect('Select a platform:',
                                                distinct_source, default=None, placeholder="All platforms", key="source")
            
            with col12:
                selected_campaigns = st.sidebar.multiselect('Select a campaign:',
                                                    distinct_campaigns, default=None, placeholder="All campaigns", key="campaign") 
        
        since_date = pd.Timestamp(st.session_state.since_date)
        until_date = pd.Timestamp(st.session_state.until_date)
        filtered_df = df[(df['START_DATE'] >= since_date) & (df['START_DATE'] <= until_date)]
        tab1, tab2 = st.tabs(["Expenses per Platform","Expenses per Campaign"])
        
        grouped = filtered_df.groupby(['CAMPAIGN_NAME', 'START_DATE'])\
            .agg({'AMOUNT_SPENT': 'sum' }).reset_index()
        campaings_df = grouped.copy()
        grouped = filtered_df.groupby(['PLATFORM', 'START_DATE'])\
            .agg({'AMOUNT_SPENT': 'sum' }).reset_index()
        platform_df = grouped.copy()

        with tab1:
            fig = px.bar(platform_df, x="START_DATE", y="AMOUNT_SPENT", color="PLATFORM") #, color="source"
            
            fig.update_layout(
                xaxis_title='Date',
                yaxis_title='Expenses',
            )
            st.plotly_chart(fig, use_container_width=True)
        with tab2:
            fig = px.bar(campaings_df, x="START_DATE", y="AMOUNT_SPENT", color="CAMPAIGN_NAME") #, color="source"
            
            fig.update_layout(
                xaxis_title='Date',
                yaxis_title='Expenses',
            )
            st.plotly_chart(fig, use_container_width=True)