from django.urls import path, include
from rest_framework.routers import DefaultRouter

from puzzles import views

router = DefaultRouter()
router.register(r'puzzles', views.PuzzleDefinitionViewSet, basename='puzzle')

urlpatterns = [
    # api endpoints
    path("", include(router.urls)),
    path("random", views.RandomPuzzleView.as_view()),
    path("unsolved", views.UnsolvedPuzzleView.as_view()),
    path("variants", views.PuzzleClassSuffixList.as_view()),
    path('leaderboard', views.leaderboard_view)
]
