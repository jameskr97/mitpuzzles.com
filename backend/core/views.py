
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle
from core import serializers


class FeedbackAPIView(APIView):
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        serializer = serializers.FeedbackSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
