# services/data_retrieval/models.py (גרסה מתוקנת)
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field, ConfigDict

class TweetModel(BaseModel):
    """
    Pydantic model matching the final schema as defined in the exam requirements.
    This model is used for API response validation and serialization.
    """
    # Note the use of 'alias' to map from MongoDB's '_id' to a clean 'id' in the JSON response.
    id: str = Field(..., alias="_id", description="Document ID from MongoDB")
    createdate: datetime = Field(..., description="Original creation date of the tweet")
    antisemietic: int = Field(..., description="Classification: 1 for antisemitic, 0 for not")
    original_text: str = Field(..., description="The original, raw text of the tweet")
    clean_text: str = Field(..., description="The processed and cleaned version of the text")
    sentiment: str = Field(..., description="Sentiment analysis result: 'positive', 'negative', or 'neutral'")
    weapons_detected: List[str] = Field(default_factory=list, description="List of weapons detected in the text")
    relevant_timestamp: str = Field(default="", description="The latest timestamp found within the text")

    model_config = ConfigDict(
        populate_by_name=True, # Allows creating model instance using field name OR alias
        json_schema_extra={
            "example": {
                "id": "64fcf0d2a1b23c0012345678",
                "createdate": "2020-03-24T09:28:15",
                "antisemietic": 0,
                "original_text": "Tomorrow (25/03/2020 09:30) we will attack using a gun (AK-47) near the border",
                "clean_text": "tomorrow attack use gun ak-47 near border",
                "sentiment": "negative",
                "weapons_detected": ["gun", "AK-47"],
                "relevant_timestamp": "25/03/2020"
            }
        }
    )

class TweetResponse(BaseModel):
    """ The final structure for the API response, containing a list of tweets. """
    count: int = Field(..., description="The number of tweets returned in the response")
    data: List[TweetModel] = Field(..., description="A list of tweet documents")