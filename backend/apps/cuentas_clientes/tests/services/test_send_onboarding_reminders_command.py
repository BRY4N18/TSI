import pytest
from io import StringIO

from django.core.management import call_command


@pytest.mark.service
class TestSendOnboardingRemindersCommand:
    def test_command_runs_successfully(self, mock_pinot, mock_kafka):
        # Arrange
        out = StringIO()

        # Act
        call_command("send_onboarding_reminders", stdout=out)

        # Assert
        assert "reminder" in out.getvalue().lower()
