"""
Tree Node Models

This module defines the database models for hierarchical tree structures.
Supports self-referential parent-child relationships for building tree data.

Models:
    TreeNode: Represents a node in a hierarchical tree structure
"""

from collections import deque
from typing import Self

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

    def clone_subtree(self, parent: Self) -> "TreeNode":
        """
        Clone this node and all its descendants using iterative breadth-first traversal.

        This method uses a bfs approach to clone the entire subtree,
        which prevents infinite recursion and stack overflow issues while also
        detecting circular references in the tree structure.

        Args:
            parent (TreeNode): Parent node to attach the cloned subtree to

        Returns:
            TreeNode: The newly created root node of the cloned subtree

        Raises:
            ValueError: If circular reference is detected in the tree structure
        """
        # Create the cloned root node
        cloned_root = TreeNode.objects.create(label=self.label, parent=parent)

        # Queue stores tuples of (original_node, cloned_parent)
        queue: deque[tuple[TreeNode, TreeNode]] = deque([(self, cloned_root)])
        visited = {self.id, cloned_root.id}  # Track visited nodes to detect cycles

        while queue:
            original_node, cloned_parent = queue.popleft()

            # Process all children of the current original node
            for child in original_node.children.all():
                # Detect circular reference
                if child.id in visited:
                    # it skips the circulare references
                    continue

                # Clone the child
                cloned_child = TreeNode.objects.create(
                    label=child.label, parent=cloned_parent
                )

                # Add child to queue for further processing and mark as visited
                queue.append((child, cloned_child))
                visited.add(child.id)
                visited.add(cloned_child.id)

        return cloned_root

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
