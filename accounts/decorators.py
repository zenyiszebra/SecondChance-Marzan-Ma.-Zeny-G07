from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*allowed_roles):
    """Allow only logged-in users whose role is in allowed_roles.

    Logged-out users go to the login page. Users with another role are sent
    back to their own dashboard, so typing another role's URL does nothing.
    """

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                messages.error(request, 'You do not have permission to open that page.')
                return redirect(request.user.dashboard_url_name)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
