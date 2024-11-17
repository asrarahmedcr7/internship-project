import pandas as pd

def findAccuracy(observations):
    return ((observations["True Positive"] + observations["True Negative"]) * 100 )// (observations["True Positive"] + observations["True Negative"] + observations["False Negative"] + observations["False Positive"])

def findDemographicParity(observations):
    return ((observations["True Positive"] + observations["False Positive"]) *100) // (observations["True Positive"] + observations["True Negative"] + observations["False Negative"] + observations["False Positive"])

def findTPR(observations_on_a_date):
    return (observations_on_a_date["True Positive"] * 100) // (observations_on_a_date["True Positive"] + observations_on_a_date["False Negative"])

def findTotal(observations):
    return (observations["True Positive"] + observations["True Negative"] + observations["False Negative"] + observations["False Positive"])

def fillLevels(location_wise_observations):
    candidate_location_data = [(location_wise_observations[location]['Total'], location) for location in location_wise_observations]
    location_accuracy_data = [(location_wise_observations[location]['Overall Accuracy'], location) for location in location_wise_observations]
    num_locations = len(candidate_location_data)

    candidate_location_data.sort(key = lambda x : x[0], reverse = True)
    for i in range(num_locations):
        location_wise_observations[candidate_location_data[i][1]]['Candidate Count Level'] = num_locations - i

    location_accuracy_data.sort(key = lambda x : x[0])
    for i in range(num_locations):
        location_wise_observations[location_accuracy_data[i][1]]['Accuracy Level'] = i + 1

    return location_wise_observations

def fillRiskPriorityNumbers(location_wise_observations):
    for location in location_wise_observations:
        location_wise_observations[location]['Risk Priority Number'] = location_wise_observations[location]['Candidate Count Level'] * location_wise_observations[location]['Accuracy Level']
    return location_wise_observations

def get_flag(observations):
    if observations['Accuracy Level'] > observations['Candidate Count Level']:
        return -1
    elif observations['Accuracy Level'] == observations['Candidate Count Level']:
        return 0
    else:
        return 1