import pytest
from django.test import TestCase  # Changed from TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from api.tree.models import TreeNode
import json


@pytest.mark.django_db(transaction=True)
class TestTreeAPIFunctional(TestCase):
    """Functional tests for Tree API endpoints"""

    def setUp(self):
        """Set up test client and common test data"""
        self.client = APIClient()
        self.tree_url = reverse("tree-api")

        # Clear any existing data
        TreeNode.objects.all().delete()

    def test_get_empty_tree(self):
        """Test GET request when no trees exist"""
        response = self.client.get(self.tree_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_single_root_node(self):
        """Test GET request with single root node"""
        root = TreeNode.objects.create(label="Root Node")

        response = self.client.get(self.tree_url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == root.id
        assert data[0]["label"] == "Root Node"
        assert data[0]["children"] == []

    def test_get_multiple_root_nodes(self):
        """Test GET request with multiple root nodes"""
        TreeNode.objects.create(label="Root 1")
        TreeNode.objects.create(label="Root 2")

        response = self.client.get(self.tree_url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

        # Sort by ID to ensure consistent order
        data.sort(key=lambda x: x["id"])
        assert data[0]["label"] == "Root 1"
        assert data[1]["label"] == "Root 2"

    def test_get_tree_with_children(self):
        """Test GET request with nested tree structure"""
        root = TreeNode.objects.create(label="Root")
        child1 = TreeNode.objects.create(label="Child 1", parent=root)
        TreeNode.objects.create(label="Child 2", parent=root)
        TreeNode.objects.create(label="Grandchild", parent=child1)

        response = self.client.get(self.tree_url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1

        root_data = data[0]
        assert root_data["label"] == "Root"
        assert len(root_data["children"]) == 2

        # Find child1 and child2
        children = {child["label"]: child for child in root_data["children"]}
        assert "Child 1" in children
        assert "Child 2" in children

        # Check grandchild
        child1_data = children["Child 1"]
        assert len(child1_data["children"]) == 1
        assert child1_data["children"][0]["label"] == "Grandchild"
        assert child1_data["children"][0]["children"] == []

        # Child 2 should have no children
        assert children["Child 2"]["children"] == []

    def test_get_complex_tree_structure(self):
        """Test GET request with complex multi-level tree"""
        # Create a complex tree structure
        root1 = TreeNode.objects.create(label="Root 1")
        root2 = TreeNode.objects.create(label="Root 2")

        # Root 1 children
        child1_1 = TreeNode.objects.create(label="Child 1.1", parent=root1)
        child1_2 = TreeNode.objects.create(label="Child 1.2", parent=root1)

        # Root 2 children
        TreeNode.objects.create(label="Child 2.1", parent=root2)

        # Grandchildren
        TreeNode.objects.create(label="Grandchild 1.1.1", parent=child1_1)
        TreeNode.objects.create(label="Grandchild 1.2.1", parent=child1_2)
        TreeNode.objects.create(label="Grandchild 1.2.2", parent=child1_2)

        response = self.client.get(self.tree_url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

        # Verify structure complexity
        total_nodes = sum(self._count_nodes_recursive(tree) for tree in data)
        assert total_nodes == 8  # 2 roots + 3 children + 3 grandchildren

    def test_post_create_root_node(self):
        """Test POST request to create root node"""
        data = {"label": "New Root"}

        response = self.client.post(
            self.tree_url, data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data["label"] == "New Root"
        assert "id" in response_data

        # Verify in database
        node = TreeNode.objects.get(id=response_data["id"])
        assert node.label == "New Root"
        assert node.parent is None

    def test_post_create_child_node(self):
        """Test POST request to create child node"""
        parent = TreeNode.objects.create(label="Parent")

        data = {"label": "Child Node", "parentId": parent.id}

        response = self.client.post(
            self.tree_url, data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert "id" in response_data
        assert response_data["label"] == "Child Node"

        # Verify in database
        child = TreeNode.objects.get(id=response_data["id"])
        assert child.parent == parent

    def test_post_label_trimming(self):
        """Test that labels are properly trimmed during creation"""
        data = {"label": "  Trimmed Label  "}

        response = self.client.post(
            self.tree_url, data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data["label"] == "Trimmed Label"

    def test_post_special_characters_in_label(self):
        """Test creating node with special characters in label"""
        data = {"label": "Node with émojis 🌳 and symbols @#$%"}

        response = self.client.post(
            self.tree_url, data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data["label"] == "Node with émojis 🌳 and symbols @#$%"

    def test_post_missing_label_error(self):
        """Test POST request with missing label"""
        data = {"parentId": 1}

        response = self.client.post(
            self.tree_url, data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert "error" in response_data
        assert "Validation failed" in response_data["error"]

    def test_post_empty_label_error(self):
        """Test POST request with empty label"""
        data = {"label": ""}

        response = self.client.post(
            self.tree_url, data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert "error" in response_data

    def test_post_whitespace_only_label_error(self):
        """Test POST request with whitespace-only label"""
        data = {"label": "   "}

        response = self.client.post(
            self.tree_url, data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert "error" in response_data

    def test_post_label_too_long_error(self):
        """Test POST request with label exceeding max length"""
        data = {"label": "a" * 256}

        response = self.client.post(
            self.tree_url, data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert "error" in response_data

    def test_post_max_length_label_success(self):
        """Test POST request with label at maximum allowed length"""
        data = {"label": "a" * 255}

        response = self.client.post(
            self.tree_url, data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert len(response_data["label"]) == 255

    def test_post_invalid_parent_id_error(self):
        """Test POST request with non-existent parent ID"""
        data = {"label": "Child", "parentId": 99999}

        response = self.client.post(
            self.tree_url, data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert "error" in response_data
        assert "Parent node does not exist" in response_data["error"]

    def test_post_negative_parent_id_error(self):
        """Test POST request with negative parent ID"""
        data = {"label": "Child", "parentId": -1}

        response = self.client.post(
            self.tree_url, data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert "error" in response_data

    def test_post_zero_parent_id_error(self):
        """Test POST request with zero parent ID"""
        data = {"label": "Child", "parentId": 0}

        response = self.client.post(
            self.tree_url, data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert "error" in response_data

    def test_post_invalid_json_error(self):
        """Test POST request with invalid JSON"""
        response = self.client.post(
            self.tree_url, data="invalid json", content_type="application/json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_invalid_content_type(self):
        """Test POST request with invalid content type"""
        data = {"label": "Test"}

        response = self.client.post(
            self.tree_url,
            data=data,  # Form data instead of JSON
        )

        # Should still work with form data
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
        ]

    def test_integration_create_and_retrieve_tree(self):
        """Test integration of POST and GET operations"""
        # Create root
        root_data = {"label": "Integration Root"}
        root_response = self.client.post(
            self.tree_url, data=json.dumps(root_data), content_type="application/json"
        )
        assert root_response.status_code == status.HTTP_201_CREATED
        root_id = root_response.json()["id"]

        # Create children
        child1_data = {"label": "Child 1", "parentId": root_id}
        child1_response = self.client.post(
            self.tree_url, data=json.dumps(child1_data), content_type="application/json"
        )
        assert child1_response.status_code == status.HTTP_201_CREATED
        child1_id = child1_response.json()["id"]

        child2_data = {"label": "Child 2", "parentId": root_id}
        child2_response = self.client.post(
            self.tree_url, data=json.dumps(child2_data), content_type="application/json"
        )
        assert child2_response.status_code == status.HTTP_201_CREATED

        # Create grandchild
        grandchild_data = {"label": "Grandchild", "parentId": child1_id}
        grandchild_response = self.client.post(
            self.tree_url,
            data=json.dumps(grandchild_data),
            content_type="application/json",
        )
        assert grandchild_response.status_code == status.HTTP_201_CREATED

        # Retrieve tree and verify structure
        get_response = self.client.get(self.tree_url)
        assert get_response.status_code == status.HTTP_200_OK

        trees = get_response.json()
        assert len(trees) == 1

        root_tree = trees[0]
        assert root_tree["label"] == "Integration Root"
        assert len(root_tree["children"]) == 2

        # Verify children
        children_labels = {child["label"] for child in root_tree["children"]}
        assert children_labels == {"Child 1", "Child 2"}

        # Find child1 and verify grandchild
        child1_tree = next(
            child for child in root_tree["children"] if child["label"] == "Child 1"
        )
        assert len(child1_tree["children"]) == 1
        assert child1_tree["children"][0]["label"] == "Grandchild"

    def test_concurrent_node_creation(self):
        """Test creating multiple nodes in sequence"""
        parent = TreeNode.objects.create(label="Concurrent Parent")

        # Create multiple children rapidly
        child_labels = [f"Child {i}" for i in range(5)]
        created_ids = []

        for label in child_labels:
            data = {"label": label, "parentId": parent.id}
            response = self.client.post(
                self.tree_url, data=json.dumps(data), content_type="application/json"
            )
            assert response.status_code == status.HTTP_201_CREATED
            created_ids.append(response.json()["id"])

        # Verify all children were created
        assert len(set(created_ids)) == 5  # All IDs should be unique

        # Verify in database
        children = TreeNode.objects.filter(parent=parent)
        assert children.count() == 5

        child_labels_db = set(children.values_list("label", flat=True))
        assert child_labels_db == set(child_labels)

    def test_deep_tree_structure(self):
        """Test creating and retrieving deep tree structure"""
        # Create a deep tree (10 levels)
        current_parent = None
        node_ids = []

        for i in range(10):
            data = {"label": f"Level {i}"}
            if current_parent:
                data["parentId"] = current_parent

            response = self.client.post(
                self.tree_url, data=json.dumps(data), content_type="application/json"
            )
            assert response.status_code == status.HTTP_201_CREATED

            current_parent = response.json()["id"]
            node_ids.append(current_parent)

        # Retrieve and verify structure
        get_response = self.client.get(self.tree_url)
        assert get_response.status_code == status.HTTP_200_OK

        trees = get_response.json()
        assert len(trees) == 1

        # Traverse down the tree
        current_node = trees[0]
        for i in range(10):
            assert current_node["label"] == f"Level {i}"
            if i < 9:  # Not the last level
                assert len(current_node["children"]) == 1
                current_node = current_node["children"][0]
            else:  # Last level
                assert len(current_node["children"]) == 0

    def test_large_tree_performance(self):
        """Test handling of tree with many siblings"""
        root = TreeNode.objects.create(label="Large Tree Root")

        # Create 50 children
        for i in range(50):
            data = {"label": f"Child {i:02d}", "parentId": root.id}
            response = self.client.post(
                self.tree_url, data=json.dumps(data), content_type="application/json"
            )
            assert response.status_code == status.HTTP_201_CREATED

        # Retrieve tree
        get_response = self.client.get(self.tree_url)
        assert get_response.status_code == status.HTTP_200_OK

        trees = get_response.json()
        assert len(trees) == 1
        assert len(trees[0]["children"]) == 50

        # Verify all children are present
        child_labels = {child["label"] for child in trees[0]["children"]}
        expected_labels = {f"Child {i:02d}" for i in range(50)}
        assert child_labels == expected_labels

    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters"""
        test_labels = [
            "Chinese: 中文节点",
            "Japanese: 日本語ノード",
            "Arabic: العقدة العربية",
            "Emoji: 🌳🍃🌿",
            "Mixed: Nœud spécial ñ 🚀",
            "Symbols: @#$%^&*()[]{}|\\:;\"'<>?,./",
        ]

        created_nodes = []
        for label in test_labels:
            data = {"label": label}
            response = self.client.post(
                self.tree_url, data=json.dumps(data), content_type="application/json"
            )
            assert response.status_code == status.HTTP_201_CREATED
            created_nodes.append(response.json())

        # Retrieve and verify
        get_response = self.client.get(self.tree_url)
        assert get_response.status_code == status.HTTP_200_OK

        trees = get_response.json()
        retrieved_labels = {tree["label"] for tree in trees}
        assert retrieved_labels == set(test_labels)

    def test_unsupported_http_methods(self):
        """Test that unsupported HTTP methods return appropriate errors"""
        # Test PUT
        put_response = self.client.put(self.tree_url, {})
        assert put_response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # Test DELETE
        delete_response = self.client.delete(self.tree_url)
        assert delete_response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # Test PATCH
        patch_response = self.client.patch(self.tree_url, {})
        assert patch_response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def _count_nodes_recursive(self, node):
        """Helper method to count nodes in a tree structure recursively"""
        count = 1  # Count the current node
        for child in node.get("children", []):
            count += self._count_nodes_recursive(child)
        return count
