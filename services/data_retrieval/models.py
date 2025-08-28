from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TweetModel(BaseModel):
    """
    Pydantic model matching the exact structure saved by Persister
    """

    id: str = Field(..., alias="_id", description="Tweet ID from MongoDB")
    createdate: datetime = Field(
        ..., alias="CreateDate", description="Original creation date"
    )
    antisemietic: int = Field(
        ..., alias="Antisemitic", description="0 or 1 - antisemitic classification"
    )
    original_text: str = Field(..., alias="text", description="Original tweet text")
    clean_text: str = Field(..., description="Processed/cleaned text")
    sentiment: str = Field(..., description="positive/negative/neutral")
    weapons_detected: List[str] = Field(
        default=[], description="List of detected weapons"
    )
    relevant_timestamp: str = Field(default="", description="Extracted date from text")

    class Config:
        allow_population_by_field_name = True
        populate_by_name = True


class TweetResponse(BaseModel):
    count: int = Field(..., description="Number of tweets returned")
    data: List[TweetModel] = Field(..., description="List of tweets")

