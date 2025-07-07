from django.urls import path, include
from rest_framework.routers import DefaultRouter

from puzzles import views

router = DefaultRouter()
router.register(r'definition', views.PuzzleDefinitionViewSet, basename='puzzle')
router.register(r'freeplay', views.FreeplayAttemptViewSet, basename='leaderboard')

urlpatterns = [
    # api endpoints
    path("", include(router.urls)),
    path("unsolved", views.UnsolvedPuzzleView.as_view()),
    path("variants", views.PuzzleClassSuffixList.as_view()),
]
