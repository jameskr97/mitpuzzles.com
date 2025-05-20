from django.http import HttpResponse, JsonResponse
from django.conf import settings
from crawleruseragents import is_crawler
from .models import Visitor

def visitor_init(request):
    """
    GET /api/visitor
    - If bot UA → 204 No Content
    - If user is authenticated → 204 No Content
    - If there is already a valid visitor_id cookie → 204 No Content
    - If valid visitor_id cookie → 204 No Content
    - Else → create Visitor, set cookie, return 201 + JSON { visitor_id }
    """
    # Pull config from settings with defaults
    cookie_name = getattr(settings, "VISITOR_COOKIE_NAME", "visitor_id")
    cookie_age  = getattr(settings, "VISITOR_COOKIE_AGE", 365 * 24 * 60 * 60)
    secure      = getattr(settings, "SESSION_COOKIE_SECURE", True)
    samesite    = getattr(settings, "SESSION_COOKIE_SAMESITE", "Lax")

    ua = request.META.get("HTTP_USER_AGENT", "")
    if is_crawler(ua):
        return HttpResponse(status=204)

    # If user is authenticated, do not create a visitor
    if hasattr(request, "user") and request.user.is_authenticated:
        response = HttpResponse(status=204)
        # Delete visitor cookie if it exists for logged-in users
        if cookie_name in request.COOKIES:
            response.delete_cookie(cookie_name)
        return response

    vid = request.COOKIES.get(cookie_name)
    # If they already have a valid Visitor, do nothing
    if vid:
        try:
            visitor = Visitor.objects.get(pk=vid)
            visitor.save(update_fields=['last_seen'])  # bumps last_seen via auto_now=True
            return HttpResponse(status=204)
        except Visitor.DoesNotExist:
            pass
    # invariant - user does not have a valid Visitor id
    visitor = Visitor.objects.create(user_agent=ua)

    # Build response
    response = HttpResponse(status=201)
    response.set_cookie(
        cookie_name,
        str(visitor.id),
        max_age=cookie_age,
        secure=secure,
        httponly=True,
        samesite=samesite
    )
    return response
