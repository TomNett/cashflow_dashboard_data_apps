import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime

from my_package.style import css_style
from my_package.html import html_code, html_footer, title, logo_html


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

app_mode = st.sidebar.selectbox('Select Page',['Expenses','Analytics']) #two pages

if app_mode=='Expenses':
    with st.container():
       st.markdown(f"{logo_html}", unsafe_allow_html=True)
       st.title("Expenses overview")    
    
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