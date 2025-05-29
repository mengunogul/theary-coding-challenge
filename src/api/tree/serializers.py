from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


class TreeNodeCreateRequest(BaseModel):
    label: str = Field(
        ..., min_length=1, max_length=255, description="Label for the tree node"
    )
    parentId: Optional[int] = Field(None, description="ID of the parent node")

    @field_validator("label")
    def validate_label(cls, v):
        if not v or not v.strip():
            raise ValueError("Label cannot be empty or whitespace only")
        return v.strip()

    @field_validator("parentId")
    def validate_parent_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Parent ID must be a positive integer")
        return v


class TreeNodeResponse(BaseModel):
    id: int = Field(..., description="Unique identifier of the tree node")
    label: str = Field(..., description="Label of the tree node")

    class Config:
        from_attributes = True


class TreeNodeWithChildren(BaseModel):
    id: int = Field(..., description="Unique identifier of the tree node")
    label: str = Field(..., description="Label of the tree node")
    children: List["TreeNodeWithChildren"] = Field(
        default=[], description="List of child nodes"
    )

    class Config:
        from_attributes = True


# Update forward reference
TreeNodeWithChildren.model_rebuild()


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message describing what went wrong")
    details: Optional[str] = Field(
        None, description="Additional error details or context"
    )
