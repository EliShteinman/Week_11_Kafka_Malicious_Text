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
                logger.error("URI must be provided on first initialization")
                raise ValueError("URI must be provided on first initialization")
            logger.debug("Creating new MongoDB client singleton instance")
            cls._instance = super().__new__(cls)
        else:
            logger.debug("Returning existing MongoDB client singleton instance")
        return cls._instance

    def __init__(self, uri=None, db_name=None, collection_name=None, *args, **kwargs):
        if not hasattr(self, '_initialized'):
            uri_display = (uri[:20] + "..." if len(uri) > 20 else uri) if uri else "None"

            logger.info(
                f"Initializing MongoDB client - URI: {uri_display}, DB:"
                f" {db_name}, Collection: {collection_name}"
            )
            super().__init__(uri, *args, **kwargs)
            self._connection_info = {
                'uri': uri,
                'db_name': db_name,
                'collection_name': collection_name
            }
            self._initialized = True
            logger.info(f"MongoDB client initialized successfully")
        else:
            logger.debug("MongoDB client already initialized, skipping initialization")

    async def connect_and_verify(self):
        try:
            logger.info("Attempting to verify MongoDB connection...")
            await self.admin.command("ping")
            logger.info("MongoDB connection verified successfully")
            return True
        except PyMongoError as e:
            logger.error(f"MongoDB connection verification failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during MongoDB connection verification: {e}")
            return False

    def is_connected(self) -> bool:
        connected = hasattr(self, '_initialized') and self._initialized
        logger.debug(f"MongoDB connection status check: {'Connected' if connected else 'Not connected'}")
        return connected

    def get_collection(self, db_name=None, collection_name=None):
        if not self.is_connected():
            logger.error("MongoDB client not initialized - cannot get collection")
            raise RuntimeError("MongoDB client not initialized")

        final_db_name = db_name or self._connection_info['db_name']
        final_collection_name = collection_name or self._connection_info['collection_name']
        if not final_db_name:
            logger.error("DB name must be provided either in init or method call")
            raise ValueError("DB name must be provided either in init or method call")

        if not final_collection_name:
            logger.error("Collection name must be provided either in init or method call")
            raise ValueError("Collection name must be provided either in init or method call")
        logger.debug(f"Getting collection: {final_db_name}.{final_collection_name}")
        return self[final_db_name][final_collection_name]

    def get_connection_info(self) -> dict:
        if not self.is_connected():
            logger.debug("MongoDB client not initialized - returning not_initialized status")
            return {"status": "not_initialized"}
        logger.debug("Returning MongoDB connection info")
        return self._connection_info

    async def health_check(self) -> dict:
        if not self.is_connected():
            logger.warning("Health check called on uninitialized MongoDB client")
            return {"status": "not_initialized"}

        try:
            logger.debug("Performing MongoDB health check...")
            await self.admin.command("ping")
            server_info = await self.admin.command("buildinfo")

            health_status = {
                "status": "healthy",
                "mongodb_version": server_info.get("version", "unknown"),
                "connection": "active",
                **self._connection_info
            }

            logger.info(f"MongoDB health check successful - Version: {health_status['mongodb_version']}")
            return health_status

        except PyMongoError as e:
            logger.error(f"MongoDB health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error during MongoDB health check: {e}")
            return {
                "status": "unhealthy",
                "error": f"Unexpected error: {str(e)}"
            }