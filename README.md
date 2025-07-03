# P21 API Data Exporter

A robust Python application for extracting and processing data from P21 ERP systems via OData API. This tool provides automated data export capabilities with configurable report generation, comprehensive error handling, and both GUI and command-line interfaces.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## 🚀 Features

- **Multiple Report Types**: Support for inventory, sales, invoices, and consolidation reports
- **Flexible Configuration**: Environment-based settings with GUI fallback
- **Async Processing**: Concurrent report execution for improved performance
- **Comprehensive Logging**: Structured logging with multiple output formats
- **Error Handling**: Robust error management with detailed reporting
- **GUI Interface**: PyQt6-based graphical interface for easy configuration
- **CLI Support**: Full command-line interface for automation
- **Type Safety**: Full type hints with mypy compatibility
- **High Test Coverage**: Comprehensive test suite with pytest

## 📋 Requirements

- Python 3.12 or higher
- P21 ERP system with OData API access
- Valid P21 credentials

## 🛠️ Installation

### Using uv (Recommended)

```bash
git clone <repository-url>
cd p21api
uv sync
```

### Using pip

```bash
git clone <repository-url>
cd p21api
pip install -e .
```

## ⚙️ Configuration

### Environment Variables

Create an `env` file in the project root:

```bash
# P21 Connection Settings
base_url=https://your-p21-server.com
username=your_username
password=your_password

# Report Settings
report_groups=monthly,inventory
output_folder=output/
start_date=2024-01-01

# Application Settings
debug=false
show_gui=false
```

### Available Report Groups

- **monthly**: Daily sales, monthly invoices, consolidation reports
- **inventory**: Current inventory reports
- **po**: Purchase order and inventory value reports

## 🖥️ Usage

### Command Line Interface

```bash
# Run with environment configuration
python main.py

# Enable debug mode
DEBUG=true python main.py

# Show GUI for configuration
SHOW_GUI=true python main.py
```

### Programmatic Usage

```python
from p21api.config import Config
from p21api.odata_client import ODataClient
from p21api.async_runner import AsyncReportRunner

# Initialize configuration
config = Config()

# Create OData client
client = ODataClient(
    username=config.username,
    password=config.password,
    base_url=config.base_url
)

# Run reports asynchronously
runner = AsyncReportRunner(max_workers=5)
results = await runner.run_reports_async(
    report_classes=config.get_reports(),
    config=config,
    client=client
)
```

### GUI Interface

Launch the GUI for interactive configuration:

```bash
python main.py --gui
```

## 📊 Report Types

### Monthly Reports

- **Daily Sales**: Daily sales transaction summaries
- **Monthly Invoices**: Complete invoice data for the month
- **Monthly Consolidation**: Consolidated monthly business metrics
- **JARP Reports**: Specialized JARP data exports
- **Kennametal POS**: Point-of-sale data for Kennametal products
- **Open Orders**: Currently open customer orders

### Inventory Reports

- **Current Inventory**: Real-time inventory levels
- **Inventory Value**: Inventory valuation reports

### Purchase Order Reports

- **Open PO**: Outstanding purchase orders
- **Inventory Value**: Purchase-related inventory valuations

## 🔧 Development

### Setup Development Environment

```bash
# Install with development dependencies
uv sync --group dev

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run tests with coverage
pytest --cov=p21api --cov-report=html

# Format code
ruff format .

# Lint code
ruff check . --fix
```

### Project Structure

```
p21api/
├── p21api/                 # Main package
│   ├── config.py          # Configuration management
│   ├── odata_client.py    # OData API client
│   ├── report_base.py     # Base report class
│   ├── report_*.py        # Specific report implementations
│   ├── async_runner.py    # Async report execution
│   ├── container.py       # Dependency injection
│   ├── environment_config.py # Environment settings
│   └── logging_config.py  # Logging configuration
├── gui/                   # GUI components
├── tests/                 # Test suite
├── output/                # Generated reports
├── main.py               # Application entry point
└── pyproject.toml        # Project configuration
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config.py

# Run with coverage
pytest --cov=p21api --cov-report=term-missing

# Run performance tests
pytest -m performance

# Run integration tests
pytest -m integration
```

## 📈 Performance

- **Concurrent Execution**: Run multiple reports simultaneously
- **Configurable Workers**: Adjust concurrency based on system capabilities
- **Memory Efficient**: Streaming data processing for large datasets
- **Connection Pooling**: Efficient API connection management

## 🛡️ Security

- **Credential Management**: Secure handling of authentication data
- **Input Validation**: Comprehensive validation of all inputs
- **Error Sanitization**: Safe error messages without credential exposure
- **Environment Isolation**: Separate configurations per environment

## 📝 Logging

The application provides comprehensive logging with multiple levels and outputs:

- **Console Logging**: Colored output for development
- **File Logging**: Rotating file logs for production
- **Structured Logging**: JSON format for log aggregation
- **Performance Metrics**: Execution time and resource usage tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

This project uses:

- **Ruff** for linting and formatting
- **Type hints** for all functions and methods
- **Docstrings** for all public APIs
- **Pytest** for testing

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- [P21 Documentation](https://www.p21.com/)
- [OData Protocol](https://www.odata.org/)
- [PyQt6 Documentation](https://doc.qt.io/qtforpython/)

## 📞 Support

For support and questions:

1. Check the [documentation](docs/)
2. Search [existing issues](issues/)
3. Create a [new issue](issues/new)

---

**Note**: This tool requires valid P21 ERP system access and appropriate permissions for OData API endpoints.
