from django.urls import path
from puzzles import views

urlpatterns = [
    # api endpoints
    path("random", views.RandomPuzzleView.as_view()),
    path("unsolved", views.UnsolvedPuzzleView.as_view()),
    path("variants", views.PuzzleClassSuffixList.as_view()),
]
