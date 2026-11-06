from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="viewer", password="SecureTest123!")

    def test_requires_bearer_token(self):
        result = self.client.get("/api/events/")
        self.assertEqual(result.status_code, 401)
        self.assertEqual(result["WWW-Authenticate"], "Bearer")

    def test_login_returns_token(self):
        result = self.client.post("/api/auth/login/", {
            "username": "viewer", "password": "SecureTest123!",
        }, format="json")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["token"], Token.objects.get(user=self.user).key)

    def test_invalid_credentials_rejected(self):
        result = self.client.post("/api/auth/login/", {
            "username": "viewer", "password": "wrong",
        }, format="json")
        self.assertEqual(result.status_code, 401)

    def test_bearer_token_works(self):
        token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
        self.assertEqual(self.client.get("/api/events/").status_code, 200)
