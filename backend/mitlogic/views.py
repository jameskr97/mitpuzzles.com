from django.views.decorators.http import etag
from rest_framework.decorators import api_view
from rest_framework.response import Response
from mitlogic import models
from mitlogic import serializers
import re

from django.views.decorators.http import etag
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def get_random_puzzle(request):
    x = models.Puzzles.objects.order_by('?').first()
    serialized = serializers.PuzzleMinesweeperSerializer(x)
    return Response(serialized.data)

from .config import generate_settings_etag, get_game_settings


@etag(generate_settings_etag)
@api_view(['GET'])
def game_settings_view(request):
    return Response(get_game_settings())