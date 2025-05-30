"""
Tree Node Models

This module defines the database models for hierarchical tree structures.
Supports self-referential parent-child relationships for building tree data.

Models:
    TreeNode: Represents a node in a hierarchical tree structure
"""

from django.db.models import (
    Model,
    AutoField,
    CharField,
    ForeignKey,
    DateTimeField,
    CASCADE,
    QuerySet,
)


class TreeNode(Model):
    """
    Model representing a node in a hierarchical tree structure.

    This model supports building tree structures through self-referential
    foreign key relationships. Each node can have one parent and multiple children.

    Attributes:
        id (AutoField): Primary key, auto-incrementing integer
        label (CharField): Human-readable label for the node (max 255 chars)
        parent (ForeignKey): Optional reference to parent node (null for roots)
        created_at (DateTimeField): Timestamp when the node was created

    Relationships:
        children: Reverse foreign key to child nodes (related_name)

    Features:
        - Self-referential foreign key for parent-child relationships
        - Cascade deletion: deleting a parent removes all descendants
        - Automatic timestamp tracking for creation time
        - Built-in serialization method for API responses
    """

    id: AutoField = AutoField(primary_key=True)
    label: CharField = CharField(
        max_length=255, help_text="Human-readable label for the tree node"
    )
    parent: ForeignKey = ForeignKey(
        "self",
        on_delete=CASCADE,
        null=True,
        blank=True,
        related_name="children",
        help_text="Parent node reference (null for root nodes)",
    )
    created_at: DateTimeField = DateTimeField(
        auto_now_add=True, help_text="Timestamp when the node was created"
    )
    children: QuerySet["TreeNode"]

    def to_dict_with_children(self) -> dict:
        """
        Recursively serialize tree node to dictionary including all descendants.

        This method performs a depth-first traversal of the tree structure,
        building a nested dictionary representation suitable for JSON serialization.

        Returns:
            dict: Nested dictionary with structure:
                {
                    "id": int,
                    "label": str,
                    "children": [dict, ...]  # Recursively nested children
                }

        Note:
            This method triggers database queries for each level of children.
            For large trees, consider using select_related/prefetch_related
            in the original query for better performance.
        """
        return {
            "id": self.id,
            "label": self.label,
            "children": [
                child.to_dict_with_children() for child in self.children.all()
            ],
        }

    def __str__(self) -> str:
        """
        String representation of the tree node.

        Returns:
            str: Human-readable string showing ID and label
        """
        return f"TreeNode(id={self.id}, label='{self.label}')"

    class Meta:
        """
        Model metadata configuration.

        Attributes:
            ordering: Default ordering by ID for consistent query results
        """

        ordering = ["id"]
        verbose_name = "Tree Node"
        verbose_name_plural = "Tree Nodes"
        db_table = "tree_node"
