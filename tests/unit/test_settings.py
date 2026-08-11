import pytest
from openstory_api.dependencies import Settings


def test_settings_accept_comma_delimited_cors_origins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "OPENSTORY_CORS_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    )

    settings = Settings()

    assert settings.cors_origins == [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ]
