import  snowflake.connector
import ast
import pandas as pd



def insert_rows_to_snowflake(df):
    my_cnx = snowflake.connector.connect(
    user = "KEBOOLA_WORKSPACE_611037349",
    password = "35zWKbK2rsWeY7q63zZhy6EEHh4PAawM" ,
    account = "keboola.eu-central-1",
    warehouse = "KEBOOLA_PROD_SMALL",
    database = "KEBOOLA_3730",
    schema = "WORKSPACE_611037349")
    # Cursor for Snowflake
    with my_cnx.cursor() as cur:
        for _, row in df.iterrows():
            client = row['Client']
            budget = row['Budget_name']
            amount = row['Budget amount']
            currency = row['Currency']
            since = row['Since date']
            until = row['Until date']
            campaigns_string = ",".join(row['Campaings']).replace("'", "''")  # Convert the list to a comma-separated string and escape any single quotes

            # SQL statement
            sql = (f"INSERT INTO KEBOOLA_3730.WORKSPACE_611037349.campaing_budget "
                   f"(client, budget, budget_amount, currency, since_date, until_date, campaings) "
                   f"SELECT '{client}', '{budget}', {amount}, '{currency}', '{since}', '{until}', "
                   f"SPLIT('{campaigns_string}', ',') AS campaings;")
            
            # Execute the SQL
            cur.execute(sql)
 
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
        df['CAMPAINGS'] = df['CAMPAINGS'].apply(lambda x: ast.literal_eval(x.strip()) if isinstance(x, str) else x)
        cur.close()
    return df