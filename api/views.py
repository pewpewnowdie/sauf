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
    query = request.data['query']
    if query:
        print(Issue.saufQL(query=query))
        return Response({'result' : 'ran fine'})
    else:
        return Response({'error' : 'Invalid saufQL'}, status=400)
