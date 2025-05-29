from django.db.models import (
    Model,
    AutoField,
    CharField,
    ForeignKey,
    DateTimeField,
    CASCADE,
)


# Create your models here.
class TreeNode(Model):
    id: AutoField = AutoField(primary_key=True)
    label: CharField = CharField(max_length=255)
    parent: ForeignKey = ForeignKey(
        "self", on_delete=CASCADE, null=True, blank=True, related_name="children"
    )
    created_at: DateTimeField = DateTimeField(auto_now_add=True)

    def to_dict_with_children(self):
        """
        Recursively convert tree node to dictionary including all children
        """
        return {
            "id": self.id,
            "label": self.label,
            "children": [
                child.to_dict_with_children() for child in self.children.all()
            ],
        }

    def __str__(self):
        return f"TreeNode(id={self.id}, label='{self.label}')"

    class Meta:
        ordering = ["id"]
