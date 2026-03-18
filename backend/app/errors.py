"""shared error response models."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """standard error response from HTTPException."""
    detail: str
