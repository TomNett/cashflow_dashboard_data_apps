import snowflake.connector
import ast
import pandas as pd



def insert_rows_to_snowflake(row):
    my_cnx = snowflake.connector.connect(
    user = "KEBOOLA_WORKSPACE_611037349",
    password = "35zWKbK2rsWeY7q63zZhy6EEHh4PAawM" ,
    account = "keboola.eu-central-1",
    warehouse = "KEBOOLA_PROD_SMALL",
    database = "KEBOOLA_3730",
    schema = "WORKSPACE_611037349")
     # Extract data from Series
    client = row['Client']
    budget = row['Budget']
    amount = row['Budget amount']
    currency = row['Currency']
    since = row['Since date']
    until = row['Until date']
    campaigns_string = ",".join(row['Campaigns']).replace("'", "''")  # Convert the list to a comma-separated string and escape any single quotes

    # SQL statement
    sql = (f"INSERT INTO KEBOOLA_3730.WORKSPACE_611037349.campaing_budget "
                   f"(client, budget, budget_amount, currency, since_date, until_date, campaings) "
                   f"SELECT '{client}', '{budget}', {amount}, '{currency}', '{since}', '{until}', "
                   f"SPLIT('{campaigns_string}', ',') AS campaings;")
                   
            
    # Cursor for Snowflake and Execute the SQL
    with my_cnx.cursor() as cur:
        cur.execute(sql)
    my_cnx.close()
    print("Success")
 
def fetch_data_from_snowflake():
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
        df['CAMPAIGNS'] = df['CAMPAIGNS'].apply(lambda x: ast.literal_eval(x.strip()) if isinstance(x, str) else x)
        cur.close()
    return df



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