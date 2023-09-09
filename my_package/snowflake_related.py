import snowflake.connector
import ast
import pandas as pd
import os
from kbcstorage.client import Client
import streamlit as st




def fetch_data_from_snowflake():
    file_path = "/data/in/tables/campaign_budget.csv"
    
    df = pd.read_csv(file_path)
    changed_column = []
    for str in df['campaigns']:
        changed_column.append(campaign.strip() for campaign in str.split(','))
    df['campaigns'] = changed_column
    # Process the Campaigns column
    #df['campaigns'] = df['campaigns'].apply(lambda x: ast.literal_eval(x.strip()) if isinstance(x, str) else x)
    return df


def insert_rows_to_snowflake(row):
    kbc_url ="https://connection.eu-central-1.keboola.com"
    kbc_token = "3730-490298-T3r89ADkBQIR2g7AnsaclUmEx0XMTztEw98Rm6NH"
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
 




def delete_row_from_snowflake_by_row_id(index):
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
        WHERE (CLIENT, SINCE_DATE) IN 
            (SELECT CLIENT, SINCE_DATE
            FROM 
                (SELECT CLIENT, SINCE_DATE, 
                    ROW_NUMBER() OVER (ORDER BY SINCE_DATE) AS rownum
            FROM KEBOOLA_3730.WORKSPACE_611037349.campaing_budget)
        WHERE rownum = {index});
        """
        
        # Execute the SQL
    with my_cnx.cursor() as cur:
        cur.execute(sql)
    
    my_cnx.close()