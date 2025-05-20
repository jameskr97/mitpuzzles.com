from rest_framework import serializers
from core import models

class FeedbackSerializer(serializers.Serializer):
    message = serializers.CharField()
    metadata = serializers.JSONField()

    def create(self, validated_data):
        request = self.context["request"]

        kwargs = {
            "message": validated_data.get("message"),
            "metadata": validated_data.get("metadata")
        }

        if request.user and request.user.is_authenticated:
            kwargs["user"] = request.user
        else:
            kwargs["visitor"] = request.visitor

        return models.Feedback.objects.create(**kwargs)
