class EnsureSessionMiddleware:
    """
    In order for us to be able to tell if the same user is making a request, we need to give them a session ID.
    This middleware ensures that a session ID is created for each user. This works for both anonymous and authenticated users.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Force the session to create a session key if it does not exist.
        if not request.session.session_key:
            request.session.save()
        response = self.get_response(request)
        return response
