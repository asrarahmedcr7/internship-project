from django.shortcuts import render
from django.db import connection
import pandas as pd
from django.http import HttpResponse
import psycopg2
from django.conf import settings


def uploadToDatabase(conn, df, path_to_csv_file, table_name):

    # Extracting columns
    columns_sql = ', '.join([f'"{column_name}" TEXT' for column_name in df.columns])
    print('column names:', columns_sql)

    with conn.cursor() as cursor:

        # Create the table if it doesn't already exist
        create_table_sql = f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            id SERIAL PRIMARY KEY,
            {columns_sql}
        );
        '''
        cursor.execute(create_table_sql)

        # Copy data from CSV file
        with open(path_to_csv_file, 'r') as f:
            copy_sql = f"COPY \"{table_name}\" FROM STDIN WITH CSV HEADER DELIMITER ','"
            cursor.copy_expert(copy_sql, f)

        conn.commit()

def evaluate_result(client_actual, api_predicted, client_table_name, api_table_name, positive, negative):

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
            SELECT C.id, C."{client_actual}", A."{api_predicted}"
            FROM "{client_table_name}" as C JOIN "{api_table_name}" as A
            ON C.id = A.id;
            '''
    
    df = pd.read_sql_query(query, connection)
    df['Observation type'] = df.apply(classify_row, axis=1)

    output_path = './data/result.csv'
    df.to_csv(output_path, index=False)
    print(f"CSV file created at: {output_path}")

def script(request):

    # Open a raw psycopg2 connection using Django's database settings
    conn = psycopg2.connect(
        dbname=settings.DATABASES['default']['NAME'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT'],
    )

    # Load the excel file
    file_path = r'data/Evalio Sample Data.xlsx' # Replace with the actual path
    df = pd.read_excel(file_path, sheet_name = None) 
    df['Base - Actual'].to_csv('data/client_data.csv', index=True, header=False)
    uploadToDatabase(conn, df['Base - Actual'], 'data/client_data.csv', 'Client Data')
    df['Base - Predicted'].to_csv('data/api_data.csv', index=True, header=False)
    uploadToDatabase(conn, df['Base - Predicted'], 'data/api_data.csv', 'API Data')
    conn.close()

    evaluate_result(client_actual = 'Auth_Actual', api_predicted = 'Auth_Pred', 
                    client_table_name = 'Client Data', api_table_name= 'API Data', 
                    positive = 'Suspect', negative = 'Genuine')

    return HttpResponse()