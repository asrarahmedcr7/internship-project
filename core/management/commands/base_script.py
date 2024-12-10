import os
from django.core.management.base import BaseCommand, CommandError
import psycopg2
import pandas as pd
from django.conf import settings
from core.utils import uploadCsvToDatabase, createTable, evaluate_result, evaluate_result_regression

class Command(BaseCommand):
    help = 'Processes a file given its path'

    def add_arguments(self, parser):
        # Adding the file path argument
        parser.add_argument(
            '--file', type=str, required=True, help='Path to the file to process',
        )
        parser.add_argument(
            '--clientID', type=str,required=True, help='Client ID for table'
        )
        parser.add_argument(
            '--engagementID', type=str,required=True, help='Engagement ID for table'
        )
        parser.add_argument(
            '--engagementType', type=str,required=True, help='Engagement Type for table'
        )

    def handle(self, *args, **options):

        file_path = options['file']
        client_id = options['clientID']
        engagement_id = options['engagementID']
        engagement_type = options['engagementType']
        
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

        if engagement_type.lower() == 'regression':
            df = pd.read_csv(file_path)
            df['Residual'] = abs(df['Actual_Compensation'] - df['Predicted_Compensation'])
            createTable(conn=conn, df=df, table_name=f'Client Data-{client_id}-{engagement_id}', primary_key = 'Candidate_ID')
            df.to_csv(f'data/client_data-{client_id}-{engagement_id}.csv', index=False, header=False)
            uploadCsvToDatabase(conn = conn, path_to_csv_file = f'data/client_data-{client_id}-{engagement_id}.csv', table_name = f'Client Data-{client_id}-{engagement_id}')
            evaluate_result_regression(conn=conn, table_name=f'Client Data-{client_id}-{engagement_id}', actual_compensation='Actual_Compensation', predicted_compensation='Predicted_Compensation', client_id=client_id, engagement_id=engagement_id)

        elif engagement_type.lower() == 'classification':
            # Load the excel file
            df = pd.read_excel(file_path, sheet_name = None)

            client_sheet = df['Base - Actual']
            API_sheet = df['Base - Predicted']
            client_sheet = client_sheet.drop_duplicates(subset='Candidate ID', keep = 'first')
            API_sheet = API_sheet.drop_duplicates(subset='Candidate ID', keep = 'first')

            createTable(conn = conn, df = client_sheet, table_name = f'Client Data-{client_id}-{engagement_id}', primary_key = 'Candidate ID')
            createTable(conn = conn, df = API_sheet, table_name = f'API Data-{client_id}-{engagement_id}', primary_key = 'Candidate ID')

            client_sheet.to_csv(f'data/client_data-{client_id}-{engagement_id}.csv', index=False, header=False)
            uploadCsvToDatabase(conn = conn, path_to_csv_file = f'data/client_data-{client_id}-{engagement_id}.csv', table_name = f'Client Data-{client_id}-{engagement_id}')
            
            API_sheet.to_csv(f'data/api_data-{client_id}-{engagement_id}.csv', index=False, header=False)
            uploadCsvToDatabase(conn = conn, path_to_csv_file = f'data/api_data-{client_id}-{engagement_id}.csv', table_name = f'API Data-{client_id}-{engagement_id}')

            evaluate_result(conn=conn, client_actual = 'Auth_Actual', api_predicted = 'Auth_Pred', 
                            client_table_name = f'Client Data-{client_id}-{engagement_id}', api_table_name= f'API Data-{client_id}-{engagement_id}', 
                            positive = 'Suspect', negative = 'Genuine', client_id=client_id, engagement_id=engagement_id)
        
        
        conn.close()