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
from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from django.views.generic import TemplateView
from django.conf import settings
from mitlogic import views


def serve_root(*args, **kwargs):
    """
    View function which wraps the basic logic behind serving the root html for the frontend.
    In debug mode, a redirect response is sent which can direct the browser to a local vue server.
    Otherwise, the frontend path setting is used in conjunction with the static root setting to find and respond
    with the root html file.

    :return: the response (either a redirect or a render response).
    """
    if settings.DEBUG:
        return HttpResponseRedirect("http://localhost:3000/")
    root_filepath = finders.find("frontend/index.html", all=False)
    if not root_filepath:
        raise ImproperlyConfigured("Could not find frontend root in static file!")
    with open(root_filepath, "r") as root_file:
        response = HttpResponse(root_file.read(), content_type="text/html")
    return response

urlpatterns = [
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type='text/plain')),
    path('admin/', admin.site.urls),

    # 3rd-party app endpoints
    path('accounts/', include('allauth.urls')),
    path('_allauth/', include('allauth.headless.urls')),

    # api endpoints
    path('api/puzzle/random', views.get_random_puzzle),
    path('api/puzzle/submit', views.post_game_recording),
    path('api/config/game-settings', views.game_settings_view),

    # redirect static files (*.css, *.js, *.jpg etc.) served on root ("/") to the static directory ("/static/")
    re_path(
        r"^(?!/?static/)(?P<path>.*\..*)$",
        RedirectView.as_view(url="/static/%(path)s", permanent=False),
    ),

    # All other paths are served the root html file.
    re_path(r'^.*$', serve_root),
]
