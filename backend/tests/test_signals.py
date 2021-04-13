import pytest
import backend.signals
from backend.models import Chat, User


@pytest.mark.django_db(transaction=True)
def test_signals():
    test : User = User.objects.create_user(username="test_user", password="testpassword123")
    assert test.auth_token.exists()