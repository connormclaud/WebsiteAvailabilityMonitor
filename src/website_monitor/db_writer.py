from abc import ABC, abstractmethod
import asyncpg


class DatabaseWriter(ABC):
    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def execute(self, query, *params):
        pass

    @abstractmethod
    async def close(self):
        pass


class PostgresWriter(DatabaseWriter):
    def __init__(self, dsn):
        self._dsn = dsn
        self._conn = None

    async def connect(self):
        self._conn = await asyncpg.connect(self._dsn)

    async def execute(self, query, *params):
        if not self._conn:
            raise RuntimeError("Database connection not established")
        await self._conn.execute(query, *params)

    async def close(self):
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()


class DatabaseWriterFactory:
    @staticmethod
    def get_writer(writer_type, dsn):
        if writer_type == 'postgres':
            return PostgresWriter(dsn)
        else:
            raise ValueError(f"Unsupported writer type: {writer_type}")
