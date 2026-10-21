"""Session boundary: safe public failures, rollback, no migration credentials."""
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.exc import DBAPIError, IntegrityError, StatementError
from sqlalchemy.orm import sessionmaker

from app.settings.config import DatabaseConfig


class DatabaseUnavailable(RuntimeError):
    def __init__(self):
        super().__init__("Database tidak dapat diakses. Periksa koneksi dan coba lagi.")


class DataConflict(ValueError):
    def __init__(self):
        super().__init__("Data bertentangan dengan data yang tersimpan atau relasi yang diwajibkan.")


class DataValidationError(ValueError):
    pass


def create_database_engine(config: DatabaseConfig, *, schema=None):
    options = "-c timezone=UTC -c statement_timeout=10000 -c lock_timeout=3000"
    if schema is not None:
        import re
        if not re.fullmatch(r"stage3_test_[a-f0-9]+", schema):
            raise ValueError("Schema uji tidak valid.")
        options += f" -c search_path={schema},public"
    url = URL.create("postgresql+psycopg", username=config.user, password=config.password,
                     host=config.host, port=config.port, database=config.name)
    return create_engine(url, hide_parameters=True, pool_pre_ping=True,
                         connect_args={"connect_timeout": 3, "options": options})


class Database:
    def __init__(self, engine):
        self.engine = engine
        self.sessions = sessionmaker(bind=engine, expire_on_commit=False)

    @contextmanager
    def transaction(self):
        try:
            with self.sessions.begin() as session:
                yield session
        except IntegrityError:
            raise DataConflict() from None
        except DBAPIError:
            raise DatabaseUnavailable() from None
        except StatementError:
            raise DataValidationError("Data tidak sesuai tipe atau dimensi yang diwajibkan.") from None

    def close(self):
        self.engine.dispose()
