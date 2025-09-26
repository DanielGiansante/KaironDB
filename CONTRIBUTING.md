# Contributing to KaironDB

Thank you for your interest in contributing to KaironDB! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- Git
- Make (optional, for using Makefile commands)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/KaironDB.git
   cd KaironDB
   ```

2. **Install development dependencies**
   ```bash
   make install-dev
   # or
   pip install -e .[dev]
   ```

3. **Setup pre-commit hooks**
   ```bash
   make dev-setup
   # or
   pre-commit install
   ```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test modules
make test-bridge
make test-models
make test-exceptions
make test-logging
make test-queries

# Quick test run
make quick-test
```

### Writing Tests

- Place tests in the `tests/` directory
- Follow the naming convention: `test_*.py`
- Use descriptive test names
- Include docstrings explaining what each test does
- Use fixtures from `conftest.py` when appropriate

## 📝 Code Style

### Formatting

We use `black` and `isort` for code formatting:

```bash
# Format code
make format

# Check formatting
make lint
```

### Type Hints

- Use type hints for all function parameters and return values
- Use `typing` module for complex types
- Run `mypy` to check type consistency

### Documentation

- Use docstrings for all public functions and classes
- Follow Google docstring format
- Include examples in docstrings when helpful

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Description**: Clear description of the issue
2. **Steps to reproduce**: Detailed steps to reproduce the bug
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Environment**: Python version, OS, KaironDB version
6. **Code example**: Minimal code example that reproduces the issue

## ✨ Feature Requests

When requesting features, please include:

1. **Description**: Clear description of the feature
2. **Use case**: Why this feature would be useful
3. **Proposed solution**: How you think it should work
4. **Alternatives**: Other solutions you've considered

## 🔧 Development Workflow

### Branch Naming

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

Follow the conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks

### Pull Request Process

1. **Create a feature branch** from `main`
2. **Make your changes** following the guidelines
3. **Write tests** for new functionality
4. **Update documentation** if needed
5. **Run the test suite** to ensure everything passes
6. **Submit a pull request** with a clear description

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] All tests pass in CI

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

## 🏗️ Project Structure

```
KaironDB/
├── src/kairondb/          # Main package
│   ├── __init__.py
│   ├── bridge.py          # SQLBridge implementation
│   ├── models.py          # Model system
│   ├── query.py           # Q objects
│   └── exceptions.py      # Exception hierarchy
├── tests/                 # Test suite
├── docs/                  # Documentation
├── GO/                    # Go backend source
├── build/                 # Build artifacts
├── dist/                  # Distribution packages
└── requirements*.txt      # Dependencies
```

## 📚 Resources

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [Conventional Commits](https://www.conventionalcommits.org/)

## 🤝 Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow the golden rule

## 📞 Getting Help

- Open an issue for questions
- Join our discussions for general chat
- Check existing issues before creating new ones

Thank you for contributing to KaironDB! 🎉
