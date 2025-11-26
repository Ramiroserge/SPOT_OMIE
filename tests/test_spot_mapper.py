import pytest
from app.spot_mapper import map_spot_to_omie, fetch_spot_products
from unittest.mock import patch, MagicMock


def test_map_spot_to_omie_basic_case():
    input_product = {
        "ProdReference": "TEST123",
        "Name": "Copo Térmico",
        "Colors": "Preto",
        "Description": "Copo térmico de alta qualidade",
        "Taric": "12345678",
        "Weight": 390,
    }

    expected_output = {
        "codigo": "TEST123",
        "codigo_produto_integracao": "TEST123",
        "descricao": "Copo Térmico - Cor: Preto",
        "descr_detalhada": "Copo térmico de alta qualidade",
        "ncm": "12345678",
        "peso_bruto": 0.39,
        "unidade": "UN",
        "importado_api": "S"
    }

    result = map_spot_to_omie(input_product)
    assert result == expected_output


def test_map_spot_to_omie_missing_fields():
    spot_product = {
        "ProdReference": "XYZ123",
        "Name": "Chaveiro"
    }

    with pytest.raises(AttributeError):
        map_spot_to_omie(spot_product)


def test_map_spot_to_omie_empty_color():
    spot_product = {
        "ProdReference": "EMPTY1",
        "Name": "Produto Sem Cor",
        "Colors": "   ",
        "Description": "Produto sem cor definida",
        "Taric": "00000000",
        "Weight": 100,
    }

    result = map_spot_to_omie(spot_product)
    assert "Cor: " in result["descricao"]


def test_map_spot_to_omie_zero_price():
    spot_product = {
        "ProdReference": "ZERO001",
        "Name": "Produto Grátis",
        "Colors": "Verde",
        "Description": "Brinde promocional",
        "Taric": "99999999",
        "Weight": 0,
    }

    result = map_spot_to_omie(spot_product)
    assert result["peso_bruto"] == 0.0


def test_map_spot_to_omie_cor_none():
    product = {
        "ProdReference": "NULL1",
        "Name": "Produto Sem Cor",
        "Colors": None,
        "Description": "Descrição padrão",
        "Taric": "11111111",
        "Weight": 250,
    }

    with pytest.raises(AttributeError):
        map_spot_to_omie(product)


def test_map_spot_to_omie_all_fields_missing():
    product = {
        "ProdReference": "EDGE123"
    }

    with pytest.raises(AttributeError):
        map_spot_to_omie(product)


@patch("app.spot_mapper.pd.DataFrame.to_csv")
def test_fetch_spot_products(mock_to_csv):
    mock_spot_client = MagicMock()
    mock_spot_client.fetch_products.return_value = {
        "Products": [
            {"ProdReference": "P1", "Name": "Produto 1", "Colors": "Azul", "Description": "Teste", "Taric": "123", "Weight": 100},
            {"ProdReference": "P2", "Name": "Produto 2", "Colors": "Verde", "Description": "Outro", "Taric": "456", "Weight": 200},
        ]
    }

    result = fetch_spot_products(mock_spot_client)

    assert len(result) == 2
    mock_spot_client.fetch_products.assert_called_once()
    mock_to_csv.assert_called_once()


@patch("app.spot_mapper.pd.DataFrame.to_csv")
def test_fetch_spot_products_empty(mock_csv):
    mock_spot = MagicMock()
    mock_spot.fetch_products.return_value = {"Products": []}

    result = fetch_spot_products(mock_spot)

    assert result == []
    mock_csv.assert_not_called()
