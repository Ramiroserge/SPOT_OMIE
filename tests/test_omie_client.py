import pytest
from unittest.mock import patch, MagicMock
from app.omie_client import OmieClient
import requests


@pytest.fixture
def omie_client():
    return OmieClient(app_key="dummy_key", app_secret="dummy_secret")


@patch("app.omie_client.requests.post")
def test_insert_product_success(mock_post, omie_client):
    dummy_response = {
        "codigo": "ABC123",
        "codigo_produto_integracao": "ABC123",
        "descricao": "Copo Térmico - Cor: Preto - Codigo: ABC123"
    }

    mock_post.return_value = MagicMock(status_code=200, json=lambda: dummy_response)

    product_data = {
        "codigo": "ABC123",
        "codigo_produto_integracao": "ABC123",
        "descricao": "Copo Térmico - Cor: Preto - Codigo: ABC123",
        "descr_detalhada": "Copo térmico de alta qualidade",
        "ncm": "12345678",
        "peso_bruto": 0.390,
        "unidade": "UN",
        "importado_api": "S"
    }

    result = omie_client.insert_product(product_data)
    assert result == dummy_response
    mock_post.assert_called_once()


@patch("app.omie_client.requests.post")
def test_insert_product_with_faultstring(mock_post, omie_client):
    mock_post.return_value = MagicMock(status_code=200, json=lambda: {
        "faultstring": "Duplicate product"
    })

    product_data = {
        "codigo": "ABC123",
        "codigo_produto_integracao": "ABC123",
        "descricao": "Produto duplicado - Cor: Preto - Codigo: ABC123",
        "descr_detalhada": "Produto duplicado",
        "ncm": "12345678",
        "peso_bruto": 0.5,
        "unidade": "UN",
        "importado_api": "S"
    }

    result = omie_client.insert_product(product_data)
    assert result is None


@patch("app.omie_client.requests.post")
def test_insert_product_http_error(mock_post, omie_client):
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.raise_for_status.side_effect = Exception("Internal Server Error")
    mock_post.return_value = mock_resp

    product_data = {
        "codigo": "X",
        "codigo_produto_integracao": "X",
        "descricao": "Erro de servidor - Cor: Preto - Codigo: X",
        "descr_detalhada": "Falha",
        "ncm": "00000000",
        "peso_bruto": 0.1,
        "unidade": "UN",
        "importado_api": "S"
    }

    with pytest.raises(Exception):
        omie_client.insert_product(product_data)


@patch("app.omie_client.requests.post")
def test_list_products_with_multiple_pages(mock_post):
    client = OmieClient("key", "secret")

    # Page 1
    page1 = {
        "produto_servico_cadastro": [{"codigo_produto_integracao": "A"}],
        "total_de_paginas": 2
    }

    # Page 2
    page2 = {
        "produto_servico_cadastro": [{"codigo_produto_integracao": "B"}],
        "total_de_paginas": 2
    }

    mock_post.side_effect = [
        MagicMock(status_code=200, json=lambda: page1),
        MagicMock(status_code=200, json=lambda: page2),
    ]

    result = client.list_products()
    assert len(result) == 2
    assert result[0]["codigo_produto_integracao"] == "A"
    assert result[1]["codigo_produto_integracao"] == "B"


@patch("app.omie_client.requests.post")
def test_list_products_handles_no_products(mock_post):
    client = OmieClient("key", "secret")
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"total_de_paginas": 1}  # no `produto_servico_cadastro`
    )

    result = client.list_products()
    assert result == []  # still safe

@patch("app.omie_client.requests.post")
def test_list_products_http_error(mock_post):
    client = OmieClient("key", "secret")

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Erro de servidor"
    mock_resp.raise_for_status.side_effect = requests.HTTPError("boom")
    mock_post.return_value = mock_resp

    result = client.list_products()
    assert result == []  # safe exit

def test_build_auth_and_headers():
    client = OmieClient("KEY", "SECRET")
    assert client._build_headers() == {"Content-Type": "application/json"}
    assert client._build_auth_payload() == {"app_key": "KEY", "app_secret": "SECRET"}

@patch("app.omie_client.requests.post")
def test_list_products_with_debug_logs(mock_post, caplog):
    client = OmieClient("key", "secret")
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "produto_servico_cadastro": [{"codigo_produto_integracao": "ABC"}],
            "total_de_paginas": 1
        }
    )

    with caplog.at_level("DEBUG"):
        result = client.list_products()
        assert "First product" in caplog.text
        assert "Number of products" in caplog.text
        assert result[0]["codigo_produto_integracao"] == "ABC"

@patch("app.omie_client.requests.post")
def test_list_products_logs_debug_info(mock_post, caplog):
    client = OmieClient("key", "secret")

    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "produto_servico_cadastro": [{"codigo_produto_integracao": "XYZ"}],
            "total_de_paginas": 1
        }
    )

    with caplog.at_level("DEBUG"):
        result = client.list_products()
        assert "First product" in caplog.text
        assert "Number of products" in caplog.text
        assert result[0]["codigo_produto_integracao"] == "XYZ"

@patch("app.omie_client.requests.post")
def test_list_products_http_error_handling(mock_post, caplog):
    client = OmieClient("key", "secret")

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Something went wrong"
    mock_response.raise_for_status.side_effect = requests.HTTPError("Boom")

    mock_post.return_value = mock_response

    with caplog.at_level("WARNING"):
        result = client.list_products()
        assert result == []
        assert "OMIE error on ListarProdutos" in caplog.text
        assert "Skipping remaining pages due to error" in caplog.text
