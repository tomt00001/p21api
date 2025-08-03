# GitHub Copilot Instructions

## Priority Guidelines

When generating code for this repository:

1. **Version Compatibility**: Always detect and respect the exact versions of languages, frameworks, and libraries used in this project
2. **Context Files**: Prioritize patterns and standards defined in the .github/copilot directory
3. **Codebase Patterns**: When context files don't provide specific guidance, scan the codebase for established patterns
4. **Architectural Consistency**: Maintain our Layered architectural style and established boundaries
5. **Code Quality**: Prioritize maintainability, performance, security, accessibility, and testability in all generated code

## Naming Conventions

- **Files/Modules**: Use `snake_case` (e.g., `report_daily_sales.py`)
- **Classes**: Use `PascalCase` (e.g., `ReportDailySales`)
- **Functions/Methods/Variables**: Use `snake_case`
- **Test Files**: Mirror the structure of the main code (e.g., `tests/reports/test_report_x.py` for `p21api/report_x.py`)

## Technology Version Detection

Before generating code, scan the codebase to identify:

1. **Language Versions**: Detect the exact versions of programming languages in use

   - Examine project files, configuration files, and package managers
   - Look for language-specific version indicators (e.g., requires-python in pyproject.toml)
   - Never use language features beyond the detected version

2. **Framework Versions**: Identify the exact versions of all frameworks

   - Check pyproject.toml and requirements in the codebase
   - Respect version constraints when generating code
   - Never suggest features not available in the detected framework versions

3. **Library Versions**: Note the exact versions of key libraries and dependencies
   - Generate code compatible with these specific versions
   - Never use APIs or features not available in the detected versions

## Context Files

Prioritize the following files in .github/copilot directory (if they exist):

- **architecture.md**: System architecture guidelines
- **tech-stack.md**: Technology versions and framework details
- **coding-standards.md**: Code style and formatting standards
- **folder-structure.md**: Project organization guidelines
- **exemplars.md**: Exemplary code patterns to follow

## Codebase Scanning Instructions

When context files don't provide specific guidance:

1. Identify similar files to the one being modified or created
2. Analyze patterns for:
   - Naming conventions
   - Code organization
   - Error handling
   - Logging approaches
   - Documentation style
   - Testing patterns
3. Follow the most consistent patterns found in the codebase
4. When conflicting patterns exist, prioritize patterns in newer files or files with higher test coverage
5. Never introduce patterns not found in the existing codebase

## Docstring and Documentation Style

- Use **Google-style docstrings** for all public APIs (see examples in `p21api/report_base.py`)
- Document parameters, return values, and exceptions as in exemplar files
- Match the level of detail and format found in the best-documented files

## Code Quality Standards

### Maintainability

- Write self-documenting code with clear naming
- Follow the naming and organization conventions evident in the codebase
- Follow established patterns for consistency
- Keep functions focused on single responsibilities
- Limit function complexity and length to match existing patterns

## Exemplar Files

- Use the following as reference for best practices:
  - `p21api/report_base.py` (base class, docstring, and type hinting patterns)
  - `p21api/logging_config.py` (logging setup and usage)
  - `p21api/container.py` (dependency injection pattern)
  - `tests/reports/test_report_daily_sales.py` (test structure and style)

### Performance

- Follow existing patterns for memory and resource management
- Match existing patterns for handling computationally expensive operations
- Follow established patterns for asynchronous operations
- Apply caching consistently with existing patterns
- Optimize according to patterns evident in the codebase

### Security

- Follow existing patterns for input validation
- Apply the same sanitization techniques used in the codebase
- Use parameterized queries matching existing patterns
- Follow established authentication and authorization patterns
- Handle sensitive data according to existing patterns

### Accessibility

- Follow existing accessibility patterns in the codebase
- Maintain keyboard navigation support consistent with existing code

### Testability

- Follow established patterns for testable code
- Match dependency injection approaches used in the codebase
- Apply the same patterns for managing dependencies
- Follow established mocking and test double patterns
- Match the testing style used in existing tests

## Documentation Requirements

- Follow the most detailed documentation patterns found in the codebase
- Match the style and completeness of the best-documented code
- Document exactly as the most thoroughly documented files do
- Follow existing patterns for linking documentation
- Match the level of detail in explanations of design decisions

## Configuration and Environment Patterns

- All new features must support `.env`-style configuration and fallback to GUI for missing/invalid config
- Reference `p21api/config.py` and `environment_config.py` for configuration patterns

## Testing Approach

### Unit Testing

- Match the exact structure and style of existing unit tests
- Follow the same naming conventions for test classes and methods
- Use the same assertion patterns found in existing tests
- Apply the same mocking approach used in the codebase
- Follow existing patterns for test isolation

### Integration Testing

- Follow the same integration test patterns found in the codebase
- Match existing patterns for test data setup and teardown
- Use the same approach for testing component interactions
- Follow existing patterns for verifying system behavior

### End-to-End Testing

- Match the existing E2E test structure and patterns
- Follow established patterns for UI testing
- Apply the same approach for verifying user journeys

### Test-Driven Development

- Follow TDD patterns evident in the codebase
- Match the progression of test cases seen in existing code
- Apply the same refactoring patterns after tests pass

## Python Guidelines

- Detect and adhere to the specific Python version in use (see pyproject.toml)
- Follow the same import organization found in existing modules
- Match type hinting approaches if used in the codebase
- Apply the same error handling patterns found in existing code
- Follow the same module organization patterns

## Dependency Injection Pattern

- Use the dependency injection approach as implemented in `p21api/container.py`
- Prefer constructor injection for core dependencies
- Register and resolve dependencies using the established container pattern

## Version Control Guidelines

- Follow Semantic Versioning patterns as applied in the codebase
- Match existing patterns for documenting breaking changes
- Follow the same approach for deprecation notices

## General Best Practices

- Follow naming conventions exactly as they appear in existing code
- Match code organization patterns from similar files
- Apply error handling consistent with existing patterns
- Follow the same approach to testing as seen in the codebase
- Match logging patterns from existing code
- Use the same approach to configuration as seen in the codebase

## Linting and Formatting

- All code must pass `ruff check .` and `ruff format .` before merging.
- Linting and formatting errors should be fixed in the same PR as the code change.

## Security and Secrets

- Never hardcode secrets or credentials. Always use `.env` files or environment variables for sensitive data.

## Documentation

- All public classes, methods, and functions must have Google-style docstrings.
- If Sphinx or another tool is used for documentation, ensure new/changed code builds cleanly with the docs tool.

## Example: Good vs. Bad Module

### Good Example

```python
from p21api.config import Config
from p21api.odata_client import ODataClient
from pydantic import BaseModel

class ReportParams(BaseModel):
    start_date: str
    end_date: str

def fetch_data(config: Config, client: ODataClient, params: ReportParams) -> list[dict]:
    """Fetch report data from OData API.

    Args:
        config: App configuration.
        client: OData API client.
        params: Report parameters.

    Returns:
        List of result dicts.
    """
    try:
        return client.get_data(params.start_date, params.end_date)
    except Exception as exc:
        config.logger.error(f"Failed to fetch data: {exc}")
        raise
```

### Bad Example

```python
def getData(cfg, cli, s, e):
    # fetches data
    return cli.get_data(s, e)
```

## Project-Specific Guidance

- Scan the codebase thoroughly before generating any code
- Respect existing architectural boundaries without exception
- Match the style and patterns of surrounding code
- When in doubt, prioritize consistency with existing code over external best practices
