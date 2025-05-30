import os
from theary.settings import *  # noqa

# Use in-memory SQLite database for development testing to avoid external DB dependencies
if os.environ.get("ENVIRONMENT", "dev") == "dev":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
