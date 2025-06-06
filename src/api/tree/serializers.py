"""
Pydantic Serializers for Tree API

This module defines Pydantic models used for request/response serialization
and validation in the Tree API. Provides type safety and automatic validation.

Classes:
    TreeNodeCreateRequest: Validates incoming tree node creation requests
    TreeNodeResponse: Serializes tree node data for API responses
    TreeNodeWithChildren: Serializes complete tree structures with nested children
    ErrorResponse: Standardized error response format
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List


class TreeNodeCreateRequest(BaseModel):
    """
    Request model for creating new tree nodes.

    Validates incoming data for tree node creation, ensuring proper
    label formatting and parent ID validation.

    Attributes:
        label: Node label (1-255 characters, automatically trimmed)
        parentId: Optional parent node ID (must be positive integer)

    Validation Rules:
        - Label cannot be empty or whitespace-only
        - Label is automatically trimmed of leading/trailing whitespace
        - Parent ID must be positive integer if provided
    """

    label: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable label for the tree node (1-255 characters)",
    )
    parentId: Optional[int] = Field(
        None,
        description="ID of the parent node (null for root nodes, must be positive)",
    )

    @field_validator("label")
    @classmethod
    def validate_label(cls, v: str) -> str:
        """
        Validate and normalize label field.

        Args:
            v: Raw label value from request

        Returns:
            str: Trimmed label string

        Raises:
            ValueError: If label is empty or whitespace-only after trimming
        """
        if not v or not v.strip():
            raise ValueError("Label cannot be empty or whitespace only")
        return v.strip()

    @field_validator("parentId")
    @classmethod
    def validate_parent_id(cls, v: Optional[int]) -> Optional[int]:
        """
        Validate parent ID field.

        Args:
            v: Parent ID value from request

        Returns:
            Optional[int]: Validated parent ID or None

        Raises:
            ValueError: If parent ID is not a positive integer
        """
        if v is not None and v <= 0:
            raise ValueError("Parent ID must be a positive integer")
        return v


class TreeNodeResponse(BaseModel):
    """
    Response model for individual tree nodes.

    Used for API responses when returning single tree node data,
    typically after creation or update operations.

    Attributes:
        id: Unique node identifier
        label: Node label/name

    Configuration:
        from_attributes: Enables creation from Django model instances
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique identifier of the tree node")
    label: str = Field(..., description="Human-readable label of the tree node")
    parentId: Optional[int] = Field(None, description="ID of the parent node")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: int) -> int:
        """
        Validate node ID field.

        Args:
            v: Node ID value

        Returns:
            int: Validated node ID

        Raises:
            ValueError: If ID is not positive
        """
        if v <= 0:
            raise ValueError("ID must be a positive integer")
        return v


class TreeNodeWithChildren(BaseModel):
    """
    Response model for tree structures with nested children.

    Used for API responses that include complete tree hierarchies,
    supporting recursive nesting of child nodes.

    Attributes:
        id: Unique node identifier
        label: Node label/name
        children: List of child nodes (recursively nested)

    Configuration:
        from_attributes: Enables creation from Django model instances

    Note:
        This model uses forward references for recursive typing.
        model_rebuild() is called after class definition to resolve references.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique identifier of the tree node")
    label: str = Field(..., description="Human-readable label of the tree node")
    children: List["TreeNodeWithChildren"] = Field(
        default=[], description="List of child nodes (empty list for leaf nodes)"
    )

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: int) -> int:
        """
        Validate node ID field.

        Args:
            v: Node ID value

        Returns:
            int: Validated node ID

        Raises:
            ValueError: If ID is not positive
        """
        if v <= 0:
            raise ValueError("ID must be a positive integer")
        return v


# Resolve forward reference for recursive children typing
TreeNodeWithChildren.model_rebuild()


class TreeNodeCloneRequest(BaseModel):
    parent_id: int = Field(..., description="Unique identifier of parent node")
    target_id: int = Field(
        ..., description="Unique identifier of targeted node to clone"
    )


class ErrorResponse(BaseModel):
    """
    Standardized error response model.

    Provides consistent error formatting across the API,
    with optional additional details for debugging.

    Attributes:
        error: Main error message describing what went wrong
        details: Optional additional context or validation details

    Usage:
        Used for all API error responses (4xx and 5xx status codes)
        to ensure consistent error format for client applications.
    """

    error: str = Field(
        ..., description="Primary error message describing what went wrong"
    )
    details: Optional[str] = Field(
        None, description="Additional error details, context, or validation messages"
    )
