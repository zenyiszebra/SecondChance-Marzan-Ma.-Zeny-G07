from django.test import TestCase
from django.urls import reverse

from .models import User

PASSWORD = 'S3cure-Pass!word'


def make_user(username, role=User.Role.STAFF, **extra):
    return User.objects.create_user(
        username=username, email=f'{username}@example.com', password=PASSWORD, role=role, **extra
    )


class RegistrationTests(TestCase):
    def data(self, **extra):
        base = {
            'first_name': 'Ana', 'last_name': 'Cruz', 'username': 'anacruz',
            'email': 'ana@example.com', 'contact_number': '09171234567',
            'role': 'staff', 'password1': PASSWORD, 'password2': PASSWORD,
        }
        base.update(extra)
        return base

    def test_register_creates_user_with_hashed_password(self):
        response = self.client.post(reverse('accounts:register'), self.data())
        self.assertRedirects(response, reverse('accounts:login'))
        user = User.objects.get(username='anacruz')
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(user.role, 'staff')

    def test_duplicate_email_is_rejected(self):
        make_user('existing')
        response = self.client.post(
            reverse('accounts:register'), self.data(email='EXISTING@example.com')
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='anacruz').exists())

    def test_password_mismatch_is_rejected(self):
        response = self.client.post(reverse('accounts:register'), self.data(password2='different'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='anacruz').exists())

    def test_invalid_email_is_rejected(self):
        response = self.client.post(reverse('accounts:register'), self.data(email='not-an-email'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='anacruz').exists())

    def test_admin_role_cannot_be_self_selected(self):
        response = self.client.post(reverse('accounts:register'), self.data(role='admin'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='anacruz').exists())


class LoginLogoutTests(TestCase):
    def test_login_redirects_to_role_dashboard(self):
        make_user('reviewer1', role=User.Role.REVIEWER)
        response = self.client.post(
            reverse('accounts:login'), {'username': 'reviewer1', 'password': PASSWORD}
        )
        self.assertRedirects(
            response, reverse('accounts:dashboard'), fetch_redirect_response=False
        )
        self.assertRedirects(
            self.client.get(reverse('accounts:dashboard')),
            reverse('accounts:reviewer_dashboard'),
        )

    def test_invalid_credentials_show_error(self):
        response = self.client.post(
            reverse('accounts:login'), {'username': 'nobody', 'password': 'wrong'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')

    def test_logout_ends_session(self):
        make_user('staff1')
        self.client.login(username='staff1', password=PASSWORD)
        self.client.post(reverse('accounts:logout'))
        response = self.client.get(reverse('accounts:staff_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)


class AccessControlTests(TestCase):
    def test_logged_out_user_is_sent_to_login(self):
        for name in ('staff_dashboard', 'admin_dashboard', 'reviewer_dashboard', 'profile'):
            response = self.client.get(reverse(f'accounts:{name}'))
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse('accounts:login'), response.url)

    def test_user_cannot_open_another_roles_dashboard(self):
        make_user('staff1', role=User.Role.STAFF)
        self.client.login(username='staff1', password=PASSWORD)
        for name in ('admin_dashboard', 'reviewer_dashboard'):
            response = self.client.get(reverse(f'accounts:{name}'))
            self.assertRedirects(
                response, reverse('accounts:staff_dashboard'), fetch_redirect_response=False
            )

    def test_each_role_can_open_its_own_dashboard(self):
        for role in User.Role.values:
            make_user(f'{role}1', role=role)
            self.client.login(username=f'{role}1', password=PASSWORD)
            response = self.client.get(reverse(f'accounts:{role}_dashboard'))
            self.assertEqual(response.status_code, 200)
            self.client.logout()


class ProfileTests(TestCase):
    def test_user_can_update_own_profile(self):
        user = make_user('staff1')
        self.client.login(username='staff1', password=PASSWORD)
        response = self.client.post(reverse('accounts:profile_edit'), {
            'first_name': 'Maria', 'last_name': 'Santos',
            'email': 'maria@example.com', 'contact_number': '09181234567',
        })
        self.assertRedirects(response, reverse('accounts:profile'))
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Maria')
        self.assertEqual(user.email, 'maria@example.com')

    def test_email_used_by_another_account_is_rejected(self):
        make_user('other')
        make_user('staff1')
        self.client.login(username='staff1', password=PASSWORD)
        response = self.client.post(reverse('accounts:profile_edit'), {
            'first_name': 'A', 'last_name': 'B', 'email': 'other@example.com',
        })
        self.assertEqual(response.status_code, 200)

    def test_profile_pages_show_only_own_data(self):
        make_user('staff1', first_name='Mine')
        make_user('staff2', first_name='Theirs')
        self.client.login(username='staff1', password=PASSWORD)
        response = self.client.get(reverse('accounts:profile'))
        self.assertContains(response, 'staff1@example.com')
        self.assertNotContains(response, 'staff2@example.com')
