import json

import pytest
from werkzeug.test import Client
from werkzeug.wrappers import Response

from .custom_asserts import assert_response


def test_response_contract_preserves_exact_and_substring_assertions() -> None:
    payload = {"status": "success", "data": [], "count": 0, "enabled": False}
    response = Client(Response(json.dumps(payload), status=201)).get("/")
    assert (
        assert_response(
            response, 201, status="success", data=[], count=0, enabled=False
        )
        == payload
    )
    assert assert_response(response, 201, contains={"status": "success"})

    for status, fields in [
        (200, {}),
        (201, {"status": "suc"}),
        (201, {"data": [1]}),
        (201, {"count": 1}),
        (201, {"enabled": True}),
        (201, {"contains": {"status": "error"}}),
    ]:
        with pytest.raises(AssertionError):
            assert_response(response, status, **fields)

    with pytest.raises(KeyError):
        assert_response(response, 201, missing=None)
    with pytest.raises(json.JSONDecodeError):
        assert_response(Client(Response("not JSON")).get("/"), 200)

    # Existing substring contracts stay distinct from exact equality contracts.
    extended = Client(
        Response(json.dumps({"status": "success with details"}))
    ).get("/")
    assert assert_response(extended, 200, contains={"status": "success"})
    with pytest.raises(AssertionError):
        assert_response(extended, 200, status="success")
