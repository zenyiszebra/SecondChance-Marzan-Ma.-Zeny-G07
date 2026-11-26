from django.conf import settings
from django.core.exceptions import ValidationError
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

    def __str__(self):
        return f'{self.inmate_number} - {self.full_name}'
