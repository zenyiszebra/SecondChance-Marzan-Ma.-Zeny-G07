from django import forms

from accounts.forms import BootstrapFormMixin

from .models import Inmate, ProgressRecord


class InmateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Inmate
        fields = (
            'inmate_number', 'first_name', 'last_name', 'date_of_birth',
            'sentence_start', 'sentence_end', 'status', 'notes',
        )
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'sentence_start': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'sentence_end': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def clean_inmate_number(self):
        return self.cleaned_data['inmate_number'].strip().upper()


class ProgressForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ProgressRecord
        fields = ('stage', 'status', 'hours_completed', 'completed_on', 'remarks')
        widgets = {
            'completed_on': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def clean(self):
        cleaned = super().clean()
        stage = cleaned.get('stage')
        if stage and self.instance.inmate_id:
            duplicate = ProgressRecord.objects.filter(
                inmate_id=self.instance.inmate_id, stage=stage
            ).exclude(pk=self.instance.pk)
            if duplicate.exists():
                self.add_error(
                    'stage', 'This stage is already recorded for this inmate. Edit that record instead.'
                )
        return cleaned
