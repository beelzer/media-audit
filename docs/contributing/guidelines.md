# Contributing Guidelines

Welcome to Media Audit! We're excited that you want to contribute to this project. This guide outlines our development process, coding standards, and how to get your contributions accepted.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Documentation](#documentation)
- [Release Process](#release-process)

## Code of Conduct

### Our Standards

We are committed to providing a welcoming and inclusive experience for everyone. We expect all contributors to:

- **Be Respectful**: Treat everyone with respect and consideration
- **Be Collaborative**: Work together constructively and assume good faith
- **Be Inclusive**: Welcome and support people of all backgrounds and identities
- **Be Professional**: Focus on what is best for the community and project

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Personal attacks or trolling
- Publishing private information without permission
- Any conduct that would be inappropriate in a professional setting

### Enforcement

Project maintainers are responsible for clarifying standards and will take corrective action in response to any behavior deemed inappropriate. Report issues to the project maintainers.

## Getting Started

### Before You Contribute

1. **Read the Documentation**: Familiarize yourself with the project by reading:
   - [Project Overview](../index.md)
   - [Architecture Overview](../architecture/overview.md)
   - [Development Setup](setup.md)

2. **Set Up Development Environment**: Follow the [setup guide](setup.md) to prepare your local environment

3. **Explore the Codebase**: Browse the source code to understand the project structure

4. **Check Existing Issues**: Look for open issues that match your interests or create new ones

### Types of Contributions

We welcome various types of contributions:

- **Bug Fixes**: Fix reported bugs or issues you discover
- **New Features**: Add functionality that enhances the project
- **Documentation**: Improve existing docs or add new documentation
- **Tests**: Add test coverage or improve existing tests
- **Performance**: Optimize code for better performance
- **Refactoring**: Improve code structure and maintainability

## Development Process

### 1. Planning

Before starting work on significant changes:

1. **Create or Find an Issue**: Discuss the change in a GitHub issue
2. **Get Feedback**: Allow maintainers and community to provide input
3. **Plan the Implementation**: Consider architecture and design implications
4. **Break Down Work**: Split large features into smaller, manageable parts

### 2. Implementation

1. **Create a Branch**: Use descriptive branch names

   ```bash
   git checkout -b feature/add-anime-parser
   git checkout -b fix/caching-race-condition
   git checkout -b docs/improve-api-reference
   ```

2. **Follow Coding Standards**: Adhere to the project's coding conventions
3. **Write Tests**: Include appropriate test coverage
4. **Update Documentation**: Keep docs in sync with code changes
5. **Test Locally**: Ensure all tests pass and functionality works

### 3. Review and Merge

1. **Create Pull Request**: Submit your changes for review
2. **Address Feedback**: Respond to review comments promptly
3. **Update as Needed**: Make requested changes
4. **Merge**: Maintainers will merge approved changes

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some project-specific conventions:

#### Code Formatting

- **Line Length**: 100 characters maximum (configured in Ruff)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings, single quotes for string literals in code
- **Imports**: Organized using Ruff's import sorting

Example:

```python
from pathlib import Path
from typing import Any, Dict, List, Optional

from media_audit.core import MovieItem, ValidationStatus


class MovieParser:
    """Parser for movie directory structures."""

    def __init__(self, patterns: CompiledPatterns, cache: Optional[MediaCache] = None):
        """Initialize movie parser.

        Args:
            patterns: Compiled regex patterns for asset matching
            cache: Optional cache for performance optimization
        """
        self.patterns = patterns
        self.cache = cache

    def parse(self, directory: Path) -> Optional[MovieItem]:
        """Parse movie directory and return MovieItem.

        Args:
            directory: Path to movie directory

        Returns:
            MovieItem if parsing successful, None otherwise

        Raises:
            ValidationError: If directory structure is invalid
        """
        if not self._is_movie_directory(directory):
            return None

        # Implementation...
```

#### Type Hints

- **Required**: All public functions and methods must have type hints
- **Modern Syntax**: Use Python 3.9+ type hint syntax where possible
- **Generics**: Use appropriate generic types for collections

```python
from typing import Dict, List, Optional, Union
from pathlib import Path

# Good
def process_files(file_paths: List[Path]) -> Dict[str, Any]:
    """Process multiple files and return results."""
    pass

# Better (Python 3.9+)
def process_files(file_paths: list[Path]) -> dict[str, Any]:
    """Process multiple files and return results."""
    pass

# Use Union for multiple types
def get_config_value(key: str) -> Union[str, int, bool, None]:
    """Get configuration value of various types."""
    pass

# Use Optional for nullable values
def find_video_file(directory: Path) -> Optional[Path]:
    """Find primary video file in directory."""
    pass
```

#### Docstrings

Use Google-style docstrings for all public functions, classes, and modules:

```python
def validate_movie(movie: MovieItem, config: ValidationConfig) -> List[ValidationIssue]:
    """Validate movie against configuration rules.

    Performs comprehensive validation of movie assets, video quality,
    and structural requirements based on the provided configuration.

    Args:
        movie: Movie item to validate
        config: Validation configuration with rules and thresholds

    Returns:
        List of validation issues found, empty if movie is valid

    Raises:
        ValidationError: If movie data is malformed or config is invalid

    Example:
        >>> movie = MovieItem(name="Test Movie", path=Path("/movies/test"))
        >>> config = ValidationConfig(require_trailer=True)
        >>> issues = validate_movie(movie, config)
        >>> len(issues)
        0
    """
    pass
```

#### Error Handling

- **Specific Exceptions**: Catch specific exceptions rather than bare `except:`
- **Error Messages**: Provide clear, actionable error messages
- **Logging**: Use appropriate logging levels
- **Graceful Degradation**: Continue processing when possible

```python
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def parse_movie_directory(directory: Path) -> Optional[MovieItem]:
    """Parse movie directory with proper error handling."""
    try:
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return None

        if not directory.is_dir():
            logger.error(f"Path is not a directory: {directory}")
            return None

        return _parse_movie_contents(directory)

    except PermissionError:
        logger.warning(f"Permission denied accessing directory: {directory}")
        return None
    except OSError as e:
        logger.error(f"OS error processing directory {directory}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing directory {directory}: {e}")
        return None
```

### Project-Specific Conventions

#### File Organization

```text
src/media_audit/
├── __init__.py          # Package initialization
├── cli.py              # Command-line interface
├── config.py           # Configuration management
├── models.py           # Data models
├── patterns.py         # Pattern matching
├── validator.py        # Validation logic
├── parsers/            # Content parsers
│   ├── __init__.py
│   ├── base.py         # Base parser class
│   ├── movie.py        # Movie parser
│   └── tv.py           # TV show parser
├── probe/              # Video analysis
│   ├── __init__.py
│   └── ffprobe.py      # FFprobe integration
├── report/             # Report generation
│   ├── __init__.py
│   ├── html.py         # HTML report generator
│   └── json.py         # JSON report generator
└── scanner/            # Main scanning logic
    ├── __init__.py
    └── scanner.py      # Media scanner
```

#### Naming Conventions

- **Classes**: PascalCase (`MediaScanner`, `ValidationIssue`)
- **Functions/Methods**: snake_case (`parse_directory`, `validate_movie`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_WORKERS`, `VIDEO_EXTENSIONS`)
- **Private Members**: Leading underscore (`_internal_method`, `_cache_data`)

#### Import Organization

1. **Standard Library**: Python built-in modules
2. **Third-Party**: External dependencies
3. **Local**: Project modules

```python
# Standard library
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# Third-party
import click
from rich.console import Console

# Local
from media_audit.core import MovieItem, ValidationStatus
from media_audit.domain.patterns import CompiledPatterns
```

## Commit Guidelines

### Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/) format:

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic changes)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance tasks, dependency updates
- **ci**: CI/CD changes
- **build**: Build system changes

#### Examples

```bash
# Simple feature
git commit -m "feat: add support for anime directory parsing"

# Bug fix with scope
git commit -m "fix(parser): handle special characters in movie titles"

# Documentation update
git commit -m "docs: update API reference for new validation rules"

# Breaking change
git commit -m "feat!: change configuration file format to YAML"

# With body and footer
git commit -m "fix(cache): resolve race condition in concurrent access

The cache was not thread-safe when multiple workers accessed
the same cache entry simultaneously. Added proper locking
mechanism to prevent data corruption.

Fixes #123
Closes #124"
```

### Commit Best Practices

1. **Atomic Commits**: Each commit should represent a single logical change
2. **Clear Messages**: Write descriptive commit messages
3. **Test Before Commit**: Ensure all tests pass
4. **Squash When Appropriate**: Clean up commit history before merging

## Pull Request Process

### Before Creating a PR

1. **Sync with Main**: Ensure your branch is up-to-date

   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run All Checks**: Verify everything passes locally

   ```bash
   pytest                      # Run tests
   ruff check src tests       # Linting
   ruff format src tests      # Formatting
   mypy src                   # Type checking
   ```

3. **Update Documentation**: Ensure docs reflect your changes

### PR Description Template

```markdown
## Description
Brief description of what this PR accomplishes.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that causes existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Changes Made
- List key changes made
- Include any architectural decisions
- Note any breaking changes

## Related Issues
Fixes #123
Closes #124

## Screenshots/Examples
Include screenshots or examples if applicable.
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs automated tests
2. **Code Review**: Maintainers and community review code
3. **Address Feedback**: Make requested changes
4. **Final Approval**: Maintainer approves and merges

### Review Criteria

Reviewers will check for:

- **Functionality**: Does the code work as intended?
- **Code Quality**: Is the code clean, readable, and maintainable?
- **Tests**: Is there adequate test coverage?
- **Documentation**: Are docs updated appropriately?
- **Performance**: Are there any performance concerns?
- **Security**: Are there any security implications?

## Issue Guidelines

### Reporting Bugs

Use the bug report template:

```markdown
## Bug Description
A clear description of what the bug is.

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- OS: [e.g., Windows 10, macOS 12, Ubuntu 20.04]
- Python Version: [e.g., 3.13.0]
- Media Audit Version: [e.g., 1.2.3]
- FFmpeg Version: [e.g., 4.4.0]

## Additional Context
Add any other context about the problem.

## Sample Media Structure
If relevant, provide example directory structure.
```

### Feature Requests

Use the feature request template:

```markdown
## Feature Description
Clear description of the desired feature.

## Use Case
Explain why this feature would be useful.

## Proposed Solution
Describe how you envision this working.

## Alternatives Considered
Other approaches you've considered.

## Additional Context
Any other relevant information.
```

### Issue Labels

We use labels to categorize issues:

- **Type**: `bug`, `enhancement`, `documentation`, `question`
- **Priority**: `low`, `medium`, `high`, `critical`
- **Difficulty**: `good-first-issue`, `help-wanted`, `expert-needed`
- **Area**: `parser`, `validator`, `scanner`, `reports`, `cli`
- **Status**: `needs-discussion`, `ready`, `in-progress`, `blocked`

## Documentation

### Documentation Standards

- **Markdown**: Use Markdown for all documentation
- **Clear Structure**: Use appropriate headings and organization
- **Code Examples**: Include working code examples
- **Screenshots**: Add screenshots for UI-related features
- **Links**: Link to related documentation and external resources

### Types of Documentation

1. **API Documentation**: Auto-generated from docstrings
2. **User Guides**: How-to guides for end users
3. **Developer Guides**: Technical documentation for contributors
4. **Architecture**: System design and component documentation

### Writing Style

- **Clear and Concise**: Use simple, direct language
- **Active Voice**: Prefer active voice over passive voice
- **Consistent Terminology**: Use the same terms throughout
- **Examples**: Include practical examples and use cases

### Documentation Updates

When making code changes, also update:

- **Docstrings**: Function and class documentation
- **User Guides**: If user-facing behavior changes
- **API Reference**: If public interfaces change
- **README**: If installation or basic usage changes

## Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Examples:

- `1.0.0` → `1.0.1` (patch: bug fix)
- `1.0.1` → `1.1.0` (minor: new feature)
- `1.1.0` → `2.0.0` (major: breaking change)

### Release Checklist

For maintainers preparing releases:

1. **Update Version**: Bump version in `pyproject.toml`
2. **Update Changelog**: Document all changes since last release
3. **Run Tests**: Ensure all tests pass on all supported platforms
4. **Build Documentation**: Update and build documentation
5. **Create Release**: Tag release and publish to PyPI
6. **Announce**: Notify community of new release

## Getting Help

### Where to Get Help

1. **Documentation**: Check existing documentation first
2. **GitHub Discussions**: Ask questions in discussions
3. **Issues**: Report bugs or request features
4. **Code Review**: Learn from review feedback

### How to Help Others

1. **Answer Questions**: Help other contributors in discussions
2. **Review PRs**: Provide constructive feedback on pull requests
3. **Improve Docs**: Update documentation when you find gaps
4. **Mentor**: Help new contributors get started

## Recognition

### Contributors

All contributors are recognized in:

- `CONTRIBUTORS.md` file
- Release notes
- Project documentation

### Types of Recognition

- **Code Contributors**: Direct code contributions
- **Documentation Contributors**: Documentation improvements
- **Community Contributors**: Helping others, discussions, reviews
- **Testing Contributors**: Bug reports, testing, feedback

## Project Governance

### Decision Making

- **Minor Changes**: Can be implemented directly by contributors
- **Major Changes**: Require discussion and maintainer approval
- **Breaking Changes**: Require broader community input

### Maintainer Responsibilities

Maintainers are responsible for:

- **Code Review**: Reviewing and approving changes
- **Release Management**: Managing releases and versioning
- **Community Management**: Fostering a welcoming community
- **Project Direction**: Guiding project evolution

Thank you for contributing to Media Audit! Your contributions make this project better for everyone.
