import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from shared.mongo_utils import SingletonMongoClient

from . import config
from .data_repository import TweetRepository
from .models import TweetModel, TweetResponse

# Setup logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle application startup and shutdown
    """
    logger.info("Application startup: connecting to database...")
    try:
        mongo_client = SingletonMongoClient(
            uri=config.MONGO_URI, db_name=config.MONGO_DB_NAME
        )
        await mongo_client.connect_and_verify()
        logger.info("Database connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

    yield

    logger.info("Application shutdown...")
    try:
        client = SingletonMongoClient()
        client.close()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


app = FastAPI(
    lifespan=lifespan,
    title="Tweet Data Retrieval API",
    version="1.0",
    description="API for retrieving processed tweet data from MongoDB",
)


def get_repository() -> TweetRepository:
    """
    Get repository instance using singleton MongoDB client
    """
    try:
        client = SingletonMongoClient()
        return TweetRepository(client)
    except Exception as e:
        logger.error(f"Failed to get repository: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection not available",
        )


@app.get("/")
def health_check():
    """
    Simple health check endpoint
    """
    return {"status": "ok", "service": "tweet-retrieval-api"}


@app.get("/health")
def detailed_health_check():
    """
    Detailed health check with database status
    """
    try:
        client = SingletonMongoClient()
        database_status = "connected" if client.is_connected() else "disconnected"

        if database_status == "disconnected":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        return {
            "status": "ok",
            "service": "tweet-retrieval-api",
            "version": "1.0",
            "database_status": database_status,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable",
        )


@app.get("/antisemitic", response_model=TweetResponse)
async def get_antisemitic_tweets():
    """
    Retrieve all antisemitic tweets with complete processing information
    """
    try:
        repo = get_repository()
        tweet_dicts = await repo.get_tweets_from_collection(
            config.MONGO_COLLECTION_ANTISEMITIC
        )

        tweet_models = [TweetModel.parse_obj(tweet_dict) for tweet_dict in tweet_dicts]
        return TweetResponse(count=len(tweet_models), data=tweet_models)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving antisemitic tweets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving tweets",
        )


@app.get("/normal", response_model=TweetResponse)
async def get_normal_tweets():
    """
    Retrieve all non-antisemitic tweets with complete processing information
    """
    try:
        repo = get_repository()
        tweet_dicts = await repo.get_tweets_from_collection(
            config.MONGO_COLLECTION_NOT_ANTISEMITIC
        )

        tweet_models = [TweetModel.parse_obj(tweet_dict) for tweet_dict in tweet_dicts]
        return TweetResponse(count=len(tweet_models), data=tweet_models)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving normal tweets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving tweets",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        log_level=config.LOG_LEVEL.lower(),
    )
