from typing import Protocol


class AlembicConfig(Protocol):
    def set_main_option(self, name: str, value: str) -> None: ...


def normalize_database_url(database_url: str) -> str:
    """Select Psycopg 3 for bare PostgreSQL URLs without changing other URLs."""
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    return database_url


def configure_alembic_database_url(config: AlembicConfig, database_url: str) -> str:
    normalized = normalize_database_url(database_url)
    # Alembic uses ConfigParser interpolation, so URL-encoded percent signs
    # must be escaped while being assigned programmatically.
    config.set_main_option("sqlalchemy.url", normalized.replace("%", "%%"))
    return normalized
