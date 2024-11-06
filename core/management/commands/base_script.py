import os
from django.core.management.base import BaseCommand, CommandError
import psycopg2
import pandas as pd
from django.conf import settings
from core.utils import uploadCsvToDatabase, createTable, evaluate_result

class Command(BaseCommand):
    help = 'Processes a file given its path'

    def add_arguments(self, parser):
        # Adding the file path argument
        parser.add_argument(
            '--file', type=str, required=True, help='Path to the file to process'
        )

    def handle(self, *args, **options):

        file_path = options['file']
        
        # Check if the file exists
        if not os.path.isfile(file_path):
            raise CommandError(f"File '{file_path}' does not exist.")
        
        # Open a raw psycopg2 connection using Django's database settings
        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
        )

        # Load the excel file
        df = pd.read_excel(file_path, sheet_name = None)

        client_sheet = df['Base - Actual']
        API_sheet = df['Base - Predicted']
        client_sheet = client_sheet.drop_duplicates(subset='Candidate ID', keep = 'first')
        API_sheet = API_sheet.drop_duplicates(subset='Candidate ID', keep = 'first')

        createTable(conn = conn, df = client_sheet, table_name = 'Client Data', primary_key = 'Candidate ID')
        createTable(conn = conn, df = API_sheet, table_name = 'API Data', primary_key = 'Candidate ID')

        client_sheet.to_csv('data/client_data.csv', index=False, header=False)
        uploadCsvToDatabase(conn = conn, path_to_csv_file = 'data/client_data.csv', table_name = 'Client Data')
        
        API_sheet.to_csv('data/api_data.csv', index=False, header=False)
        uploadCsvToDatabase(conn = conn, path_to_csv_file = 'data/api_data.csv', table_name = 'API Data')

        evaluate_result(conn=conn, client_actual = 'Auth_Actual', api_predicted = 'Auth_Pred', 
                        client_table_name = 'Client Data', api_table_name= 'API Data', 
                        positive = 'Suspect', negative = 'Genuine')
        
        
        conn.close()