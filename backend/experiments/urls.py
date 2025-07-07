from django.urls import path
from pycparser.c_ast import Default
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('prolific', views.ProlificParticipationViewSet, basename='prolific-participation')

urlpatterns = router.urls
