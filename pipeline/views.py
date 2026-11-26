from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User

from .forms import InmateForm
from .models import Inmate

ALL_ROLES = (User.Role.ADMIN, User.Role.STAFF, User.Role.REVIEWER)
WRITE_ROLES = (User.Role.ADMIN, User.Role.STAFF)


def visible_inmates(user):
    """Staff see only their own inmates. Admin and reviewer see all."""
    queryset = Inmate.objects.select_related('created_by')
    if user.role == User.Role.STAFF:
        return queryset.filter(created_by=user)
    return queryset


def editable_inmates(user):
    """Admin edits all. Staff edit only their own. Reviewers edit nothing."""
    if user.role == User.Role.ADMIN:
        return Inmate.objects.all()
    if user.role == User.Role.STAFF:
        return Inmate.objects.filter(created_by=user)
    return Inmate.objects.none()


def can_edit_inmate(user, inmate):
    return user.role == User.Role.ADMIN or (
        user.role == User.Role.STAFF and inmate.created_by_id == user.id
    )


@role_required(*ALL_ROLES)
def inmate_list(request):
    query = request.GET.get('q', '').strip()
    inmates = visible_inmates(request.user)
    if query:
        inmates = inmates.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(inmate_number__icontains=query)
        )
    context = {
        'inmates': inmates,
        'q': query,
        'can_create': request.user.role in WRITE_ROLES,
    }
    return render(request, 'pipeline/inmate_list.html', context)


@role_required(*WRITE_ROLES)
def inmate_create(request):
    if request.method == 'POST':
        form = InmateForm(request.POST)
        if form.is_valid():
            inmate = form.save(commit=False)
            inmate.created_by = request.user
            inmate.save()
            messages.success(request, f'{inmate.full_name} was added.')
            return redirect(inmate)
        messages.error(request, 'The inmate was not saved. Please fix the errors below.')
    else:
        form = InmateForm()
    return render(request, 'pipeline/inmate_form.html', {'form': form, 'title': 'Add inmate'})


@role_required(*ALL_ROLES)
def inmate_detail(request, pk):
    inmate = get_object_or_404(visible_inmates(request.user), pk=pk)
    context = {'inmate': inmate, 'can_edit': can_edit_inmate(request.user, inmate)}
    return render(request, 'pipeline/inmate_detail.html', context)


@role_required(*WRITE_ROLES)
def inmate_edit(request, pk):
    inmate = get_object_or_404(editable_inmates(request.user), pk=pk)
    if request.method == 'POST':
        form = InmateForm(request.POST, instance=inmate)
        if form.is_valid():
            form.save()
            messages.success(request, f'{inmate.full_name} was updated.')
            return redirect(inmate)
        messages.error(request, 'Changes were not saved. Please fix the errors below.')
    else:
        form = InmateForm(instance=inmate)
    return render(request, 'pipeline/inmate_form.html', {'form': form, 'title': 'Edit inmate'})


@role_required(*WRITE_ROLES)
def inmate_delete(request, pk):
    inmate = get_object_or_404(editable_inmates(request.user), pk=pk)
    if request.method == 'POST':
        name = inmate.full_name
        inmate.delete()
        messages.success(request, f'{name} was deleted.')
        return redirect('pipeline:inmate_list')
    return render(request, 'pipeline/inmate_confirm_delete.html', {'inmate': inmate})
