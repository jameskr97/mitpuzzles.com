from rest_framework import serializers
from .models import ProlificParticipation, Experiment
from tracking.models import Visitor


class ProlificParticipationSerializer(serializers.ModelSerializer):
    experiment_id = serializers.CharField(write_only=True, required=False)
    prolific_participant_id = serializers.CharField(write_only=True)
    prolific_study_id = serializers.CharField(write_only=True)
    prolific_session_id = serializers.CharField(write_only=True)
    experiment_data = serializers.JSONField(required=False, default=dict)
    survey = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = ProlificParticipation
        fields = [
            'id', 'prolific_participant_id', 'prolific_study_id', 'prolific_session_id',
            'experiment_data', 'survey', 'created_at', 'updated_at', 'experiment_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Extract prolific data
        prolific_participant_id = validated_data.pop('prolific_participant_id')
        prolific_study_id = validated_data.pop('prolific_study_id')
        prolific_session_id = validated_data.pop('prolific_session_id')
        experiment_id = validated_data.pop('experiment_id')

        # Extract survey data and put it in survey_response field
        survey_data = validated_data.pop('survey', None)

        # Get visitor and experiment from context
        request = self.context.get('request')
        visitor = getattr(request, 'visitor', None)

        return ProlificParticipation.objects.create(
            prolific_subject_id=prolific_participant_id,
            prolific_study_id=prolific_study_id,
            prolific_session_id=prolific_session_id,
            survey_response=survey_data,
            visitor=visitor,
            experiment_id=experiment_id,
            **validated_data
        )
