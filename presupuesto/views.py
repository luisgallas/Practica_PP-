from django.shortcuts import render
from django.http import JsonResponse


def api_info(request):
    """Endpoint básico de información"""
    return JsonResponse({
        'mensaje': 'API Practica PP',
        'versión': '1.0.0'
    })
