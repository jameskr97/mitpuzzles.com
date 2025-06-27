import functools
import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.utils import timezone
from rest_framework.decorators import api_view

from .models import ProlificParticipation


def with_prolific_session(view_func):
    """Decorator to handle common JSON parsing and session retrieval."""
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            prolific_session_id = data.get('prolific_session_id')
            if not prolific_session_id:
                return HttpResponseBadRequest("Missing 'prolific_session_id'.")

            try:
                session = ProlificParticipation.objects.get(id=prolific_session_id)
            except ProlificParticipation.DoesNotExist:
                return HttpResponseNotFound(f"ProlificSession with session_id '{prolific_session_id}' not found.")

            return view_func(request, session, data, *args, **kwargs)
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON.")

    return wrapper

@api_view(['POST'])
@with_prolific_session
def mark_experiment_consented(request, session, data):
    if session.consented_at is not None:
        return JsonResponse({'status': 'success', 'message': 'Experiment already consented.'}, status=200)

    session.consented_at = timezone.now()
    session.save()

    return JsonResponse({'status': 'success', 'message': 'Experiment consent recorded.'})


@api_view(['POST'])
@with_prolific_session
def mark_step(request, session, data):
    step_name = data.get('step')
    session.current_step = step_name
    session.save()
    return JsonResponse({}, status=200)

@api_view(['POST'])
@with_prolific_session
def submit_survey(request, session, data):
    survey_data = data.get('survey')
    session.survey_response = survey_data
    session.completed = True
    session.save()
    return JsonResponse({'completion_code': session.experiment.completion_code}, status=200)

