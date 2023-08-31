# TODO Dispaly only campaigns, which are not selected 
# TODO filter per client 
# TODO client and budget ( editace)
# TODO filters depending on tabs of page 
# TODO utracena % z kamp
# TODO tabulka budget kterou nalinkuju na kampani

# TODO = csv read budgets and show over the limit 
# TODO scenare pro kampan  - pridat ?
# TODO Vypocet budgetu pro kampan - not needed 
# TODO add columns in snowflake corresponding to client for a futher filtration

# mesice a vypotrebovany budget 
# pak bude analyza konkrenti kampani 



import streamlit as st
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
#import arrow 
#import snowflake.connector 
pd.options.mode.chained_assignment = None  # default='warn'

from my_package.style import apply_css

from my_package.html import html_code, html_footer, title


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
            month_year_list.append(str(y) + '-'+ str(m))
    return month_year_list


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


app_mode = st.sidebar.selectbox('Select Page',['Expenses','Analytics','Campaigns']) #two pages
distinct_campaigns = df['campaign_name'].unique()
distinct_source = df["platform_id"].unique()
 # Get current month and year
current_month = datetime.datetime.now().month
current_year = datetime.datetime.now().year
current_day = datetime.datetime.now().day
current_date = pd.to_datetime(date.today().strftime('%Y-%m-%d'))
current_month_name = datetime.datetime.now().strftime("%B")
current_year_month =str(current_year)  + '-' + current_month_name

months_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

month_year_list = create_month_year_list(months_order, df)

dates = [datetime.datetime.strptime(date, '%Y-%B') for date in month_year_list]

# Separate the list by year
dates_2022 = sorted([date for date in dates if date.year == 2022])
dates_2023 = sorted([date for date in dates if date.year == 2023])

# Find the index of the current month and year in the 2023 list
current_index = dates_2023.index(datetime.datetime(2023, 8, 1))  # 2023-August

# Reorder the 2023 list
ordered_dates_2023 = dates_2023[:current_index + 1] + dates_2023[current_index + 1:]

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
        tab1, tab2, tab3 = st.tabs(["Best performing Campaigns","Visualizations per Campaigns","Raw data" ])
        grouped = filtered_df.groupby(['campaign_name', 'start_date']).agg({'link_clicks': 'sum', 'impressions': 'sum'}).reset_index()
        grouped['ctr'] = (grouped['link_clicks'] / grouped['impressions']) * 100
        campaings_df = grouped.copy()
        max_campaign = campaings_df["ctr"].max()


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
            st.plotly_chart(fig, use_container_width=True)

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
                col11,col12 = st.columns((1.5, 1.5))

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
                filtered_df = df[(df['start_date'] >= since_date) & (df['start_date'] <= until_date)]


                with col11:
                    selected_sources = st.multiselect('Select Platform',
                                                    distinct_source, default=distinct_source, placeholder="Select  platforms from the list", key="source")
                if not selected_sources: 
                    col12.error("Please select a platform.")
                else:     
                    if len(st.session_state.source) != 0:
                        filtered_df = filtered_df[filtered_df['platform_id'].isin(st.session_state.source)]
                        distinct_campaigns_by_platform = filtered_df['campaign_name'].unique()
                        with col12:
                            selected_campaigns = st.multiselect('Select a campaign:',
                                                            distinct_campaigns_by_platform, default=None, placeholder="All campaigns", key="campaign") 
            
                
                

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
                
                current_month_name = datetime.datetime.now().strftime("%B")
                if len(st.session_state.source) != 0:
                    df_filtered_months = df_filtered_months[df_filtered_months['platform_id'].isin(st.session_state.source)]
                
                if (len(st.session_state.campaign) != 0):
                    df_filtered_months = df_filtered_months[df_filtered_months['campaign_name'].isin(st.session_state.campaign)]
                
            except URLError as e:
                    st.error()
        # Columns for metrics 

        col1, col2 = st.columns(2)
        
        # Column 1 
       

        #target_value = col1.number_input('Target Spend Amount')  
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

                # fig.add_shape(type="line", 
                #             x0=target_value, y0=0, x1=target_value, y1=1,
                #             line=dict(color='rgb(64, 224, 208)', width=3),
                #             xref='x', yref='paper')
        
                col1.plotly_chart(fig, use_container_width=True)
        except URLError as e:
            st.error()        

        # Column 2 
        
        platform_id_spend = df_current_month.groupby(['platform_id']).agg({'spent_amount': 'sum'}).reset_index()

        #target_value_platform_id = col2.number_input('Target Spend Amount For platform_id')  
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

        # fig_spend.add_shape(type="line", 
        #                     x0=target_value_platform_id, y0=0, x1=target_value_platform_id, y1=1,
        #                     line=dict(color='rgb(64, 224, 208)', width=6),
        #                     xref='x', yref='paper')



        col2.plotly_chart(fig_spend, use_container_width=True)

        
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


elif app_mode == 'Campaigns':
    
    with st.container():
        col1, col2, col3 = st.columns(3,gap="small")
        with col2:
            st.title("Campaigns overview")
    apply_css()
    with st.expander("Show budget settings"):
        #df_current_month = df[(df['start_date'] >= (current_date - timedelta(days=30))) & (df['start_date'] <= current_date)]
        col1, col2= st.columns(2,gap="small")
        col11,col12 = st.columns((1.5, 1.5))

        col1, col2, col3 = st.columns((2, 1, 1))
    
    
        df['month_name'] = pd.DatetimeIndex(df['start_date']).strftime("%B")
        current_month_name = datetime.datetime.now().strftime("%B")
        
        #############################
        ######## Filters ############
        #############################
       
        try:
            with col11:
                #selected_month = datetime.datetime.now().month
                st.header("Filters: ") 
                default_ix = months_order.index(datetime.datetime.now().strftime("%B"))
                selected_year_month = st.selectbox('Select Year and Month:',
                    ordered_list_year_month, index=default_ix,  placeholder="All months", key="month")
                
                day_count = calendar.monthrange(2023, datetime.datetime.strptime(selected_year_month[5:], '%B').month)[1]
                last_d = str(day_count) + ' ' + selected_year_month[5:] + ', ' + selected_year_month[:4]
                first_d = '1 ' + selected_year_month[5:] + ', 2023'
            def custom_str_to_date(date_str, format_str='%d %B, %Y'):
                return datetime.datetime.strptime(date_str, format_str).date()

            first_date = custom_str_to_date(first_d)
            last_date = custom_str_to_date(last_d)

   
                
            if len(st.session_state.month) != 0:           
                filtered_df = df[(df['start_date'] >= pd.to_datetime(first_date)) & (df['start_date'] <= pd.to_datetime(last_date))]
            with col11:
                selected_sources = st.multiselect('Select Platform:',
                    distinct_source, default=distinct_source, placeholder="All platform_ids", key="source")
            if not selected_sources:
                col11.error("Please select a platform.")
            else:
                if len(st.session_state.source) != 0:
                    filtered_df = filtered_df[filtered_df['platform_id'].isin(st.session_state.source)]
                    
                    distinct_campaigns_by_platform = filtered_df['campaign_name'].unique()
                    col11.subheader('Budget editing :')       
                     

                currency_distinct = ["EUR", "CZK", "USD"]


                # Container for budget df
                # Define column names for the empty dataframe
                columns = ["Client","Budget", "Budget amount","Currency","Since date", "Until date", "Campaings"]
                # Create an empty dataframe with the defined columns
                empty_df = pd.DataFrame(columns=columns)
            
                # Create an empty session state variable
                session_state = st.session_state
                # Check if the session state variable is already defined
                
                if "df" not in session_state:
                    # Assign the initial data to the session state variable
                    session_state.df = empty_df
                    session_state.row = pd.Series(index=columns)
                
                 # Create a selectbox for each column in the current row
                for col in columns:
                #     # Get unique values from the corresponding column in the resource_data dataframe
                    if col == "Client":
                        session_state.row[col] = col11.text_input(col, '',placeholder ='Enter a client name', key=col)
                            
                    elif col == "Budget":
                        session_state.row[col] = col11.text_input(col, '',placeholder ='Enter a budget name', key=col)

                    elif col == "Budget amount":
                        session_state.row[col] = col11.number_input(col, value = 1000)
                    elif col == "Currency":
                        session_state.row[col] = col11.selectbox(col, currency_distinct, index = 0, key='currency_budget')
                    elif col == "Since date":
                        session_state.row[col] = col11.date_input("Select a start date for budget:",
                        datetime.date(current_year, current_month-1, 1), key="since_date_budget")
                    elif col == "Until date":
                        session_state.row[col] = col11.date_input("Select a start date for budget:",
                        datetime.date(current_year, current_month, current_day), key="until_date_budget")    
                    elif col == "Campaings":
                        session_state.row[col] = col11.multiselect('Select a campaign:',
                            distinct_campaigns_by_platform, default=None, placeholder="All campaigns", key="campaign")  
                        
                    
                    

                col1, col2 = st.columns(2)
                    # Add a button to add a new empty row to the dataframe and clear the values of the selectboxes for the current row
                with col12:
                    st.subheader("Entered data preview  : ")
                    st.table(session_state.row)
                    
                    col21, col22,col23, col24, col25 = st.columns((0.3,0.3,0.3,0.3,0.8), gap="small")
                    if col21.button("Add Row"):
                        session_state.df.loc[len(session_state.df)] = session_state.row
                        session_state.row = pd.Series(index=columns)
                    if col22.button("Change Row", key='rowchange'):
                        #TODO
                        print('Hi')
                    if col23.button("Delete Row",key="deleterow"):
                        col11, col12 = st.columns(2)
                        col11.warning("🚨 Specify row you want to be deleted")
                        index_to_delete = col11.number_input('ID of row', value=0)
                        
                        if "delete_pressed" not in session_state:
                            session_state.delete_pressed = False

                        if col11.button("Delete", key="deleter"):
                            session_state.delete_pressed = True

                        if session_state.delete_pressed:
                            session_state.df = delete_row_from_df(session_state.df, index_to_delete)
                            session_state.delete_pressed = False  
                    if col24.button("Clear DF"):
                        session_state.df = empty_df
                col1.header("Budgets and their limits")
                col1.table(session_state.df)
                                        
        except URLError as e:
            st.error()


        

        
        
        
        #st.dataframe(session_state.df)
        #st.data_editor(budget_df, num_rows="static")
    


    #filtered_df = df[(df['start_date'] >= since_date) & (df['start_date'] <= until_date)]
    
    df_last_month = df[(df['start_date'] >= (current_date - timedelta(days=60))) & (df['start_date'] <= (current_date - timedelta(days=60)))]#TODO change to current month
    df_filtered_months = df[(df['start_date'] >= (current_date - timedelta(days=150))) & (df['start_date'] <= current_date)]
    df_filtered_months["month_column"]  = df_filtered_months.start_date.dt.month
    df_filtered_months["month_name"]  = df_filtered_months.start_date.dt.strftime("%B")
    spend_current_month = round(np.sum(filtered_df["spent_amount"]),2)
    spend_last_month = round(np.sum(df_last_month["spent_amount"]),2)

    #Dummy df for representation
    data = {"Client" :["MOL"], "Budget":[1500,], "Campaign":[["FACEBOOK-MOL - link clicks - FB+IG - MOL MOVE kampaň - 05-07/2023", "LINKEDIN-MOL - link clicks - LI - Provozovatelé - 2023"]]}
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
                        """,unsafe_allow_html=True
                    )
            # Create two columns for filter controls
            col1, col2 = st.columns((1.5, 3), gap="large")

            
            with col1:
                col11, col22, col33 = st.columns((1, 2.5, 1.5), gap="small")
                
                # Sample dataframe
                data = {'Client': ['MOL', 'WMC'],
                'Budget': [1500, 1200],
                'Spend': [1300, 900]}
                df = pd.DataFrame(data)
                col1.subheader('Advertising -  total budget Utilization')
                for _, row in df.iterrows():
                    spend_current_month = row['Spend']
                    month_budget = row['Budget']

                    fig = px.bar(x=[spend_current_month],
                                y=[row['Client']],
                                orientation='h',
                                labels={'x': 'EUR', 'y': ''})

                    fig.update_layout(xaxis=dict(range=[0, month_budget]), height=200)
                    fig.update_traces(marker_color='rgb(105, 205, 251)')

                    percentage_spend = spend_current_month/month_budget*100

                    fig.add_annotation(x=spend_current_month,
                                    y=row['Client'],
                                    text=f"{percentage_spend:.2f}%",
                                    showarrow=False,
                                    yshift=10,xshift=30)
                    
                    col1.plotly_chart(fig, use_container_width=True)

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
            with col2:
                fig_spend = go.Figure()
                df_current_month  = filtered_df[(filtered_df[['spent_amount','impressions','cpm']] != 0).all(axis=1)]
                platform_id_spend = df_current_month.groupby(['platform_id']).agg({'spent_amount': 'sum','cpm': 'mean'}).reset_index().sort_values(by='spent_amount', ascending = True)
                
                if platform_id_spend["spent_amount"].empty:
                    max_spend = 0
                else:
                    max_spend = max(platform_id_spend["spent_amount"])
                
                
                col11, col22 = st.columns((1.8,1.5))
                with col11:
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

                    fig_spend.update_layout(title='Current month expanses by platform',
                                            xaxis=dict(range=[0, max_spend*1.30], title='EUR'),
                                            yaxis_title='',
                                            showlegend=False)

                    



                    st.plotly_chart(fig_spend, use_container_width=True)
                with col22:
                    platform_id_spend["spent_amount"] = round(platform_id_spend["spent_amount"],2)
                    st.table(platform_id_spend.rename(columns={"platform_id": "Platform", "spent_amount": "Spendings", "cpm": "CPM"}).sort_values(by='Spendings', ascending = False))
    
    

    # Column 3  - Campaigns abobve the budget, where budget comes from csv file #TODO
    with st.container():   
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




    
    
    

    st.dataframe(filtered_df.head(5)) #TODO tabulka nezarazenych kampani
    st.write(st.session_state)

    

                    




