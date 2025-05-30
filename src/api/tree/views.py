"""
Tree API Views

This module contains the API views for managing hierarchical tree structures.
Supports creating new tree nodes and retrieving complete tree hierarchies.

Classes:
    TreeAPIView: Async API view handling GET and POST operations for tree nodes
"""

# Create your views here.
from adrf.views import APIView
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from asgiref.sync import sync_to_async
from .models import TreeNode
from .serializers import (
    TreeNodeCreateRequest,
    TreeNodeResponse,
    TreeNodeWithChildren,
    ErrorResponse,
)
from pydantic import ValidationError
import structlog

logger = structlog.get_logger(__name__)


class TreeAPIView(APIView):
    """
    Async API view for hierarchical tree data management.

    This view provides endpoints for:
    - GET: Retrieve all tree structures starting from root nodes
    - POST: Create new tree nodes with optional parent relationships

    Features:
    - Async/await support for better performance
    - Input validation using Pydantic models
    - Structured logging for debugging and monitoring
    - Transaction safety for data consistency
    - Comprehensive error handling with detailed responses
    """

    @extend_schema(
        methods=["get"],
        responses={
            200: TreeNodeWithChildren,
            404: ErrorResponse,
            500: ErrorResponse,
        },
        description="Retrieve all tree structures as a forest of trees starting from root nodes",
        summary="Get all trees",
    )
    async def get(self, request):
        """
        Retrieve all tree structures from the database.

        Returns a list of tree structures, where each tree starts from a root node
        (node without a parent) and includes all descendants in a nested format.

        Args:
            request: HTTP request object

        Returns:
            Response: JSON array of tree structures with nested children

        Response Format:
            [
                {
                    "id": 1,
                    "label": "Root Node",
                    "children": [
                        {
                            "id": 2,
                            "label": "Child Node",
                            "children": []
                        }
                    ]
                }
            ]
        """
        logger.info("Fetching all tree structures")

        # Query optimization: Use prefetch_related to minimize database queries
        # when accessing children relationships
        root_nodes = await sync_to_async(list)(
            TreeNode.objects.filter(parent__isnull=True).prefetch_related("children")
        )

        # Convert Django model instances to dictionary format for JSON serialization
        tree_data = await sync_to_async(
            lambda: [node.to_dict_with_children() for node in root_nodes]
        )()

        logger.info(
            "Successfully retrieved tree data",
            tree_count=len(tree_data),
        )

        return Response(tree_data, status=status.HTTP_200_OK)

    @extend_schema(
        methods=["post"],
        request=TreeNodeCreateRequest,
        responses={
            201: TreeNodeResponse,
            400: ErrorResponse,
            404: ErrorResponse,
            500: ErrorResponse,
        },
        description="Create a new tree node with optional parent relationship",
        summary="Create tree node",
    )
    async def post(self, request):
        """
        Create a new tree node with optional parent relationship.

        Validates input data and creates a new tree node. If a parent ID is provided,
        validates that the parent exists before creating the relationship.

        Args:
            request: HTTP request object containing node data

        Request Body:
            {
                "label": "Node Label",      # Required: 1-255 characters
                "parentId": 123            # Optional: ID of parent node
            }

        Returns:
            Response: Created node data with HTTP 201 status

        Raises:
            ValidationError: If input data is invalid
            ValueError: If parent node doesn't exist

        Response Format:
            {
                "id": 123,
                "label": "Node Label",
                "parentId": 456  # or null for root nodes
            }
        """
        logger.info("Creating new tree node", request_data=request.data)

        try:
            # Validate request data using Pydantic model
            # This ensures type safety and business rule validation
            validated_data = TreeNodeCreateRequest.model_validate(request.data)
            logger.debug(
                "Request data validated successfully",
                label=validated_data.label,
                parent_id=validated_data.parentId,
            )
        except ValidationError as e:
            logger.warning("Validation failed", error=str(e), request_data=request.data)
            error_response = ErrorResponse(error="Validation failed", details=str(e))
            return Response(
                error_response.model_dump(), status=status.HTTP_400_BAD_REQUEST
            )

        @sync_to_async
        def create_tree_node():
            """
            Database operation wrapper for creating tree nodes.

            Uses atomic transactions to ensure data consistency.
            Validates parent existence before creating relationships.

            Returns:
                TreeNode: The newly created tree node instance

            Raises:
                ValueError: If parent node doesn't exist
            """
            with transaction.atomic():
                parent = None

                # Validate parent node existence if parent ID provided
                if validated_data.parentId:
                    try:
                        parent = TreeNode.objects.get(id=validated_data.parentId)
                        logger.debug(
                            "Parent node found", parent_id=validated_data.parentId
                        )
                    except TreeNode.DoesNotExist:
                        raise ValueError("Parent node does not exist")

                # Create and save new tree node
                new_node = TreeNode(label=validated_data.label, parent=parent)
                new_node.save()

                logger.info(
                    "Tree node created successfully",
                    node_id=new_node.id,
                    label=new_node.label,
                    parent_id=new_node.parent.id if new_node.parent else None,
                )

                return new_node

        try:
            new_node = await create_tree_node()
        except ValueError as e:
            logger.warning("Node creation failed", error=str(e))
            error_response = ErrorResponse(error=str(e))
            return Response(
                error_response.model_dump(), status=status.HTTP_400_BAD_REQUEST
            )

        # Serialize response using Pydantic model for consistency
        response_data = TreeNodeResponse(
            id=new_node.id,
            label=new_node.label,
            parentId=new_node.parent.id if new_node.parent else None,
        )

        return Response(response_data.model_dump(), status=status.HTTP_201_CREATED)
