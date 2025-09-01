from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
from trackers.models import Issue
from trackers.serializers import IssueSerializer
import json

# Create your views here.

@api_view(['GET'])
def issues(request, *args, **kwargs):
    project = request.data['project']
    if project:
        queryset = Issue.objects.filter(project=project)
        data = []
        for issue in queryset:
            data.append(IssueSerializer(issue).data)
        return Response({'result' : data})
    else:
        return Response({'error' : 'Invalid Project'}, status=400)
    

# @api_view(['GET'])
# def issues(request, *args, **kwargs):
#     saufql = request.data['saufql']
#     if saufql:
#         pass
