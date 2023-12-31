import snowflake.connector
import ast
import pandas as pd
import os
from kbcstorage.client import Client
import streamlit as st
import types
import csv


def insert_rows_to_table(row):
    my_cnx = snowflake.connector.connect(
        user="KEBOOLA_WORKSPACE_611037349",
        password="35zWKbK2rsWeY7q63zZhy6EEHh4PAawM",
        account="keboola.eu-central-1",
        warehouse="KEBOOLA_PROD_SMALL",
        database="KEBOOLA_3730",
        schema="WORKSPACE_611037349"
    )
    
    # Extract data from Series
    src_id = row['client'] + "-" + row['budget']
    client = row['client']
    budget = row['budget']
    amount = row['budget_amount']
    currency = row['currency']
    since = row['since_date']
    until = row['until_date']
    campaigns_string = ",".join(row['campaigns']).replace("'", "''")  # Convert the list to a comma-separated string and escape any single quotes
    
    # SQL statement
    sql = (f"INSERT INTO KEBOOLA_3730.WORKSPACE_611037349.campaing_budget "
           f"""("src_id", "client", "budget", "budget_amount", "currency", "since_date", "until_date", "campaigns") """
           f"SELECT '{src_id}' , '{client}', '{budget}', {amount}, '{currency}', '{since}', '{until}', "
           f"""SPLIT('{campaigns_string}', ',') AS "campaigns";""")

    # Cursor for Snowflake and Execute the SQL
    with my_cnx.cursor() as cur:
        cur.execute(sql)

    my_cnx.close()
    print("Success")

def fetch_data_from_sf():
    my_cnx = snowflake.connector.connect(
    user = "KEBOOLA_WORKSPACE_611037349",
    password = "35zWKbK2rsWeY7q63zZhy6EEHh4PAawM" ,
    account = "keboola.eu-central-1",
    warehouse = "KEBOOLA_PROD_SMALL",
    database = "KEBOOLA_3730",
    schema = "WORKSPACE_611037349")
    with my_cnx as cur:
        # SQL query to fetch data
        query = "SELECT * FROM KEBOOLA_3730.WORKSPACE_611037349.campaing_budget;"

        # Fetch data and transform into DataFrame
        df = pd.read_sql(query, cur)

        # Process the Campaings column
        df['campaigns'] = df['campaigns'].apply(lambda x: ast.literal_eval(x.strip()) if isinstance(x, str) else x)
        cur.close()
    return df

def fetch_data_from_snowflake():
    file_path = "/data/in/tables/campaign_budget.csv"
    
    df = pd.read_csv(file_path)
    changed_column = []
    for str in df['campaigns']:
        changed_column.append(campaign.strip() for campaign in str.split(','))
    df['campaigns'] = changed_column
    df['campaigns'] = df['campaigns'].apply(lambda x: list(x) if isinstance(x, types.GeneratorType) else x)
    
    # Process the Campaigns column
    #df['campaigns'] = df['campaigns'].apply(lambda x: ast.literal_eval(x.strip()) if isinstance(x, str) else x)
    return df

def get_dataframe(kbc_url, kbc_token):
    
    # kbc_url ="https://connection.eu-central-1.keboola.com"
    # kbc_token = "3730-490298-T3r89ADkBQIR2g7AnsaclUmEx0XMTztEw98Rm6NH"
    client = Client(kbc_url, kbc_token)

    table_detail = client.tables.detail('out.c-Marketing_cash_flow.campaign_budget')

    client.tables.export_to_file(table_id = 'out.c-Marketing_cash_flow.campaign_budget', path_name='')
    list = client.tables.list()
    with open('./' + table_detail['name'], mode='rt', encoding='utf-8') as in_file:
        lazy_lines = (line.replace('\0', '') for line in in_file)
        reader = csv.reader(lazy_lines, lineterminator='\n')
    if os.path.exists('data.csv'):
        os.remove('data.csv')
    else:
        print("The file does not exist")
    os.rename(table_detail['name'], 'data.csv')
    df = pd.read_csv('data.csv')
    changed_column = []
    #df['campaigns'] = df['campaigns'].apply(lambda x: str(x) if isinstance(x, types.GeneratorType) else x)
    for str in df['campaigns']:
        changed_column.append(campaign.strip() for campaign in str.split(','))
    df['campaigns'] = changed_column
    #df['campaigns'] = df['campaigns'].apply(lambda x: list(x) if isinstance(x, types.GeneratorType) else x)
    return df


def insert_rows_to_snowflake(row,kbc_url, kbc_token):
    # kbc_url ="https://connection.eu-central-1.keboola.com"
    # kbc_token = "3730-490298-T3r89ADkBQIR2g7AnsaclUmEx0XMTztEw98Rm6NH"
    client_kbc = Client(kbc_url, kbc_token)
     # Extract data from Series
    src_id = row['client'] + "-" + row['budget']
    client = row['client']
    budget = row['budget']
    amount = row['budget_amount']
    currency = row['currency']
    since = row['since_date']
    until = row['until_date']
    campaigns_string = ",".join(row['campaigns']).replace("'", "''")  # Convert the list to a comma-separated string and escape any single quotes



    data_dict = {
        'src_id': src_id,
        'client': client,
        'budget': budget,
        'budget_amount': amount,
        'currency': currency,
        'since_date': since,
        'until_date': until,
        'campaigns': [campaigns_string]
    }
    results = pd.DataFrame(data_dict)
    results.to_csv('./results.csv.gz', index=False, compression='gzip')
    client_kbc.tables.load(table_id='out.c-Marketing_cash_flow.campaign_budget', file_path='./results.csv.gz', is_incremental=True)
    
    print("Success")
 




def delete_row_from_snowflake_by_row_id(id):
    
    my_cnx = snowflake.connector.connect(
        user="KEBOOLA_WORKSPACE_611037349",
        password="35zWKbK2rsWeY7q63zZhy6EEHh4PAawM",
        account="keboola.eu-central-1",
        warehouse="KEBOOLA_PROD_SMALL",
        database="KEBOOLA_3730",
        schema="WORKSPACE_611037349"
    )
    

    # SQL statement to delete a row based on its row_id
    sql = f"""
        DELETE FROM KEBOOLA_3730.WORKSPACE_611037349.campaing_budget 
        WHERE ("src_id") = '{id}';
    """
    # sql = f"""
    #     DELETE FROM KEBOOLA_3730.WORKSPACE_611037349.campaing_budget 
    #     WHERE ("client", "since_date") IN 
    #         (SELECT "client", "since_date"
    #         FROM 
    #             (SELECT "client", "since_date", 
    #                 ROW_NUMBER() OVER (ORDER BY "since_date") AS rownum
    #         FROM KEBOOLA_3730.WORKSPACE_611037349.campaing_budget)
    #     WHERE rownum = {index_to_del});
    #     """
        
        # Execute the SQL
    with my_cnx.cursor() as cur:
        cur.execute(sql)
    
    my_cnx.close()
    print(sql)