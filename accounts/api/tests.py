from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User


LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'
SIGNUP_URL = '/api/accounts/signup/'

class AccountApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = self.create_user(
            username='admin_123',
            email='admin@twitter.com',
            password='correct password',
        )

    def create_user(self, username, email, password):
        return User.objects.create_user(username, email, password)

    # every test starts with 'test_xxxx'
    def test_login(self):
        # check if method == GET
        response = self.client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 405)

        # check if password is correct
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'wrong password',
        })
        self.assertEqual(response.status_code, 400)

        # check not logged in.
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

        # use the correct password
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['user'], None)
        self.assertEqual(response.data['user']['email'], 'admin@twitter.com')

        # check logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

        # check if user exists
        response = self.client.post(LOGIN_URL, {
            'username': 'non-exists',
            'password': 'correct password'
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data['errors']['username'][0]), 'User does not exist.')

    def test_logout(self):
        # login first and check status
        self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

        # check if it is POST request
        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)

        # check with POST and it should return 200
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 200)

        # check not logged out.
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

    def test_signup(self):
        data = {
            'username': 'someone',
            'email': 'someone@twitter.com',
            'password': 'any password',
        }

        # can only accept POST
        response = self.client.get(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 405)

        # test wrong email
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'not a correct email',
            'password': 'any password'
        })
        self.assertEqual(response.status_code, 400)

        # password too short
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'someone@twitter.com',
            'password': '123'
        })
        self.assertEqual(response.status_code, 400)

        # username too long
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone is toooooooooooooooooo longggggggggggggggg',
            'email': 'someone@twitter.com',
            'password': 'any password'
        })
        self.assertEqual(response.status_code, 400)

        # username is already used
        response = self.client.post(SIGNUP_URL, {
            'username': 'admin_123',
            'email': 'xxx@twitter.com',
            'password': 'any password'
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data['errors']['username'][0]), 'This user has been occupied.')

        # email is already used
        response = self.client.post(SIGNUP_URL, {
            'username': 'admin_345',
            'email': 'admin@twitter.com',
            'password': 'any password'
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data['errors']['email'][0]), 'This email address has been occupied.')

        # successful signed up
        response = self.client.post(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'someone')

        # test if it is logged in.
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)