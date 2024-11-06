import psycopg2
import pandas as pd
from django.conf import settings

def generatePivot(result_table_name):
    conn = psycopg2.connect(
            dbname='hrness',
            user='postgres',
            password='Asrarahmed@7860',
            host='localhost',
            port='5432',
        )
    
    sql = f''' SELECT "Date", "Observation type", COUNT(*) AS count
            FROM "{result_table_name}"
            GROUP BY "Date", "Observation type"
            ORDER BY "Date", "Observation type";
            '''
    
    df = pd.read_sql_query(sql, conn)
    df.to_csv('../../data/pivot.csv', index=False)
    print("Pivot generated successfully")
    conn.close()

generatePivot('Result')