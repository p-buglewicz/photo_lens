# LensAnalytics Tests

This directory contains the test suite for LensAnalytics.

## Running Tests Locally

### Run all tests

```bash
make test
```

### Run tests with coverage report

```bash
make test-cov
```

The coverage report will be generated in `htmlcov/index.html`.

### Run specific test file

```bash
uv run pytest tests/test_health.py -v
```

### Run specific test function

```bash
uv run pytest tests/test_health.py::test_health_check -v
```

## Test Structure

- **test_health.py** - Health check endpoint tests
- **test_config.py** - Configuration loading tests
- **test_main.py** - FastAPI application initialization tests
- **conftest.py** - Pytest fixtures and configuration

## CI/CD Pipeline

Tests are automatically run on every push via GitLab CI/CD. The pipeline runs:

1. **Unit tests** with coverage reporting
2. **Code linting** (ruff, black formatting checks)
3. **Type checking** (mypy)

See `.gitlab-ci.yml` for the full pipeline configuration.

## Adding New Tests

When adding new tests:

1. Create a new file named `test_*.py` in the `tests/` directory
2. Import the `client` fixture from `conftest.py` for API tests
3. Use descriptive test names starting with `test_`
4. Add docstrings explaining what the test verifies

Example:

```python
from fastapi.testclient import TestClient

def test_new_endpoint(client: TestClient) -> None:
    """Test new endpoint behavior."""
    response = client.get("/api/endpoint")
    assert response.status_code == 200
```

## Test Dependencies

The test suite requires these dev dependencies (installed via `make setup`):

- pytest
- pytest-cov
- pytest-asyncio
- httpx
