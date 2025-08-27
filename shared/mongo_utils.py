# shared/database/connection.py
import logging
from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)


class SingletonMongoClient(AsyncMongoClient):
    _instance = None
    _connection_info = None

    def __new__(cls, uri=None, db_name=None, collection_name=None, *args, **kwargs):
        if cls._instance is None:
            if uri is None:
                raise ValueError("URI, db_name, and collection_name must be provided on first initialization")
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, uri=None, db_name=None, collection_name=None, *args, **kwargs):
        if not hasattr(self, '_initialized'):
            super().__init__(uri, *args, **kwargs)
            self._connection_info = {
                'uri': uri,
                'db_name': db_name,
                'collection_name': collection_name
            }
            self._initialized = True
            logger.info(f"MongoDB client initialized: {uri}, DB: {db_name}, Collection: {collection_name}")

    async def connect_and_verify(self):
        try:
            await self.admin.command("ping")
            logger.info("MongoDB connection verified successfully")
            return True
        except PyMongoError as e:
            logger.error(f"MongoDB connection failed: {e}")
            return False

    def is_connected(self) -> bool:
        return hasattr(self, '_initialized') and self._initialized

    def get_collection(self):
        if not self.is_connected():
            raise RuntimeError("MongoDB client not initialized")

        db_name = self._connection_info['db_name']
        collection_name = self._connection_info['collection_name']
        return self[db_name][collection_name]

    def get_custom_collection(self, db_name, collection_name):
        if not self.is_connected():
            raise RuntimeError("MongoDB client not initialized")
        return self[db_name][collection_name]

    def get_connection_info(self) -> dict:
        if not self.is_connected():
            return {"status": "not_initialized"}
        return self._connection_info

    async def health_check(self) -> dict:
        if not self.is_connected():
            return {"status": "not_initialized"}

        try:
            await self.admin.command("ping")
            server_info = await self.admin.command("buildinfo")

            return {
                "status": "healthy",
                "mongodb_version": server_info.get("version", "unknown"),
                "connection": "active",
                **self._connection_info
            }
        except PyMongoError as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }