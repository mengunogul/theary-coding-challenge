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
    Tree API view with GET and POST methods for hierarchical data
    """

    @extend_schema(
        methods=["get"],
        responses={
            200: TreeNodeWithChildren,
            404: ErrorResponse,
            500: ErrorResponse,
        },
        description="Retrieve an array of all trees that exist",
    )
    async def get(self, request):
        """
        Handle GET requests - return tree structure starting from root nodes
        """
        logger.info("Fetching all tree structures")

        # Get all root nodes (nodes without parents)
        root_nodes = await sync_to_async(list)(
            TreeNode.objects.filter(parent__isnull=True).prefetch_related("children")
        )

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
        description="Create a new tree node",
    )
    async def post(self, request):
        """
        Handle POST requests to create new tree nodes with cycle detection
        """
        logger.info("Creating new tree node", request_data=request.data)

        try:
            # Validate request data with Pydantic
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
            with transaction.atomic():
                parent = None

                # Validate parent exists if provided
                if validated_data.parentId:
                    try:
                        parent = TreeNode.objects.get(id=validated_data.parentId)
                        logger.debug(
                            "Parent node found", parent_id=validated_data.parentId
                        )
                    except TreeNode.DoesNotExist:
                        raise ValueError("Parent node does not exist")

                # Create new node
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

        # Return validated response
        response_data = TreeNodeResponse(
            id=new_node.id,
            label=new_node.label,
            parentId=new_node.parent.id if new_node.parent else None,
        )

        return Response(response_data.model_dump(), status=status.HTTP_201_CREATED)
