"""
URL configuration for mitlogic project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.http import HttpResponse, HttpResponseRedirect
from django.core.exceptions import ImproperlyConfigured
from django.contrib.staticfiles import finders
from django.contrib import admin
from django.urls import path, re_path
from django.views.generic.base import RedirectView
from django.views.generic import TemplateView
from django.conf import settings

def serve_frontend(*args, **kwargs):
    """
    View function which wraps the basic logic behind serving the root html for the frontend.
    In debug mode, a redirect response is sent which can direct the browser to a local vue server.
    Otherwise, the frontend path setting is used in conjunction with the static root setting to find and respond
    with the root html file.

    :return: the response (either a redirect or a render response).
    """
    root_filepath = finders.find("index.html", all=False)
    if not root_filepath:
        raise ImproperlyConfigured("Could not find frontend root in static file!")
    with open(root_filepath, "r") as root_file:
        response = HttpResponse(root_file.read(), content_type="text/html")
    return response

urlpatterns = [
    path('admin/', admin.site.urls),
    # redirect to frontend if no other path matches (excluding "static/" path)
    re_path(r"^(?!static/)(?P<path>.*)$", serve_frontend),
    # redirect static files (*.css, *.js, *.jpg etc.) served on root ("/") to the static directory ("/static/")
    re_path(
        r"^(?!/?static/)(?P<path>.*\..*)$",
        RedirectView.as_view(url="/static/%(path)s", permanent=False),
    ),
]
