import psycopg2
import pandas as pd
from django.conf import settings
from client.utils.calculations import findAccuracy, findTPR, findTotal, fillLevels, fillRiskPriorityNumbers, findDemographicParity

def generateDateWisePivot(result_table_name):
    conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
        )
    
    date_wise_observations_sql = f''' SELECT "Date", "Observation type", COUNT(*) AS count
            FROM "{result_table_name}"
            GROUP BY "Date", "Observation type"
            ORDER BY "Date", "Observation type";
            '''
    
    df = pd.read_sql_query(date_wise_observations_sql, conn)
    date_wise_observations = df.groupby('Date').apply(lambda x: x.set_index('Observation type')['count'].to_dict()).to_dict()
    
    for date in date_wise_observations:
        date_wise_observations[date]['Overall Accuracy'] = findAccuracy(date_wise_observations[date])
        date_wise_observations[date]['TPR'] = findTPR(date_wise_observations[date])
        date_wise_observations[date]['Total'] = findTotal(date_wise_observations[date])
    
    conn.close()
    print("DateWisePivot generated successfully")
    return date_wise_observations


def generateLocationWisePivot(result_table_name, client_table_name, primary_key):

    conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
        )

    location_wise_observations_sql = f''' SELECT "Location", "Observation type", COUNT(*) AS count
            FROM "{result_table_name}" JOIN "{client_table_name}" ON "{result_table_name}"."{primary_key}" = "{client_table_name}"."{primary_key}"
            GROUP BY "Location", "Observation type";
            '''
    df = pd.read_sql_query(location_wise_observations_sql, conn)
    location_wise_observations = df.groupby("Location").apply(lambda x: x.set_index('Observation type')['count'].to_dict()).to_dict()
    for location in location_wise_observations:
        location_wise_observations[location]['Overall Accuracy'] = findAccuracy(location_wise_observations[location])
        location_wise_observations[location]['Total'] = findTotal(location_wise_observations[location])
    
    location_wise_observations = fillLevels(location_wise_observations)
    location_wise_observations = fillRiskPriorityNumbers(location_wise_observations)
  
    sorted_location_wise_observations = {}
    for key in sorted(location_wise_observations, key = lambda location: location_wise_observations[location]['Risk Priority Number'], reverse = True):
        sorted_location_wise_observations[key] = location_wise_observations[key]
    
    print("LocationWisePivot generated successfully")
    
    return sorted_location_wise_observations

def generateGenderWisePivot(client_table_name, result_table_name, primary_key):

    conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
        )
    
    gender_wise_observations_sql = f"""
    SELECT 
        "{result_table_name}"."Date",
        "Gender",
        "Observation type",
        COUNT(*) AS count FROM "{result_table_name}" JOIN "{client_table_name}" ON "{result_table_name}"."{primary_key}" = "{client_table_name}"."{primary_key}"
    GROUP BY 
        "{result_table_name}"."Date", "Gender", "Observation type"
    ORDER BY 
        "{result_table_name}"."Date", "Gender";
    """

    # Read the query result into a Pandas DataFrame
    df = pd.read_sql_query(gender_wise_observations_sql, conn)
    df.to_csv('test.csv')

    # Convert the DataFrame to the nested dictionary format
    result_dict = {}
    for _, row in df.iterrows():
        gender = row['Gender']
        date = row['Date']
        
        if gender not in result_dict:
            result_dict[gender] = {}
        if date not in result_dict[gender]:
            result_dict[gender][date] = {'True Positive':0, 'True Negative':0, 'False Positive':0, 'False Negative':0}

        # Populate each Observation type with its count, defaulting to 0 if not present
        if row['Observation type'] not in result_dict[gender][date]:
            result_dict[gender][date][row['Observation type']] = 0
        result_dict[gender][date][row['Observation type']] += row['count']

    for gender in result_dict:
        for date in result_dict[gender]:
            result_dict[gender][date]['Total'] = findTotal(result_dict[gender][date])
            result_dict[gender][date]['Demographic Parity'] = findDemographicParity(result_dict[gender][date])
            result_dict[gender][date]['Accuracy'] = findAccuracy(result_dict[gender][date])

    conn.close()
    print("GenderWisePivot generated successfully")
    return result_dict