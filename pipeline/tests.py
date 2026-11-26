from datetime import date

from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Inmate, ProgressRecord

PASSWORD = 'S3cure-Pass!word'


def make_user(username, role=User.Role.STAFF):
    return User.objects.create_user(
        username=username, email=f'{username}@example.com', password=PASSWORD, role=role
    )


def make_inmate(owner, number='SC-001', **extra):
    data = dict(
        inmate_number=number, first_name='Juan', last_name='Dela Cruz',
        date_of_birth=date(1990, 1, 1), sentence_start=date(2024, 1, 1),
        sentence_end=date(2030, 1, 1), created_by=owner,
    )
    data.update(extra)
    return Inmate.objects.create(**data)


def form_data(**extra):
    data = {
        'inmate_number': 'sc-100', 'first_name': 'Pedro', 'last_name': 'Reyes',
        'date_of_birth': '1991-05-05', 'sentence_start': '2025-01-01',
        'sentence_end': '2029-01-01', 'status': 'active', 'notes': '',
    }
    data.update(extra)
    return data


class InmateCrudTests(TestCase):
    def setUp(self):
        self.staff = make_user('staff1')
        self.client.login(username='staff1', password=PASSWORD)

    def test_staff_can_create_inmate_linked_to_them(self):
        response = self.client.post(reverse('pipeline:inmate_create'), form_data())
        inmate = Inmate.objects.get(inmate_number='SC-100')
        self.assertRedirects(response, inmate.get_absolute_url())
        self.assertEqual(inmate.created_by, self.staff)

    def test_sentence_end_must_be_after_start(self):
        response = self.client.post(
            reverse('pipeline:inmate_create'), form_data(sentence_end='2024-01-01')
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Inmate.objects.count(), 0)

    def test_duplicate_inmate_number_is_rejected(self):
        make_inmate(self.staff, number='SC-100')
        response = self.client.post(reverse('pipeline:inmate_create'), form_data())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Inmate.objects.count(), 1)

    def test_staff_can_edit_and_delete_own_inmate(self):
        inmate = make_inmate(self.staff)
        self.client.post(
            reverse('pipeline:inmate_edit', args=[inmate.pk]), form_data(inmate_number='SC-001')
        )
        inmate.refresh_from_db()
        self.assertEqual(inmate.first_name, 'Pedro')
        self.client.post(reverse('pipeline:inmate_delete', args=[inmate.pk]))
        self.assertFalse(Inmate.objects.filter(pk=inmate.pk).exists())


class InmateAccessTests(TestCase):
    def setUp(self):
        self.owner = make_user('owner')
        self.other = make_user('other')
        self.inmate = make_inmate(self.owner)

    def test_logged_out_user_is_sent_to_login(self):
        response = self.client.get(reverse('pipeline:inmate_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_staff_cannot_see_another_staffs_inmate(self):
        self.client.login(username='other', password=PASSWORD)
        response = self.client.get(reverse('pipeline:inmate_detail', args=[self.inmate.pk]))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse('pipeline:inmate_delete', args=[self.inmate.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Inmate.objects.filter(pk=self.inmate.pk).exists())

    def test_admin_sees_all_inmates(self):
        make_user('boss', role=User.Role.ADMIN)
        self.client.login(username='boss', password=PASSWORD)
        response = self.client.get(reverse('pipeline:inmate_detail', args=[self.inmate.pk]))
        self.assertEqual(response.status_code, 200)

    def test_reviewer_is_read_only(self):
        make_user('rev', role=User.Role.REVIEWER)
        self.client.login(username='rev', password=PASSWORD)
        self.assertEqual(self.client.get(reverse('pipeline:inmate_list')).status_code, 200)
        self.assertEqual(
            self.client.get(reverse('pipeline:inmate_detail', args=[self.inmate.pk])).status_code, 200
        )
        response = self.client.post(reverse('pipeline:inmate_create'), form_data())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Inmate.objects.count(), 1)
        response = self.client.post(reverse('pipeline:inmate_delete', args=[self.inmate.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Inmate.objects.filter(pk=self.inmate.pk).exists())


def make_record(inmate, owner, stage='education', status='in_progress', **extra):
    data = dict(inmate=inmate, stage=stage, status=status, recorded_by=owner)
    data.update(extra)
    return ProgressRecord.objects.create(**data)


class ProgressRecordTests(TestCase):
    def setUp(self):
        self.staff = make_user('staff1')
        self.inmate = make_inmate(self.staff)
        self.client.login(username='staff1', password=PASSWORD)
        self.url = reverse('pipeline:progress_create', args=[self.inmate.pk])

    def test_staff_can_record_a_stage(self):
        response = self.client.post(self.url, {
            'stage': 'education', 'status': 'in_progress', 'hours_completed': 12, 'remarks': 'Started',
        })
        self.assertRedirects(response, self.inmate.get_absolute_url())
        record = ProgressRecord.objects.get(inmate=self.inmate)
        self.assertEqual(record.recorded_by, self.staff)

    def test_completed_stage_needs_a_completion_date(self):
        response = self.client.post(self.url, {
            'stage': 'education', 'status': 'completed', 'hours_completed': 40,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProgressRecord.objects.count(), 0)

    def test_same_stage_cannot_be_recorded_twice(self):
        make_record(self.inmate, self.staff)
        response = self.client.post(self.url, {
            'stage': 'education', 'status': 'in_progress', 'hours_completed': 1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProgressRecord.objects.count(), 1)

    def test_progress_percent_counts_completed_stages(self):
        make_record(self.inmate, self.staff, stage='education', status='completed',
                    completed_on=date(2025, 6, 1))
        make_record(self.inmate, self.staff, stage='skills', status='in_progress')
        self.assertEqual(self.inmate.completed_stage_count, 1)
        self.assertEqual(self.inmate.progress_percent, 17)

    def test_staff_can_edit_and_delete_a_record(self):
        record = make_record(self.inmate, self.staff)
        self.client.post(reverse('pipeline:progress_edit', args=[record.pk]), {
            'stage': 'education', 'status': 'in_progress', 'hours_completed': 30,
        })
        record.refresh_from_db()
        self.assertEqual(record.hours_completed, 30)
        self.client.post(reverse('pipeline:progress_delete', args=[record.pk]))
        self.assertFalse(ProgressRecord.objects.filter(pk=record.pk).exists())

    def test_detail_and_list_pages_render(self):
        make_record(self.inmate, self.staff)
        self.assertEqual(self.client.get(self.inmate.get_absolute_url()).status_code, 200)
        self.assertEqual(self.client.get(reverse('pipeline:inmate_list')).status_code, 200)


class ProgressAccessTests(TestCase):
    def setUp(self):
        self.owner = make_user('owner')
        self.inmate = make_inmate(self.owner)
        self.record = make_record(self.inmate, self.owner)

    def test_another_staff_cannot_change_the_record(self):
        make_user('other')
        self.client.login(username='other', password=PASSWORD)
        response = self.client.post(reverse('pipeline:progress_delete', args=[self.record.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(ProgressRecord.objects.filter(pk=self.record.pk).exists())

    def test_reviewer_can_view_but_not_record(self):
        make_user('rev', role=User.Role.REVIEWER)
        self.client.login(username='rev', password=PASSWORD)
        self.assertEqual(self.client.get(self.inmate.get_absolute_url()).status_code, 200)
        response = self.client.post(
            reverse('pipeline:progress_create', args=[self.inmate.pk]),
            {'stage': 'skills', 'status': 'in_progress', 'hours_completed': 1},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ProgressRecord.objects.count(), 1)
