from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
from trackers.models import Issue, Project
from trackers.serializers import IssueSerializer, ProjectSerializer
import json

# Create your views here.

@api_view(['GET'])
def issues(request, *args, **kwargs):
    query = request.data['query']
    if query:
        instance = Issue.saufQL(query=query)
        data = IssueSerializer(instance, many=True).data
        return Response({'type' : 'json', 'result': data})
    else:
        return Response({'type': 'error', 'result': 'Invalid saufQL'}, status=400)
    

@api_view(['GET'])
def projects(request, *args, **kwargs):
    instance = Project.objects.all()
    data = ProjectSerializer(instance, many=True).data
    return Response({'type': 'json', 'result': data})
