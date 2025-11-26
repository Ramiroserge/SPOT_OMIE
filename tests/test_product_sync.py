from app.product_sync import sync_products
from unittest.mock import patch, MagicMock

@patch("app.product_sync.SpotClient")
@patch("app.product_sync.OmieClient")
def test_sync_products_inserts_only_new(mock_omie_cls, mock_spot_cls):
    mock_spot = MagicMock()
    mock_spot.fetch_products.return_value = {
        "Products": [
            {"ProdReference": "A1", "Name": "Produto Novo", "Colors": "Azul", "PrecoVenda": 10.0},
            {"ProdReference": "B2", "Name": "Produto Existente", "Colors": "Preto", "PrecoVenda": 20.0}
        ]
    }
    mock_spot_cls.return_value = mock_spot

    mock_omie = MagicMock()
    mock_omie.list_products.return_value = [{"codigo_produto_integracao": "B2"}]
    mock_omie_cls.return_value = mock_omie

    sync_products("fake", "app_key", "secret", dry_run=False, preview_count=2)

    mock_omie.insert_product.assert_called_once()
    inserted = mock_omie.insert_product.call_args[0][0]
    assert inserted["codigo"] == "A1"


@patch("app.product_sync.SpotClient")
@patch("app.product_sync.OmieClient")
def test_sync_products_skips_existing(mock_omie_cls, mock_spot_cls):
    mock_spot = MagicMock()
    mock_spot.fetch_products.return_value = {
        "Products": [{"ProdReference": "DUP123", "Name": "Produto Existente", "Colors": "Azul", "PrecoVenda": 15.0}]
    }
    mock_spot_cls.return_value = mock_spot

    mock_omie = MagicMock()
    mock_omie.list_products.return_value = [{"codigo_produto_integracao": "DUP123"}]
    mock_omie_cls.return_value = mock_omie

    sync_products("fake", "app_key", "secret", dry_run=False, preview_count=1)

    mock_omie.insert_product.assert_not_called()


@patch("app.product_sync.SpotClient")
@patch("app.product_sync.OmieClient")
def test_sync_products_inserts_new_product(mock_omie_cls, mock_spot_cls):
    mock_spot = MagicMock()
    mock_spot.fetch_products.return_value = {
        "Products": [{"ProdReference": "NEW456", "Name": "Produto Novo", "Colors": "Preto", "PrecoVenda": 20.0}]
    }
    mock_spot_cls.return_value = mock_spot

    mock_omie = MagicMock()
    mock_omie.list_products.return_value = []
    mock_omie_cls.return_value = mock_omie

    sync_products("fake", "app_key", "secret", dry_run=False, preview_count=1)

    mock_omie.insert_product.assert_called_once()
    inserted = mock_omie.insert_product.call_args[0][0]
    assert inserted["codigo"] == "NEW456"
    assert "Preto" in inserted["descricao"]


@patch("app.product_sync.SpotClient")
@patch("app.product_sync.OmieClient")
def test_sync_products_skips_missing_code_and_existing(mock_omie_cls, mock_spot_cls):
    mock_spot = MagicMock()
    mock_spot.fetch_products.return_value = {
        "Products": [
            {"ProdReference": "ABC123", "Name": "Produto A", "Colors": "Azul", "PrecoVenda": 30.0},
            {},  # missing code
            {"ProdReference": "ABC123"}  # already exists
        ]
    }
    mock_spot_cls.return_value = mock_spot

    mock_omie = MagicMock()
    mock_omie.list_products.return_value = [{"codigo_produto_integracao": "ABC123"}]
    mock_omie_cls.return_value = mock_omie

    sync_products("fake", "app_key", "secret", dry_run=False, preview_count=3)

    mock_omie.insert_product.assert_not_called()


@patch("app.product_sync.SpotClient")
@patch("app.product_sync.OmieClient")
def test_sync_products_skips_missing_integration_code(mock_omie_cls, mock_spot_cls):
    mock_spot = MagicMock()
    mock_spot.fetch_products.return_value = {
        "Products": [{"Name": "Produto sem código"}]
    }
    mock_spot_cls.return_value = mock_spot

    mock_omie = MagicMock()
    mock_omie.list_products.return_value = []
    mock_omie_cls.return_value = mock_omie

    sync_products("fake", "app_key", "secret", dry_run=False, preview_count=1)

    mock_omie.insert_product.assert_not_called()
@patch("app.product_sync.SpotClient")
@patch("app.product_sync.OmieClient")
def test_sync_products_dry_run(mock_omie_cls, mock_spot_cls):
    mock_spot = MagicMock()
    mock_spot.fetch_products.return_value = {
        "Products": [
            {"ProdReference": "ABC123", "Name": "Caneca", "Colors": "Branco", "Description": "Copo simples", "Taric": "12345678", "Weight": 100}
        ]
    }
    mock_spot_cls.return_value = mock_spot

    mock_omie = MagicMock()
    mock_omie.list_products.return_value = []
    mock_omie_cls.return_value = mock_omie

    sync_products(
        spot_key="dummy_spot",
        omie_app_key="key",
        omie_app_secret="secret",
        dry_run=True,
        preview_count=1
    )

    mock_omie.insert_product.assert_not_called()
    mock_spot.fetch_products.assert_called_once()

@patch("app.product_sync.SpotClient")
@patch("app.product_sync.OmieClient")
def test_sync_products_handles_insert_failure(mock_omie_cls, mock_spot_cls):
    mock_spot = MagicMock()
    mock_spot.fetch_products.return_value = {
        "Products": [
            {
                "ProdReference": "ERR123",
                "Name": "Erro",
                "Colors": "Vermelho",
                "Description": "Falha intencional",
                "Taric": "12345678",
                "Weight": 500
            }
        ]
    }
    mock_spot_cls.return_value = mock_spot

    mock_omie = MagicMock()
    mock_omie.list_products.return_value = []
    mock_omie.insert_product.side_effect = Exception("Simulated failure")
    mock_omie_cls.return_value = mock_omie

    # No exception should propagate
    sync_products("fake", "key", "secret", dry_run=False, preview_count=1)

    mock_omie.insert_product.assert_called_once()

@patch("app.product_sync.pd.DataFrame.to_csv")
@patch("app.product_sync.SpotClient")
@patch("app.product_sync.OmieClient")
def test_sync_products_handles_ncm_missing(mock_omie_cls, mock_spot_cls, mock_csv):
    mock_spot = MagicMock()
    mock_spot.fetch_products.return_value = {
        "Products": [
            {
                "ProdReference": "NCMFAIL",
                "Name": "Produto",
                "Colors": "Azul",
                "Description": "Teste",
                "Taric": "1234",
                "Weight": 123
            }
        ]
    }
    mock_spot_cls.return_value = mock_spot

    mock_omie = MagicMock()
    mock_omie.list_products.return_value = []
    mock_omie.insert_product.return_value = {
        "faultcode": "123",
        "faultstring": "NCM não cadastrada"
    }
    mock_omie_cls.return_value = mock_omie

    sync_products("key", "key", "secret", dry_run=False, preview_count=1)

    mock_csv.assert_called_once()

@patch("app.product_sync.pd.DataFrame.to_csv")
@patch("app.product_sync.SpotClient")
@patch("app.product_sync.OmieClient")
def test_sync_products_handles_fatal_fault(mock_omie_cls, mock_spot_cls, mock_csv):
    mock_spot = MagicMock()
    mock_spot.fetch_products.return_value = {
        "Products": [{
            "ProdReference": "FATAL",
            "Name": "Erro grave",
            "Colors": "Vermelho",
            "Description": "Falhou tudo",
            "Taric": "00000000",
            "Weight": 100
        }]
    }
    mock_spot_cls.return_value = mock_spot

    mock_omie = MagicMock()
    mock_omie.list_products.return_value = []
    mock_omie.insert_product.return_value = {
        "faultcode": "CLIENT-999",
        "faultstring": "Erro fatal"
    }
    mock_omie_cls.return_value = mock_omie

    sync_products("key", "key", "key", dry_run=False, preview_count=1)

    mock_omie.insert_product.assert_called_once()
    mock_csv.assert_not_called()
