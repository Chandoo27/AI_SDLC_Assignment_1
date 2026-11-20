from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from reminder_agent.models import ResolutionContext


@pytest.fixture
def context() -> ResolutionContext:
    return ResolutionContext(
        reference_time=datetime(2026, 11, 19, 9, 0, tzinfo=ZoneInfo("Asia/Kolkata")),
        timezone="Asia/Kolkata",
        reminder_tasks=("pay electricity bill", "attend project review"),
    )
