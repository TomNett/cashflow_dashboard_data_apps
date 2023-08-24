import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime


st.set_page_config(layout="wide")
file_path = "/data/in/tables/input_table.csv"
file_path_local = "data_apps/data/data.csv"

df = pd.read_csv(file_path_local)
print(df)

app_mode = st.sidebar.selectbox('Select Page',['Expenses','Analytics']) #two pages

if app_mode=='Expenses':    
    st.title('Expenses overview')
    with st.container():
        st.text(filter)
        # Extract unique values for campaigns and domains
        distinct_campaigns = df['CAMPAIGN_NAME'].unique()
        distinct_source = df["PLATFORM"].unique()
        
        # Create two columns for filter controls
        col1, col2 = st.columns((1.5, 1.5))
        col11,col12,col13 = st.columns((1,1,1))
        
        # Get current month and year
        current_month = datetime.datetime.now().month
        current_year = datetime.datetime.now().year
        st.stop()
elif app_mode == 'Analytics': 
     st.title('Analytical page')