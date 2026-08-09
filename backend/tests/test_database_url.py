from alembic.config import Config
from sqlalchemy.engine import make_url

from app.db.database_url import configure_alembic_database_url, normalize_database_url
from app.db.session import create_database_engine


def test_database_url_normalization() -> None:
    cases = {
        "postgresql://user:password@host:5432/database": "postgresql+psycopg://user:password@host:5432/database",
        "postgres://user:password@host:5432/database": "postgresql+psycopg://user:password@host:5432/database",
        "postgresql+psycopg://user:password@host:5432/database": "postgresql+psycopg://user:password@host:5432/database",
        "sqlite:///./test.sqlite3": "sqlite:///./test.sqlite3",
    }
    for supplied, expected in cases.items():
        assert normalize_database_url(supplied) == expected


def test_application_and_alembic_use_the_same_normalized_url() -> None:
    supplied = "postgresql://user:p%40ssword@host:5432/database"
    expected = normalize_database_url(supplied)

    engine = create_database_engine(supplied)
    try:
        assert engine.url.drivername == "postgresql+psycopg"
        assert make_url(expected).drivername == engine.url.drivername
    finally:
        engine.dispose()

    config = Config()
    assert configure_alembic_database_url(config, supplied) == expected
    assert config.get_main_option("sqlalchemy.url") == expected
