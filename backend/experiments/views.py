import functools
import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework import viewsets

from .models import ProlificParticipation
from .serializers import ProlificParticipationSerializer


class ProlificParticipationViewSet(viewsets.ModelViewSet):
    queryset = ProlificParticipation.objects.all()
    serializer_class = ProlificParticipationSerializer
    lookup_field = 'prolific_session_id'

    def create(self, request, *args, **kwargs):
        """Create participation record with all data at once"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return JsonResponse({
            'status': 'success',
            'message': 'Experiment data submitted successfully',
            'data': serializer.data
        }, status=201)
