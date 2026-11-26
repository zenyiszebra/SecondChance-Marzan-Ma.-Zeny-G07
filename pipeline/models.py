from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Inmate(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        RELEASED = 'released', 'Released'

    inmate_number = models.CharField(
        max_length=20, unique=True, help_text='Unique ID, for example SC-2026-001.'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    sentence_start = models.DateField()
    sentence_end = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='inmates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def clean(self):
        errors = {}
        if self.date_of_birth and self.date_of_birth >= timezone.localdate():
            errors['date_of_birth'] = 'Date of birth must be in the past.'
        if self.sentence_start and self.sentence_end and self.sentence_end <= self.sentence_start:
            errors['sentence_end'] = 'Sentence end must be after the sentence start.'
        if self.date_of_birth and self.sentence_start and self.sentence_start < self.date_of_birth:
            errors['sentence_start'] = 'Sentence start cannot be before the date of birth.'
        if errors:
            raise ValidationError(errors)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_absolute_url(self):
        return reverse('pipeline:inmate_detail', args=[self.pk])

    @property
    def completed_stage_count(self):
        return self.records.filter(status=ProgressRecord.Status.COMPLETED).count()

    @property
    def progress_percent(self):
        return round(self.completed_stage_count / len(ProgressRecord.Stage.choices) * 100)

    def __str__(self):
        return f'{self.inmate_number} - {self.full_name}'


class ProgressRecord(models.Model):
    """One rehabilitation stage for one inmate (at most one record per stage)."""

    class Stage(models.TextChoices):
        ASSESSMENT = 'assessment', 'Initial Assessment'
        EDUCATION = 'education', 'Education'
        SKILLS = 'skills', 'Skills Training'
        COUNSELING = 'counseling', 'Counseling'
        WORK = 'work', 'Work Program'
        RELEASE_PREP = 'release_prep', 'Release Preparation'

    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not started'
        IN_PROGRESS = 'in_progress', 'In progress'
        COMPLETED = 'completed', 'Completed'

    inmate = models.ForeignKey(Inmate, on_delete=models.CASCADE, related_name='records')
    stage = models.CharField(max_length=20, choices=Stage.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
    hours_completed = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(5000)])
    completed_on = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='progress_records'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['inmate', 'created_at']
        constraints = [
            models.UniqueConstraint(fields=['inmate', 'stage'], name='unique_stage_per_inmate')
        ]

    def clean(self):
        errors = {}
        if self.status == self.Status.COMPLETED and not self.completed_on:
            errors['completed_on'] = 'Enter the completion date for a completed stage.'
        if self.completed_on:
            if self.status != self.Status.COMPLETED:
                errors['completed_on'] = 'Only completed stages can have a completion date.'
            elif self.completed_on > timezone.localdate():
                errors['completed_on'] = 'The completion date cannot be in the future.'
            elif self.inmate_id and self.completed_on < self.inmate.sentence_start:
                errors['completed_on'] = 'The completion date cannot be before the sentence start.'
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.inmate.inmate_number} - {self.get_stage_display()}'
