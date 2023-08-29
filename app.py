#TODO = csv read budgets and show over the limit 
#TODO utracena % z kamp


import streamlit as st
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

from my_package.style import css_style
from my_package.html import html_code, html_footer, title


st.set_page_config(layout="wide")
#file_path = "/data/in/tables/input_table.csv"
file_path_local = "data/ads_insight_fact.csv"
df = pd.read_csv(file_path_local)
#CREATED_DATE	start_date	MODIFIED_DATE	END_DATE
df["created_date"] = pd.to_datetime(df["created_date"]).dt.date
df["start_date"] = pd.to_datetime(df["start_date"]).dt.date
df["modified_date"] = pd.to_datetime(df["modified_date"]).dt.date
df["end_date"] = pd.to_datetime(df["end_date"]).dt.date


df["impressions"] = pd.to_numeric(df["impressions"])
df["link_clicks"] = pd.to_numeric(df["link_clicks"])
df['start_date'] = pd.to_datetime(df['start_date'])
df['campaign_name'] = df.apply(lambda row: row['platform_id'][:9] + '-' + row['campaign_name'], axis=1)


app_mode = st.sidebar.selectbox('Select Page',['Expenses','Analytics']) #two pages
distinct_campaigns = df['campaign_name'].unique()
distinct_source = df["platform_id"].unique()
 # Get current month and year
current_month = datetime.datetime.now().month
current_year = datetime.datetime.now().year
current_day = datetime.datetime.now().day
current_date = pd.to_datetime(date.today().strftime('%Y-%m-%d'))

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
        
        
        filtered_df = df[(df['start_date'] >= since_date) & (df['start_date'] <= until_date)]
        
        if len(st.session_state.source) != 0:
            filtered_df = filtered_df[filtered_df['platform_id'].isin(st.session_state.source)]

        if len(st.session_state.campaign) != 0:
            filtered_df = filtered_df[filtered_df['campaign_name'].isin(st.session_state.campaign)]

        st.markdown(title["charts"], unsafe_allow_html=True)
        tab1, tab2, tab3, tab4 = st.tabs(["Best performing Campaigns","Visualizations per Campaigns","Visualizations per platform_id", "Raw data"])
        grouped = filtered_df.groupby(['campaign_name', 'start_date']).agg({'link_clicks': 'sum', 'impressions': 'sum'}).reset_index()
        grouped['ctr'] = (grouped['link_clicks'] / grouped['impressions']) * 100
        campaings_df = grouped.copy()
        max_campaign = campaings_df["ctr"].max()
        #max_campaign = campaings_df["ctr"].max()
        with tab1:
            st.markdown(title["topcampains"], unsafe_allow_html=True)
            df_top_campaing =  filtered_df.groupby(['platform_id','campaign_name', 'start_date']).agg({'impressions': 'sum', 'link_clicks': 'sum', }).reset_index()
            st.write(df_top_campaing.head(5))
            col1, col2 = st.columns(2)
            ctr_mean = round(np.mean(filtered_df["ctr"]),2)*100
            col1.metric("Average Clickthrough rate", str(ctr_mean) + ' %')
            target_value = col1.slider('Target Clickthrough Rate', 0, 100, 40)
            
           

            fig = px.bar(x=[ctr_mean],
             y=['ctr'],
             orientation='h',
             labels={'x': '%', 'y': ''},
             title='Average Clickthrough rate')
            fig.update_layout(xaxis=dict(range=[0, 100]),height=200)
            fig.update_traces(marker_color='rgb(255, 75, 75)')
            fig.add_annotation(x=ctr_mean * 100, y='ctr', 
                   text=f"{ctr_mean * 100:.2f}%",  # format the number to 2 decimal places
                   showarrow=False,
                   yshift=20)
            fig.add_shape(type="line", 
              x0=target_value, y0=0, x1=target_value, y1=1,
              line=dict(color='rgb(64, 224, 208)', width=6),
              xref='x', yref='paper')
            col1.plotly_chart(fig, use_container_width=True)
            
            cpm_mean = round(np.mean(filtered_df["cpm"]),2)
            max_cpm = np.max(filtered_df["cpm"])
            col2.metric("Cost per mille", str(cpm_mean) + ' EUR')
            cpm_mean = round(np.mean(filtered_df["cpm"]),2)
            max_cpm_range= cpm_mean + 10
            fig = px.bar(x=[cpm_mean],
                        y=['cpm'],
                        orientation='h',
                        labels={'x': 'EUR', 'y': ''},
                        title='Average Clickthrough rate')
            fig.update_layout(xaxis=dict(range=[0, max_cpm_range]),height=200)
            fig.update_traces(marker_color='rgb(255, 75, 75)')
            fig.add_annotation(x=cpm_mean, y='cpm', 
                            text=f"{cpm_mean:.2f} EUR" ,  # format the number to 2 decimal places
                            showarrow=False,
                            yshift=20)

            col2.plotly_chart(fig, use_container_width=True)
            
           

            

        with tab2:
            # # Display title for the "Campaigns" section
            st.markdown(title["impressions"], unsafe_allow_html=True)
            fig = px.bar(campaings_df, x="start_date", y="impressions", color="campaign_name")
            #st.bar_chart(data = campaings_df, x="start_date", y="impressions",use_container_width=True)
            # fig = px.bar(campaings_df, x="start_date", y="impressions", color="campaign_name") # , color="source"
            fig.update_layout(xaxis_title='Date', yaxis_title='impressions')
            # # Display the bar chart
            st.plotly_chart(fig, use_container_width=False)

            # Clicks
            st.markdown(title["clicks"], unsafe_allow_html=True)
            fig = px.bar(campaings_df, x="start_date", y="link_clicks", color="campaign_name") # , color="source"
            fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Clicks',
            )
            # Display the bar chart
            st.plotly_chart(fig, use_container_width=True)

            st.markdown(title["clicktr"], unsafe_allow_html=True)
            fig = px.line(campaings_df, x="start_date", y="ctr", color="campaign_name") #, color="source"

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
    ##################
    # Filter section #
    ##################
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
                selected_sources = st.sidebar.multiselect('Select a platform_id:',
                                                distinct_source, default=None, placeholder="All platform_ids", key="source")
            
            with col12:
                selected_campaigns = st.sidebar.multiselect('Select a campaign:',
                                                    distinct_campaigns, default=None, placeholder="All campaigns", key="campaign") 
        
        since_date = pd.Timestamp(st.session_state.since_date)
        until_date = pd.Timestamp(st.session_state.until_date)
        filtered_df = df[(df['start_date'] >= since_date) & (df['start_date'] <= until_date)]

        ###################
        # Metrics section #
        ###################
        
        
        
        #Columns and data creation

        df_current_month = df[(df['start_date'] >= (current_date - timedelta(days=30))) & (df['start_date'] <= current_date)]
        df_last_month = df[(df['start_date'] >= (current_date - timedelta(days=60))) & (df['start_date'] <= (current_date - timedelta(days=60)))]#TODO change to current month
        df_filtered_months = df[(df['start_date'] >= (current_date - timedelta(days=150))) & (df['start_date'] <= current_date)]
        df_filtered_months["month_column"]  = df_filtered_months.start_date.dt.month
        df_filtered_months["month_name"]  = df_filtered_months.start_date.dt.strftime("%B")
        spend_current_month = round(np.sum(df_current_month["spent_amount"]),2)
        spend_last_month = round(np.sum(df_last_month["spent_amount"]),2) #TODO
        current_month_name = datetime.datetime.now().strftime("%B")
        months_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        if len(st.session_state.source) != 0:
            df_filtered_months = df_filtered_months[df_filtered_months['platform_id'].isin(st.session_state.source)]

        if len(st.session_state.campaign) != 0:
            df_filtered_months = df_filtered_months[df_filtered_months['campaign_name'].isin(st.session_state.campaign)]
        
        # Columns for metrics 

        col1, col2 = st.columns(2)
        
        # Column 1 
       

        target_value = col1.number_input('Target Spend Amount')  
        col1.metric("Spend this month", str(spend_current_month) + ' EUR')#TODO - devision by 0 , str(spend_current_month/spend_current_month)

        # Initialize the figure
        fig = go.Figure()
        try:
            month_spend = df_filtered_months.groupby(['month_name']).agg({'spent_amount': 'sum'}).reset_index()
            month_spend['month_name'] = pd.Categorical(month_spend['month_name'], categories=months_order, ordered=True)

            # Sort the dataframe by 'month_name'
            month_spend = month_spend.sort_values('month_name').reset_index(drop=True)
            if  month_spend.empty:
                col1.error("Please check filters - Selected platform does not have selected campaigns")  
            else:
                # Add the bars
                for index, row in month_spend.iterrows():
                    fig.add_trace(go.Bar(
                        x=[row['spent_amount']],
                        y=[row['month_name']],
                        orientation='h',
                        text=[row['spent_amount']],  # this will be the individual value now
                        textposition='outside',
                        marker_color=px.colors.qualitative.Plotly[index % len(px.colors.qualitative.Plotly)]  # cycling through colors
                    ))

                fig.update_layout(title='Last five month spendings',
                                xaxis=dict(range=[0, max(month_spend["spent_amount"])*1.15], title='Spend in EUR', showgrid=True),
                                yaxis_title='Month',
                                showlegend=False)

                fig.add_shape(type="line", 
                            x0=target_value, y0=0, x1=target_value, y1=1,
                            line=dict(color='rgb(64, 224, 208)', width=3),
                            xref='x', yref='paper')
        
                col1.plotly_chart(fig, use_container_width=True)
        except URLError as e:
            st.error()        

        # Column 2 
        
        platform_id_spend = df_current_month.groupby(['platform_id']).agg({'spent_amount': 'sum'}).reset_index()

        target_value_platform_id = col2.number_input('Target Spend Amount For platform_id')  
        col2.metric("Average Spend By platform_id", str(round(np.mean(platform_id_spend["spent_amount"]),2)) + ' EUR') 


        fig_spend = go.Figure()

        # Add the bars
        for index, row in platform_id_spend.iterrows():
            fig_spend.add_trace(go.Bar(
                x=[row['spent_amount']],
                y=[row['platform_id']],
                orientation='h',
                text=[row['spent_amount']],  # this will be individual value now
                textposition='outside',
                marker_color=px.colors.qualitative.Plotly[index % len(px.colors.qualitative.Plotly)]  # cycling through colors
            ))

        fig_spend.update_layout(title='Current month expanses by platform_id',
                                xaxis=dict(range=[0, spend_current_month*1.15], title='EUR'),
                                yaxis_title='',
                                showlegend=False)

        fig_spend.add_shape(type="line", 
                            x0=target_value_platform_id, y0=0, x1=target_value_platform_id, y1=1,
                            line=dict(color='rgb(64, 224, 208)', width=6),
                            xref='x', yref='paper')



        col2.plotly_chart(fig_spend, use_container_width=True)

        # Column 3  - Campaigns abobve the budget, where budget comes from csv file #TODO
       
        #campaign_limit = st.number_input('Set a campaign limit')
        campains_grouped_budget = df_current_month.groupby(['campaign_name']).agg({'spent_amount': 'sum'}).reset_index() 
        campains_grouped_budget["budget"] = np.nan
        edited_df = st.data_editor(campains_grouped_budget, num_rows="dynamic")
        campaigns_above_budget = edited_df[edited_df['spent_amount'] > edited_df['budget']]
        
        col1, col2 = st.columns(2)
        
        col1.metric("Number of campaigns above the limit ", '❗' + str(campaigns_above_budget.shape[0]) + ' Campaigns above budget') #TODO 
        col1.write(campaigns_above_budget.rename(columns={"campaign_name": "Campaign", "spent_amount": "Spendings"}))

        if col1.button('Generate plot'):
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=campaigns_above_budget['campaign_name'],
                x=campaigns_above_budget['spent_amount'],
                orientation='h',
                name='Cost',
                marker_color='red',
                text=campaigns_above_budget['spent_amount'], # <-- Add text values here
                textposition='outside'
            ))

            # Add Budget bars
            fig.add_trace(go.Bar(
                y=campaigns_above_budget['campaign_name'],
                x=campaigns_above_budget['budget'],
                orientation='h',
                name='Budget',
                marker_color='blue',
                text=campaigns_above_budget['budget'], # <-- Add text values here
                textposition='outside' # <-- Specify text position
            ))

            # Update layout
            fig.update_layout(
                title='Campaign Cost vs Budget',
                xaxis_title='Value',
                yaxis_title='Campaign Name',
                barmode='group'
            )


            
            col2.plotly_chart(fig, use_container_width=True)



        ####################
        # Charts  sections #
        ####################
        tab1, tab2 = st.tabs(["Expenses per platform_id","Expenses per Campaign"])
        try:

            if len(st.session_state.source) != 0:
                filtered_df = filtered_df[filtered_df['platform_id'].isin(st.session_state.source)]

            if len(st.session_state.campaign) != 0:
                filtered_df = filtered_df[filtered_df['campaign_name'].isin(st.session_state.campaign)]
            if  filtered_df.empty:
                st.error("Please check filters - Selected platform does not have selected campaigns")
            else:
                grouped = filtered_df.groupby(['campaign_name', 'start_date'])\
                    .agg({'spent_amount': 'sum' }).reset_index()
                campaings_df = grouped.copy()
                grouped = filtered_df.groupby(['platform_id', 'start_date'])\
                    .agg({'spent_amount': 'sum' }).reset_index()
                platform_id_df = grouped.copy()

                with tab1:
                    fig = px.bar(platform_id_df, x="start_date", y="spent_amount", color="platform_id") #, color="source"
                    
                    fig.update_layout(
                        xaxis_title='Date',
                        yaxis_title='Expenses',
                    )
                    st.plotly_chart(fig, use_container_width=True)
                with tab2:
                    fig = px.bar(campaings_df, x="start_date", y="spent_amount", color="campaign_name") #, color="source"
                    
                    fig.update_layout(
                        xaxis_title='Date',
                        yaxis_title='Expenses'
                        
                    )
                    st.plotly_chart(fig, use_container_width=True)
        except URLError as e:
            st.error()    

            # try:
            #     fruit_choice = st.text_input('What fruit would you like information about?')
            #     if not fruit_choice:
            #         st.error("Please select a fruit to get information.")
            #     else:
            #         data= get_fruityvice_data(fruit_choice)
            #         st.dataframe(data)
            #     #streamlit.write('The user entered ', fruit_choice)
            # except URLError as e:
            # st.error()