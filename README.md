# Theary Coding Challenge

A Django-based REST API for managing hierarchical tree structures with async support.

## Overview

This project implements a Tree API that allows you to:

- Create tree nodes with optional parent-child relationships
- Retrieve complete tree structures as nested JSON
- Handle multiple tree roots (forest structure)
- Validate input data with comprehensive error handling

## Features

- **Async API Views**: Built with ADRF (Async Django REST Framework) for better performance
- **Hierarchical Data**: Self-referential foreign key relationships for tree structures
- **Input Validation**: Pydantic models for type safety and business rule validation
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Structured Logging**: JSON-formatted logs with contextual information
- **PostgreSQL Support**: Production-ready database configuration
- **Comprehensive Testing**: Unit and functional tests with pytest
- **Code Quality**: Pre-commit hooks for consistent code formatting and linting
- **CI Pipeline**: Automated testing and quality checks on every commit

## API Endpoints

### GET /api/tree/

Retrieve all tree structures starting from root nodes.

**Response Format:**

```json
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
```

### POST /api/tree/

Create a new tree node with optional parent relationship.

**Request Body:**

```json
{
  "label": "New Node",
  "parentId": 1  // Optional: omit for root nodes
}
```

**Response:**

```json
{
  "id": 3,
  "label": "New Node",
  "parentId": 1
}
```

## Development Setup

### Prerequisites

- Python 3.13+
- uv (Python package manager)
- Docker & Docker Compose (for PostgreSQL)

### Environment Configuration

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=theary_db
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
```

### Local Development with SQLite

For quick development and testing, you can use in memory SQLite instead of depending on external PostgreSQL service:

```bash
# Set environment to use SQLite
export ENVIRONMENT=dev

# Install dependencies
uv sync

# Run migrations
uv run python src/manage.py migrate

# Start development server
uv run python src/manage.py runserver
```

### PostgreSQL Setup

For production-like testing with PostgreSQL:

```bash
# Start PostgreSQL container
docker compose up -d db

# Set environment for PostgreSQL
export ENVIRONMENT=test

# Run migrations
uv run python src/manage.py migrate

# Start development server
uv run python src/manage.py runserver
```

## Testing

### Quick Testing with SQLite

```bash
export ENVIRONMENT=dev
uv run pytest
```

### Full Testing with PostgreSQL

```bash
# Start PostgreSQL
docker compose -d db

# Run tests
export ENVIRONMENT=test
uv run pytest
```

## Code Quality

### Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality and consistency:

```bash
# Install pre-commit
pre-commit install

# Run pre-commit on all files
pre-commit run --all-files
```

The pre-commit configuration includes:

- **Ruff**: Code linting and formatting (replaces Black + isort + Flake8)
- **MyPy**: Static type checking
- **Bandit**: Security vulnerability scanning
- **Detect-secrets**: Secrets detection and prevention
- **Conventional Commits**: Commit message formatting
- **General Hooks**: YAML/JSON validation, trailing whitespace, large file detection

### CI Pipeline

The project includes a comprehensive CI pipeline (`.github/workflows/theary.yml`) that runs on every push and pull request:

**Pipeline Stages:**

1. **Security Checks**:
   - Bandit security scanning
   - Debug statement detection
   - Hardcoded secrets detection
   - SQL injection pattern checking

2. **Code Quality (Lint)**:
   - Ruff linting and formatting
   - MyPy type checking
   - Bandit security analysis

3. **Testing**:
   - Full test suite with PostgreSQL 16
   - Runs after security and lint checks pass
   - Uses GitHub environments for configuration management

**Infrastructure:**

- **PostgreSQL Service**: Containerized database for integration testing
- **Health Checks**: Ensures database readiness before tests
- **Environment Variables**: Secure handling of secrets and configuration
- **Custom Actions**: Reusable workflow components for setup, security, linting, and testing

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: /api/swagger/
- **OpenAPI Schema**: /api/schema/

## Project Structure

```
src/
├── theary/                 # Django project settings
│   ├── settings.py         # Main configuration
│   ├── urls.py            # Root URL routing
│   └── asgi.py            # ASGI application
├── api/
│   └── tree/              # Tree API application
│       ├── models.py      # TreeNode model
│       ├── views.py       # API views
│       ├── serializers.py # Pydantic serializers
│       ├── urls.py        # API URL routing
│       └── tests/         # Test modules
└── manage.py              # Django management script
```

## Data Model

### TreeNode

- **id**: Auto-incrementing primary key (automatically assigned upon creation)
- **label**: Node label (1-255 characters, duplicates allowed)
- **parent**: Self-referential foreign key (null for root nodes)
- **created_at**: Automatic timestamp

### Relationships

- Each node can have one parent (or null for roots)
- Each node can have multiple children
- Since IDs are automatically assigned, repeated labels are permitted across different nodes

## Logging

The application uses structured logging with different formats:

- **Development**: Human-readable console output
- **Production**: JSON-formatted logs for log aggregation

Log levels by component:

- **django**: INFO level
- **api**: DEBUG level (detailed API operation logs)

## Error Handling

All API errors return standardized JSON responses:

```json
{
  "error": "Primary error message",
  "details": "Additional context (optional)"
}
```

Common error scenarios:

- **400**: Validation errors, invalid parent ID
- **404**: Parent node not found
- **500**: Server errors

## Performance Considerations

- **Async Views**: Non-blocking I/O for better concurrency
- **Query Optimization**: Uses `prefetch_related` for efficient tree loading
- **Transaction Safety**: Atomic database operations
- **Connection Pooling**: PostgreSQL connection management
