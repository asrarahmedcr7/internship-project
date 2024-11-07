import pandas as pd

def findAccuracy(observations):
    return (observations["True Positive"] + observations["True Negative"]) * 100 // (observations["True Positive"] + observations["True Negative"] + observations["False Negative"] + observations["False Positive"])

def findTNR(observations_on_a_date):
    return (observations_on_a_date["True Negative"] * 100) // (observations_on_a_date["True Negative"] + observations_on_a_date["False Positive"])

def findAccuracyLevel(accuracy):
    if accuracy >= 80:
        return 1
    elif accuracy >= 70:
        return 2
    return 3

def findTotal(observations):
    return (observations["True Positive"] + observations["True Negative"] + observations["False Negative"] + observations["False Positive"])

def fillCandidateCountLevels(location_wise_observations):
    data = {'totals' : [location_wise_observations[location]['Total'] for location in location_wise_observations]}
    df = pd.DataFrame(data)
    mean = df['totals'].mean()
    std = df['totals'].std()

    # Categorize the data
    for location in location_wise_observations:
        if location_wise_observations[location]['Total'] > mean + std:
            location_wise_observations[location]['Candidate Count Level'] = 3
        elif location_wise_observations[location]['Total'] >= mean - std and location_wise_observations[location]['Total'] <= mean + std:
            location_wise_observations[location]['Candidate Count Level'] = 2
        else:
            location_wise_observations[location]['Candidate Count Level'] = 1

    return location_wise_observations

def fillRiskPriorityNumbers(location_wise_observations):
    for location in location_wise_observations:
        location_wise_observations[location]['Risk Priority Number'] = location_wise_observations[location]['Candidate Count Level'] * location_wise_observations[location]['Accuracy Level']
    return location_wise_observations