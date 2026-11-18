from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count
from django.shortcuts import redirect, render

from .decorators import role_required
from .forms import LoginForm, ProfileForm, RegisterForm
from .models import User


def home(request):
    if request.user.is_authenticated:
        return redirect(request.user.dashboard_url_name)
    return render(request, 'accounts/home.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect(request.user.dashboard_url_name)
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created for {user.username}. You can now log in.')
            return redirect('accounts:login')
        messages.error(request, 'Registration failed. Please fix the errors below.')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


class UserLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        name = self.request.user.first_name or self.request.user.username
        messages.success(self.request, f'Welcome back, {name}!')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Login failed. Check your username and password.')
        return super().form_invalid(form)


class UserLogoutView(LogoutView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.info(request, 'You have been logged out.')
        return response


@login_required
def dashboard_redirect(request):
    """Send each user to the dashboard that matches their role."""
    return redirect(request.user.dashboard_url_name)


@role_required(User.Role.ADMIN)
def admin_dashboard(request):
    counts = {row['role']: row['total'] for row in User.objects.values('role').annotate(total=Count('id'))}
    context = {
        'total_users': User.objects.count(),
        'admin_count': counts.get(User.Role.ADMIN, 0),
        'staff_count': counts.get(User.Role.STAFF, 0),
        'reviewer_count': counts.get(User.Role.REVIEWER, 0),
        'recent_users': User.objects.order_by('-date_joined')[:5],
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@role_required(User.Role.STAFF)
def staff_dashboard(request):
    return render(request, 'accounts/staff_dashboard.html')


@role_required(User.Role.REVIEWER)
def reviewer_dashboard(request):
    return render(request, 'accounts/reviewer_dashboard.html')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')


@login_required
def profile_edit(request):
    # Always the logged-in user's own record; there is no user id in the URL.
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was updated.')
            return redirect('accounts:profile')
        messages.error(request, 'Profile not saved. Please fix the errors below.')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})
