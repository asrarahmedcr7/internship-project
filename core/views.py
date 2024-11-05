from django.shortcuts import render
from django.db import connection
import pandas as pd
from django.http import HttpResponse
import psycopg2
from django.conf import settings
import numpy as np


def uploadToDatabase(conn, df, path_to_csv_file, table_name, primary_key):

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
    print('column names:', columns_sql)

    with conn.cursor() as cursor:

        # Create the table if it doesn't already exist
        create_table_sql = f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" (
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
            SELECT C."Employee ID", C."{client_actual}", A."{api_predicted}"
            FROM "{client_table_name}" as C JOIN "{api_table_name}" as A
            ON C."Employee ID" = A."Employee ID";
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

    client_sheet = df['Base - Actual']
    API_sheet = df['Base - Predicted']

    client_sheet = client_sheet.drop_duplicates(subset='Employee ID', keep = 'first')
    client_sheet.to_csv('data/client_data.csv', index=False, header=False)
    uploadToDatabase(conn, client_sheet, 'data/client_data.csv', 'Client Data', 'Employee ID')
    
    API_sheet = API_sheet.drop_duplicates(subset='Employee ID', keep = 'first')
    API_sheet.to_csv('data/api_data.csv', index=False, header=False)
    uploadToDatabase(conn, API_sheet, 'data/api_data.csv', 'API Data', 'Employee ID')
    
    conn.close()

    evaluate_result(client_actual = 'Auth_Actual', api_predicted = 'Auth_Pred', 
                    client_table_name = 'Client Data', api_table_name= 'API Data', 
                    positive = 'Suspect', negative = 'Genuine')

    return HttpResponse()