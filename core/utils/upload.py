from django.db import connection
import pandas as pd

def createTable(conn, df, table_name, primary_key):

    # To store the values in their respective formats
    dtype_mapping = {
        'int64': 'INTEGER',
        'float64': 'FLOAT',
        'object': 'TEXT',
        'bool': 'BOOLEAN',
        'datetime64[ns]': 'TIMESTAMP',
        'timedelta64[ns]': 'INTERVAL'
    }

    # Extracting columns
    columns_sql = ', '.join([f'"{column_name}" {dtype_mapping.get(str(df[column_name].dtype))} {"PRIMARY KEY" if column_name == primary_key else ""}' for column_name in df.columns])

    with conn.cursor() as cursor:

        # Create the table if it doesn't already exist
        create_table_sql = f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            {columns_sql}
        );
        '''
        cursor.execute(create_table_sql)
        print(f'{table_name} created successfully.')

def uploadCsvToDatabase(conn, path_to_csv_file, table_name):

    with conn.cursor() as cursor:

        # Copy data from CSV file
        with open(path_to_csv_file, 'r') as f:
            copy_sql = f"COPY \"{table_name}\" FROM STDIN WITH CSV HEADER DELIMITER ','"
            cursor.copy_expert(copy_sql, f)
        conn.commit()
        print(f'Values inserted into {table_name}')

def evaluate_result(conn, client_actual, api_predicted, client_table_name, api_table_name, positive, negative, client_id, engagement_id):

    def classify_row(row):
        if row[client_actual] == positive and row[api_predicted] == positive:
            return 'True Positive'
        elif row[client_actual] == negative and row[api_predicted] == negative:
            return 'True Negative'
        elif row[client_actual] == negative and row[api_predicted] == positive:
            return 'False Positive'
        else:
            return 'False Negative'

    query = f'''
            SELECT C."Candidate ID", C."Date", C."{client_actual}", A."{api_predicted}"
            FROM "{client_table_name}" as C JOIN "{api_table_name}" as A
            ON C."Candidate ID" = A."Candidate ID";
            '''
    
    df = pd.read_sql_query(query, conn)
    df['Observation type'] = df.apply(classify_row, axis=1)

    output_path = f'./data/result-{client_id}-{engagement_id}.csv'
    df.to_csv(output_path, index=False)

    createTable(conn=conn, df=df, table_name=f'Result-{client_id}-{engagement_id}', primary_key='Candidate ID')
    uploadCsvToDatabase(conn=conn, path_to_csv_file=f'data/result-{client_id}-{engagement_id}.csv', table_name=f'Result-{client_id}-{engagement_id}')

    print(f'Result generated and uploaded to database.')
