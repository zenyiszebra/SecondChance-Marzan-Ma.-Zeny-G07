from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User

from .forms import InmateForm, ProgressForm
from .models import Inmate, ProgressRecord

ALL_ROLES = (User.Role.ADMIN, User.Role.STAFF, User.Role.REVIEWER)
WRITE_ROLES = (User.Role.ADMIN, User.Role.STAFF)
STAGE_COUNT = len(ProgressRecord.Stage.choices)


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
    inmates = list(
        inmates.annotate(
            done_count=Count('records', filter=Q(records__status=ProgressRecord.Status.COMPLETED))
        )
    )
    for inmate in inmates:
        inmate.percent = round(inmate.done_count / STAGE_COUNT * 100)
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
    records = {r.stage: r for r in inmate.records.select_related('recorded_by')}
    stages = [
        {'value': value, 'label': label, 'record': records.get(value)}
        for value, label in ProgressRecord.Stage.choices
    ]
    context = {
        'inmate': inmate,
        'stages': stages,
        'done_count': sum(1 for r in records.values() if r.status == ProgressRecord.Status.COMPLETED),
        'stage_count': STAGE_COUNT,
        'can_edit': can_edit_inmate(request.user, inmate),
    }
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


def get_record_or_404(user, pk):
    """A stage record can be changed only by someone who may edit its inmate."""
    return get_object_or_404(
        ProgressRecord.objects.select_related('inmate'),
        pk=pk,
        inmate__in=editable_inmates(user),
    )


@role_required(*WRITE_ROLES)
def progress_create(request, inmate_pk):
    inmate = get_object_or_404(editable_inmates(request.user), pk=inmate_pk)
    record = ProgressRecord(inmate=inmate)
    if request.method == 'POST':
        form = ProgressForm(request.POST, instance=record)
        if form.is_valid():
            saved = form.save(commit=False)
            saved.recorded_by = request.user
            saved.save()
            messages.success(request, f'{saved.get_stage_display()} was recorded for {inmate.full_name}.')
            return redirect(inmate)
        messages.error(request, 'The stage was not saved. Please fix the errors below.')
    else:
        form = ProgressForm(instance=record, initial={'stage': request.GET.get('stage')})
    context = {'form': form, 'inmate': inmate, 'title': 'Record a rehabilitation stage'}
    return render(request, 'pipeline/progress_form.html', context)


@role_required(*WRITE_ROLES)
def progress_edit(request, pk):
    record = get_record_or_404(request.user, pk)
    if request.method == 'POST':
        form = ProgressForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, f'{record.get_stage_display()} was updated.')
            return redirect(record.inmate)
        messages.error(request, 'Changes were not saved. Please fix the errors below.')
    else:
        form = ProgressForm(instance=record)
    context = {'form': form, 'inmate': record.inmate, 'title': 'Edit rehabilitation stage'}
    return render(request, 'pipeline/progress_form.html', context)


@role_required(*WRITE_ROLES)
def progress_delete(request, pk):
    record = get_record_or_404(request.user, pk)
    if request.method == 'POST':
        inmate = record.inmate
        label = record.get_stage_display()
        record.delete()
        messages.success(request, f'{label} record was deleted.')
        return redirect(inmate)
    return render(request, 'pipeline/progress_confirm_delete.html', {'record': record})
