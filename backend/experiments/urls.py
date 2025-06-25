from django.urls import path
from . import views

urlpatterns = [
    path('consent', views.mark_experiment_consented, name='mark_experiment_consented'),
    path('step', views.mark_step, name='mark_step'),
    path('survey', views.submit_survey, name='submit_survey'),
]
