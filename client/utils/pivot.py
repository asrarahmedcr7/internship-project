import psycopg2
import pandas as pd
from django.conf import settings
from calculations import findAccuracy, findTNR, findTotal, findAccuracyLevel, fillCandidateCountLevels, fillRiskPriorityNumbers

def generatePivot(result_table_name, client_table_name, primary_key):

    conn = psycopg2.connect(
            dbname='hrness',
            user='postgres',
            password='Asrarahmed@7860',
            host='localhost',
            port='5432',
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
        date_wise_observations[date]['TNR'] = findTNR(date_wise_observations[date])
        date_wise_observations[date]['Total'] = findTotal(date_wise_observations[date])

    location_wise_observations_sql = f''' SELECT "Location", "Observation type", COUNT(*) AS count
            FROM "{result_table_name}" JOIN "{client_table_name}" ON "{result_table_name}"."{primary_key}" = "{client_table_name}"."{primary_key}"
            GROUP BY "Location", "Observation type";
            '''
    df = pd.read_sql_query(location_wise_observations_sql, conn)
    location_wise_observations = df.groupby("Location").apply(lambda x: x.set_index('Observation type')['count'].to_dict()).to_dict()
    for location in location_wise_observations:
        location_wise_observations[location]['Overall Accuracy'] = findAccuracy(location_wise_observations[location])
        location_wise_observations[location]['Accuracy Level'] = findAccuracyLevel(location_wise_observations[location]['Overall Accuracy'])
        location_wise_observations[location]['Total'] = findTotal(location_wise_observations[location])
    
    location_wise_observations = fillCandidateCountLevels(location_wise_observations)
    location_wise_observations = fillRiskPriorityNumbers(location_wise_observations)

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

    # Pivot the data so each 'Observation type' becomes a column with counts
    pivot_gender = df.pivot_table(
        index=['Gender', 'Date'],
        columns='Observation type',
        values='count',
        fill_value=0
    ).reset_index()

    # Convert the DataFrame to the nested dictionary format
    result_dict = {}
    for _, row in pivot_gender.iterrows():
        gender = row['Gender']
        date = row['Date']
        
        if gender not in result_dict:
            result_dict[gender] = {}
        if date not in result_dict[gender]:
            result_dict[gender][date] = {}

        # Populate each Observation type with its count, defaulting to 0 if not present
        result_dict[gender][date] = {
            'True Positive': row.get('True Positive', 0),
            'True Negative': row.get('True Negative', 0),
            'False Positive': row.get('False Positive', 0),
            'False Negative': row.get('False Negative', 0)
        }
    
    sorted_location_wise_observations = {}
    for key in sorted(location_wise_observations, key = lambda location: location_wise_observations[location]['Risk Priority Number'], reverse = True):
        sorted_location_wise_observations[key] = location_wise_observations[key]
    
    pivot_date = pd.DataFrame(date_wise_observations)
    pivot_location = pd.DataFrame(sorted_location_wise_observations)

    with pd.ExcelWriter('../../data/pivot.xlsx') as writer:
        pivot_date.to_excel(writer, sheet_name='Date Wise')
        pivot_gender.to_excel(writer, sheet_name='Gender Wise')
        pivot_location.to_excel(writer, sheet_name='Location Wise')
    print("Pivot generated successfully")
    conn.close()

generatePivot('Result', 'Client Data', 'Candidate ID')