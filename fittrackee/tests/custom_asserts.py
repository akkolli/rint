import json
import re
from typing import Dict, Optional

from werkzeug.test import TestResponse


def assert_response(
    response: TestResponse,
    status_code: int,
    *,
    contains: Optional[Dict] = None,
    **expected: object,
) -> Dict:
    """Check exact HTTP/envelope contracts and return the full JSON payload.

    Only named fields are checked; callers retain their domain assertions.
    Unlike error substring helpers, each expected value must match exactly.
    """
    assert response.status_code == status_code
    data = json.loads(response.data.decode())
    for field, value in (contains or {}).items():
        assert value in data[field], (
            f"missing value in response field: {field}"
        )
    for field, value in expected.items():
        assert data[field] == value, f"unexpected response field: {field}"
    return data


def assert_errored_response(
    response: TestResponse,
    status_code: int,
    error_message: Optional[str] = None,
    status: Optional[str] = "error",
    match: Optional[str] = None,
) -> Dict:
    assert response.content_type == "application/json"
    assert response.status_code == status_code

    data = json.loads(response.data.decode())
    assert status in data["status"]
    if error_message is not None:
        assert error_message in data["message"]
    if match is not None:
        assert re.match(match, data["message"])
    return data


def assert_oauth_errored_response(
    response: TestResponse,
    status_code: int,
    error: str,
    error_description: Optional[str] = None,
) -> Dict:
    assert response.content_type == "application/json"
    assert response.status_code == status_code

    data = json.loads(response.data.decode())
    assert error in data["error"]
    if error_description is not None:
        assert error_description in data["error_description"]
    return data
