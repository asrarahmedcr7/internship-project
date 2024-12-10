import plotly.express as px
from django.shortcuts import render
import pandas as pd
from Client.utils import retrieveData
from django.http import Http404

def overallAccuracyView(request):
    if request.method == "POST":
        user = request.user
        client_id = user.client.id
        engagement_id = request.POST.get('engagement_id')

        if engagement_id is None:
            engagement_id = request.session.get('engagement_id')
        
        request.session['engagement_id'] = engagement_id
        result = retrieveData(table_name = f'Result-{client_id}-{engagement_id}')
        
        fig = px.line(data_frame=result, x=list(range(1, len(result['r2']) + 1)), y='r2', title='R2 Trend')
        graph = fig.to_html(full_html=False)
        return render(request, 'Client/regression/overallAccuracy.html', {'graph':graph, 'engagement_type':'regression'})
    return Http404()

def modelAccuracyView(request):
    if request.method == "POST":
        user = request.user
        client_id = user.client.id
        engagement_id = request.session.get('engagement_id')

        result = retrieveData(table_name = f'Result-{client_id}-{engagement_id}')
        coefficients_df = pd.DataFrame({'Feature':[feature for feature in result if feature != 'r2' and feature != 'mse'], 'Coefficient':[list(result[feature])[-1] for feature in result if feature != 'r2' and feature != 'mse']})
    
        fig = px.bar(coefficients_df, x='Feature', y='Coefficient', color_discrete_sequence=['lightgreen'], title='Feature Importance')
        graph = fig.to_html(full_html=False)
        return render(request, 'Client/regression/modelAccuracy.html', {'graph':graph, 'engagement_type':'regression'})

    return Http404()

def modelInclusivityView(request):
    if request.method == "POST":
        pass
    return Http404()