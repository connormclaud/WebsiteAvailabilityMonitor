import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from website_monitor.db_writer import DatabaseWriter, PostgresWriter, DatabaseWriterFactory

dsn = "postgresql://user:password@localhost/dbname"
query = "INSERT INTO my_table (column1, column2) VALUES ($1, $2)"
params = ("value1", "value2")


def test_database_writer_abstract_methods():
    with pytest.raises(TypeError):
        DatabaseWriter()


@pytest.mark.asyncio
async def test_postgres_writer_connect():
    with patch("asyncpg.connect", new_callable=AsyncMock) as mock_connect:
        writer = PostgresWriter(dsn)

        await writer.connect()

        mock_connect.assert_called_once_with(dsn)


@pytest.mark.asyncio
async def test_postgres_writer_write():
    with patch("asyncpg.connect", new_callable=AsyncMock) as mock_connect:
        mock_execute = AsyncMock()
        mock_conn = MagicMock()
        mock_conn.execute = mock_execute
        mock_connect.return_value = mock_conn

        writer = PostgresWriter(dsn)
        await writer.connect()

        await writer.write(query, *params)

        mock_execute.assert_called_once_with(query, *params)


@pytest.mark.asyncio
async def test_postgres_writer_close():
    with patch("asyncpg.connect") as mock_connect:
        mock_close = AsyncMock()
        mock_conn = MagicMock()
        mock_conn.close = mock_close
        mock_connect.return_value = mock_conn

        writer = PostgresWriter(dsn)
        await writer.connect()

        await writer.close()

        mock_close.assert_called_once()


@pytest.mark.asyncio
async def test_postgres_writer_write_without_connect():
    writer = PostgresWriter(dsn)

    with pytest.raises(RuntimeError, match="Database connection not established"):
        await writer.write(query, *params)


def test_get_postgres_writer():
    writer_type = "postgres"

    writer = DatabaseWriterFactory.get_writer(writer_type, dsn)

    assert isinstance(writer, PostgresWriter)


def test_get_unsupported_writer():
    writer_type = "unsupported"

    with pytest.raises(ValueError) as exc_info:
        DatabaseWriterFactory.get_writer(writer_type, dsn)

    assert str(exc_info.value) == f"Unsupported writer type: {writer_type}"
