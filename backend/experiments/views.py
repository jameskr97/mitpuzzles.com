import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import ProlificParticipation

@require_POST
def mark_experiment_consented(request):
    try:
        data = json.loads(request.body)
        prolific_session_id = data.get('prolific_session_id')
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON.")

    if not prolific_session_id:
        return HttpResponseBadRequest("Missing 'prolific_session_id'.")

    try:
        session = ProlificParticipation.objects.get(id=prolific_session_id)
    except ProlificParticipation.DoesNotExist:
        return HttpResponseNotFound(f"ProlificSession with session_id '{prolific_session_id}' not found.")


    if session.consented_at is not None:
        return JsonResponse({'status': 'success', 'message': 'Experiment already consented.'}, status=200)

    session.consented_at = timezone.now()
    session.save()

    return JsonResponse({'status': 'success', 'message': 'Experiment consent recorded.'})

@require_POST
def mark_step(request):
    try:
        data = json.loads(request.body)
        prolific_session_id = data.get('prolific_session_id')
        step_name = data.get('step')
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON.")

    if not prolific_session_id:
        return HttpResponseBadRequest("Missing 'prolific_session_id'.")

    try:
        session = ProlificParticipation.objects.get(id=prolific_session_id)
    except ProlificParticipation.DoesNotExist:
        return HttpResponseNotFound(f"ProlificSession with session_id '{prolific_session_id}' not found.")

    session.current_step = step_name
    session.save()
    return JsonResponse({}, status=200)


@require_POST
def submit_survey(request):
    try:
        data = json.loads(request.body)
        prolific_session_id = data.get('prolific_session_id')
        survey_data = data.get('survey')
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON.")

    if not prolific_session_id:
        return HttpResponseBadRequest("Missing 'prolific_session_id'.")

    try:
        session = ProlificParticipation.objects.get(id=prolific_session_id)
    except ProlificParticipation.DoesNotExist:
        return HttpResponseNotFound(f"ProlificSession with session_id '{prolific_session_id}' not found.")

    session.survey_response = survey_data
    session.completed = True
    session.save()
    return JsonResponse({'completion_code': session.experiment.completion_code }, status=200)
