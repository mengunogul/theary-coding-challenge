import pytest
from pydantic import ValidationError
from api.tree.serializers import (
    TreeNodeCreateRequest,
    TreeNodeResponse,
    TreeNodeWithChildren,
    ErrorResponse,
)


class TestTreeNodeCreateRequest:
    """Test cases for TreeNodeCreateRequest serializer"""

    def test_valid_data_with_parent(self):
        """Test valid data with parent ID"""
        data = {"label": "Test Node", "parentId": 1}
        request = TreeNodeCreateRequest(**data)
        assert request.label == "Test Node"
        assert request.parentId == 1

    def test_valid_data_without_parent(self):
        """Test valid data without parent ID (root node)"""
        data = {"label": "Root Node"}
        request = TreeNodeCreateRequest(**data)
        assert request.label == "Root Node"
        assert request.parentId is None

    @pytest.mark.parametrize(
        "input_label,expected_label",
        [
            ("  Trimmed Label  ", "Trimmed Label"),
            ("\t\nTabbed Label\n\t", "Tabbed Label"),
            ("   Single Space   ", "Single Space"),
            ("NoSpaces", "NoSpaces"),
        ],
    )
    def test_label_trimming(self, input_label, expected_label):
        """Test that labels are properly trimmed of various whitespace"""
        request = TreeNodeCreateRequest(label=input_label)
        assert request.label == expected_label

    def test_missing_label_raises_error(self):
        """Test that missing label raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TreeNodeCreateRequest()
        error_details = exc_info.value.errors()[0]
        assert error_details["type"] == "missing"
        assert "label" in error_details["loc"]

    def test_empty_label_raises_error(self):
        """Test that empty label raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TreeNodeCreateRequest(label="")
        assert "String should have at least 1 character" in str(exc_info.value)

    @pytest.mark.parametrize(
        "whitespace_label",
        [
            "   ",
            "\t\t",
            "\n\n",
            " \t\n ",
        ],
    )
    def test_whitespace_only_label_raises_error(self, whitespace_label):
        """Test that whitespace-only labels raise validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TreeNodeCreateRequest(label=whitespace_label)
        assert "Label cannot be empty or whitespace only" in str(exc_info.value)

    def test_max_length_label_valid(self):
        """Test that label at max length (255 chars) is valid"""
        max_label = "a" * 255
        request = TreeNodeCreateRequest(label=max_label)
        assert len(request.label) == 255

    def test_long_label_raises_error(self):
        """Test that label exceeding max length raises validation error"""
        long_label = "a" * 256
        with pytest.raises(ValidationError) as exc_info:
            TreeNodeCreateRequest(label=long_label)
        assert "String should have at most 255 characters" in str(exc_info.value)

    @pytest.mark.parametrize("invalid_parent_id", [0, -1, -100])
    def test_invalid_parent_id_raises_error(self, invalid_parent_id):
        """Test that invalid parent IDs raise validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TreeNodeCreateRequest(label="Test", parentId=invalid_parent_id)
        assert "Parent ID must be a positive integer" in str(exc_info.value)

    @pytest.mark.parametrize("valid_parent_id", [1, 100, 999999])
    def test_valid_parent_ids(self, valid_parent_id):
        """Test that valid parent IDs are accepted"""
        request = TreeNodeCreateRequest(label="Test", parentId=valid_parent_id)
        assert request.parentId == valid_parent_id

    def test_invalid_parent_id_type_raises_error(self):
        """Test that non-integer parent ID raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TreeNodeCreateRequest(label="Test", parentId="not_an_int")
        error_details = exc_info.value.errors()[0]
        assert error_details["type"] == "int_parsing"

    def test_special_characters_in_label(self):
        """Test that special characters in labels are preserved"""
        special_label = "Node with émojis 🌳 and symbols @#$%"
        request = TreeNodeCreateRequest(label=special_label)
        assert request.label == special_label


class TestTreeNodeResponse:
    """Test cases for TreeNodeResponse serializer"""

    def test_valid_response_data(self):
        """Test valid response data creation"""
        data = {"id": 1, "label": "Test Node"}
        response = TreeNodeResponse(**data)
        assert response.id == 1
        assert response.label == "Test Node"

    def test_from_attributes_config(self):
        """Test that from_attributes is properly configured"""
        assert TreeNodeResponse.model_config["from_attributes"] is True

    def test_model_dump_includes_all_fields(self):
        """Test that model dump includes all expected fields"""
        response = TreeNodeResponse(id=1, label="Test")
        dumped = response.model_dump()
        assert dumped == {"id": 1, "label": "Test"}

    def test_response_from_mock_model_instance(self):
        """Test creating response from mock model instance"""

        class MockTreeNode:
            def __init__(self):
                self.id = 42
                self.label = "Mock Node"

        mock_node = MockTreeNode()
        response = TreeNodeResponse.model_validate(mock_node)
        assert response.id == 42
        assert response.label == "Mock Node"

    def test_missing_required_fields_raises_error(self):
        """Test that missing required fields raise validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TreeNodeResponse(id=1)  # Missing label
        error_details = exc_info.value.errors()[0]
        assert error_details["type"] == "missing"
        assert "label" in error_details["loc"]

    @pytest.mark.parametrize("invalid_id", ["string", None, 1.5])
    def test_invalid_id_types_raise_error(self, invalid_id):
        """Test that invalid ID types raise validation errors"""
        with pytest.raises(ValidationError):
            TreeNodeResponse(id=invalid_id, label="Test")

    @pytest.mark.parametrize("invalid_id", [-1, 0])
    def test_negative_and_zero_id_raise_error(self, invalid_id):
        """Test that negative and zero IDs raise validation errors"""
        with pytest.raises(ValidationError) as exc_info:
            TreeNodeResponse(id=invalid_id, label="Test")
        assert "ID must be a positive integer" in str(exc_info.value)

    def test_positive_id_valid(self):
        """Test that positive IDs are valid"""
        response = TreeNodeResponse(id=1, label="Test")
        assert response.id == 1


class TestTreeNodeWithChildren:
    """Test cases for TreeNodeWithChildren serializer"""

    def test_node_without_children(self):
        """Test node with empty children list"""
        data = {"id": 1, "label": "Leaf Node"}
        node = TreeNodeWithChildren(**data)
        assert node.id == 1
        assert node.label == "Leaf Node"
        assert node.children == []
        assert isinstance(node.children, list)

    def test_node_with_children(self):
        """Test node with nested children"""
        data = {
            "id": 1,
            "label": "Parent",
            "children": [
                {"id": 2, "label": "Child 1", "children": []},
                {"id": 3, "label": "Child 2", "children": []},
            ],
        }
        node = TreeNodeWithChildren(**data)
        assert node.id == 1
        assert len(node.children) == 2
        assert node.children[0].label == "Child 1"
        assert node.children[1].label == "Child 2"
        assert all(isinstance(child, TreeNodeWithChildren) for child in node.children)

    def test_deeply_nested_children(self):
        """Test deeply nested children structure"""
        data = {
            "id": 1,
            "label": "Root",
            "children": [
                {
                    "id": 2,
                    "label": "Level 1",
                    "children": [
                        {
                            "id": 3,
                            "label": "Level 2",
                            "children": [{"id": 4, "label": "Level 3", "children": []}],
                        }
                    ],
                }
            ],
        }
        node = TreeNodeWithChildren(**data)
        assert node.children[0].children[0].label == "Level 2"
        assert node.children[0].children[0].children[0].label == "Level 3"
        assert len(node.children[0].children[0].children[0].children) == 0

    def test_model_rebuild_forward_reference(self):
        """Test that forward reference resolution works correctly"""
        # This tests that TreeNodeWithChildren.model_rebuild() was called
        data = {"id": 1, "label": "Parent", "children": [{"id": 2, "label": "Child"}]}
        node = TreeNodeWithChildren(**data)
        assert isinstance(node.children[0], TreeNodeWithChildren)

    def test_empty_children_list_explicit(self):
        """Test explicitly setting children to empty list"""
        data = {"id": 1, "label": "Node", "children": []}
        node = TreeNodeWithChildren(**data)
        assert node.children == []

    def test_large_children_list(self):
        """Test node with many children"""
        children_data = [
            {"id": i, "label": f"Child {i}", "children": []}
            for i in range(2, 102)  # 100 children
        ]
        data = {"id": 1, "label": "Parent", "children": children_data}
        node = TreeNodeWithChildren(**data)
        assert len(node.children) == 100
        assert node.children[0].label == "Child 2"
        assert node.children[-1].label == "Child 101"

    def test_model_dump_nested_structure(self):
        """Test that model dump properly serializes nested structure"""
        data = {"id": 1, "label": "Parent", "children": [{"id": 2, "label": "Child"}]}
        node = TreeNodeWithChildren(**data)
        dumped = node.model_dump()
        expected = {
            "id": 1,
            "label": "Parent",
            "children": [{"id": 2, "label": "Child", "children": []}],
        }
        assert dumped == expected

    def test_invalid_children_structure_raises_error(self):
        """Test that invalid children structure raises validation error"""
        with pytest.raises(ValidationError):
            TreeNodeWithChildren(
                id=1, label="Parent", children=[{"invalid": "structure"}]
            )

    @pytest.mark.parametrize("invalid_id", [-1, 0])
    def test_negative_and_zero_id_raise_error(self, invalid_id):
        """Test that negative and zero IDs raise validation errors"""
        with pytest.raises(ValidationError) as exc_info:
            TreeNodeWithChildren(id=invalid_id, label="Test")
        assert "ID must be a positive integer" in str(exc_info.value)

    def test_invalid_child_id_raises_error(self):
        """Test that invalid child ID raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TreeNodeWithChildren(
                id=1, label="Parent", children=[{"id": -1, "label": "Invalid Child"}]
            )
        assert "ID must be a positive integer" in str(exc_info.value)


class TestErrorResponse:
    """Test cases for ErrorResponse serializer"""

    def test_error_without_details(self):
        """Test error response without details"""
        error = ErrorResponse(error="Something went wrong")
        assert error.error == "Something went wrong"
        assert error.details is None

    def test_error_with_details(self):
        """Test error response with details"""
        error = ErrorResponse(
            error="Validation failed", details="Label cannot be empty"
        )
        assert error.error == "Validation failed"
        assert error.details == "Label cannot be empty"

    def test_error_with_empty_details(self):
        """Test error response with empty details string"""
        error = ErrorResponse(error="Error", details="")
        assert error.details == ""

    def test_model_dump_with_none_details(self):
        """Test that model dump handles None details correctly"""
        error = ErrorResponse(error="Test error")
        dumped = error.model_dump()
        assert dumped == {"error": "Test error", "details": None}

    def test_model_dump_exclude_none(self):
        """Test model dump with exclude_none option"""
        error = ErrorResponse(error="Test error")
        dumped = error.model_dump(exclude_none=True)
        assert dumped == {"error": "Test error"}

    def test_missing_error_field_raises_error(self):
        """Test that missing error field raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            ErrorResponse(details="Some details")
        error_details = exc_info.value.errors()[0]
        assert error_details["type"] == "missing"
        assert "error" in error_details["loc"]

    @pytest.mark.parametrize(
        "error_message",
        [
            "Short error",
            "A" * 1000,  # Very long error message
            "Error with special chars: éñ中文🚨",
            "Error\nwith\nnewlines",
        ],
    )
    def test_various_error_message_formats(self, error_message):
        """Test that various error message formats are accepted"""
        error = ErrorResponse(error=error_message)
        assert error.error == error_message

    def test_json_serialization(self):
        """Test that ErrorResponse can be JSON serialized"""
        error = ErrorResponse(error="Test", details="Details")
        json_str = error.model_dump_json()
        assert '"error":"Test"' in json_str
        assert '"details":"Details"' in json_str
