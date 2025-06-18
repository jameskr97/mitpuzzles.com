import json

from django.http import HttpResponse, JsonResponse
from django.conf import settings
from crawleruseragents import is_crawler
from rest_framework.decorators import api_view
from better_profanity import profanity
from profanity_check import predict as predict_profanity

from .models import Visitor

# Initialize profanity filter
profanity.load_censor_words()

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
            return JsonResponse({"generated_username": visitor.generated_username})
        except Visitor.DoesNotExist:
            pass
    # invariant - user does not have a valid Visitor id
    visitor = Visitor.objects.create(user_agent=ua)
    visitor.set_readable_username()
    visitor.save()

    # Build response
    response = JsonResponse({"generated_username": visitor.generated_username}, status=201)
    response.set_cookie(
        cookie_name,
        str(visitor.id),
        max_age=cookie_age,
        secure=secure,
        httponly=True,
        samesite=samesite
    )
    return response

@api_view(['POST'])
def change_visitor_username(request):
    """
    Endpoint to change the username of a visitor.
    Expects JSON with new_username field.
    Uses the visitor_id cookie to identify the visitor.
    """
    try:
        data = json.loads(request.body)
        new_username = data.get("new_username")

        # Get visitor ID from cookie
        visitor_id = request.COOKIES.get("visitor_id")
        if not visitor_id:
            return JsonResponse({"error": "Visitor not identified"}, status=401)

        if not new_username:
            return JsonResponse({"error": "New username is required"}, status=400)

        # Validate username
        if len(new_username) > 50:
            return JsonResponse({"error": "Username too long (max 50 characters)"}, status=400)

        # Check for profanity in the username
        if  profanity.contains_profanity(new_username) or predict_profanity([new_username]) > 0:
            return JsonResponse({"error": "Username contains inappropriate language"}, status=400)

        # Check for uniqueness
        if Visitor.objects.filter(generated_username=new_username).exists():
            return JsonResponse({"error": "Username already taken"}, status=400)

        try:
            visitor = Visitor.objects.get(id=visitor_id)
            visitor.generated_username = new_username
            visitor.save()
            return JsonResponse({"success": True, "username": new_username})
        except Visitor.DoesNotExist:
            return JsonResponse({"error": "Visitor not found"}, status=404)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
