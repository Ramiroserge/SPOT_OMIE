import pytest
import requests
from unittest.mock import patch, MagicMock
from app.spot_client import SpotClient

@pytest.fixture
def spot_client():
    return SpotClient(access_key="fake-access-key")

@patch("app.spot_client.requests.get")
def test_fetch_products(mock_get, spot_client):
    mock_response = {
        "products": [
            {"CodigoComposto": "X1", "Nome": "Produto A"},
            {"CodigoComposto": "X2", "Nome": "Produto B"}
        ]
    }

    mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_response)

    result = spot_client.fetch_products()
    assert isinstance(result, dict)
    assert "products" in result
    assert len(result["products"]) == 2

@patch("app.spot_client.requests.get")
def test_authenticate_success(mock_get, spot_client):
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {"Token": "abc123", "ErrorCode": None, "ErrorMessage": None}
    )

    spot_client.authenticate()
    assert spot_client.session_token == "abc123"
    mock_get.assert_called_once_with("http://ws.spotgifts.com.br/api/v1/authenticateclient?AccessKey=fake-access-key")


@patch("app.spot_client.requests.get")
def test_validate_session_valid(mock_get, spot_client):
    spot_client.session_token = "abc123"
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {"Status": 1, "ErrorCode": None, "ErrorMessage": None}
    )

    is_valid = spot_client.validate_session()
    assert is_valid is True
    mock_get.assert_called_once_with("http://ws.spotgifts.com.br/api/v1/validateSession?token=abc123")


@patch("app.spot_client.requests.get")
def test_validate_session_invalid(mock_get, spot_client):
    spot_client.session_token = "abc123"
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {"Status": 0, "ErrorCode": None, "ErrorMessage": None}
    )

    is_valid = spot_client.validate_session()
    assert is_valid is False

@patch("app.spot_client.requests.get")
def test_authenticate_with_error_response(mock_get, spot_client):
    mock_get.return_value = MagicMock(status_code=200, json=lambda: {
        "Token": None,
        "ErrorCode": "401",
        "ErrorMessage": "Unauthorized"
    })

    with pytest.raises(Exception) as e:
        spot_client.authenticate()
    assert "Authentication failed" in str(e.value)

@patch("app.spot_client.requests.get")
def test_authenticate_http_error(mock_get, spot_client):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.raise_for_status.side_effect = Exception("Unauthorized")

    mock_get.return_value = mock_resp

    with pytest.raises(Exception):
        spot_client.authenticate()

@patch("app.spot_client.requests.get")
def test_authenticate_token_missing(mock_get, spot_client):
    mock_get.return_value = MagicMock(status_code=200, json=lambda: {
        "ErrorCode": "403",
        "ErrorMessage": "Token missing"
    })

    with pytest.raises(Exception):
        spot_client.authenticate()

@patch("app.spot_client.requests.get")
def test_fetch_products_http_error(mock_get, spot_client):
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("Server error")
    mock_get.return_value = mock_resp

    with pytest.raises(requests.exceptions.HTTPError):
        spot_client.fetch_products()

@patch("app.spot_client.requests.get")
def test_validate_session_no_token(mock_get, spot_client):
    # Make sure no token is set
    spot_client.session_token = None
    is_valid = spot_client.validate_session()
    assert is_valid is False
    mock_get.assert_not_called()

@patch("app.spot_client.requests.get")
def test_validate_session_invalid_token(mock_get, spot_client):
    spot_client.session_token = "invalid-token"
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {"Status": 0}
    )

    is_valid = spot_client.validate_session()
    assert is_valid is False
    mock_get.assert_called_once()