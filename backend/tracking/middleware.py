import logging
import uuid
import crawleruseragents

from django.utils import timezone
from django.conf import settings
from django.core.signing import Signer, BadSignature
from .models import Visitor

VISITOR_COOKIE = "visitor_id"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365 * 1  # 1 year
signer = Signer()  # optional: to prevent forging


class VisitorMiddleware:
    """
    Checks for a visitor_id cookie in the request, and if it exists,
    retrieves the corresponding Visitor object, and sets it on the request object.
    If the cookie does not exist, no visitor is set on the request.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.cookie_name = getattr(settings, "VISITOR_COOKIE_NAME", "visitor_id")
        self.cookie_age = getattr(settings, "VISITOR_COOKIE_AGE", 365 * 24 * 60 * 60)  # 1 year
        # default for secure and samesite settings taken from Django settings defaults
        self.secure = getattr(settings, "SESSION_COOKIE_SECURE", True)
        self.samesite = getattr(settings, "SESSION_COOKIE_SAMESITE", "Lax")

    def __call__(self, request):
        request.visitor = None

        # if user is authenticated, return early.
        # don't check for a visitor cookie when they are logged in.
        if hasattr(request, "user") and request.user.is_authenticated:
            return self.get_response(request)

        # try to load existing Visitor
        visitor = None
        vid = request.COOKIES.get(self.cookie_name)
        if vid:
            try:
                visitor = Visitor.objects.get(pk=vid)
                visitor.save()  # bumps last_seen via auto_now=True
            except (Visitor.DoesNotExist, ValueError):
                visitor = None
        request.visitor = visitor

        # invariant - visitor object exists
        return self.get_response(request)
