# NosVid Tests

This directory contains tests for the NosVid application.

## Test Structure

The tests are organized into two main categories:

- **Unit Tests**: Located in the `unit` directory, these tests focus on testing individual components in isolation.
- **Integration Tests**: Located in the `integration` directory, these tests focus on testing how components work together.

Each test directory mirrors the structure of the `src` directory to make it easy to find tests for specific modules.

## Running Tests

You can run the tests using the `nosvid test` command:

```bash
# Run all tests
./nosvid test

# Run only unit tests
./nosvid test --unit

# Run only integration tests
./nosvid test --integration

# Run tests with coverage
./nosvid test --coverage

# Run tests for a specific module
./nosvid test tests/unit/decdata
```

Alternatively, you can use pytest directly:

```bash
# Run all tests
python -m pytest

# Run only unit tests
python -m pytest tests/unit

# Run only integration tests
python -m pytest tests/integration

# Run tests with coverage
python -m pytest --cov=src tests/

# Run tests for a specific module
python -m pytest tests/unit/decdata
```

## Writing Tests

When writing tests, follow these guidelines:

1. **Test Location**: Place tests in the appropriate directory based on whether they are unit or integration tests.
2. **Test Naming**: Name test files with a `test_` prefix and test functions with a `test_` prefix.
3. **Test Organization**: Organize tests into classes based on the component being tested.
4. **Fixtures**: Use fixtures for common setup and teardown code.
5. **Mocking**: Use mocks to isolate the component being tested.
6. **Dependency Injection**: Use dependency injection to make components more testable.

## Continuous Integration

Tests are automatically run on GitHub Actions for each push and pull request. The workflow is defined in `.github/workflows/ci.yml`.

## Code Coverage

Code coverage reports are generated for each test run and uploaded to Codecov. You can view the coverage report on the Codecov dashboard.
