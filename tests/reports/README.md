# Report Tests

This directory contains unit tests for individual P21 API report implementations, broken down by report type for better maintainability.

## Structure

- `test_report_daily_sales.py` - Tests for ReportDailySales
- `test_report_inventory.py` - Tests for ReportInventory
- `test_report_inventory_value.py` - Tests for ReportInventoryValue
- `test_report_jarp.py` - Tests for ReportJarp
- `test_report_kennametal_pos.py` - Tests for ReportKennametalPos
- `test_report_monthly_consolidation.py` - Tests for ReportMonthlyConsolidation
- `test_report_monthly_invoices.py` - Tests for ReportMonthlyInvoices
- `test_report_open_orders.py` - Tests for ReportOpenOrders
- `test_report_open_po.py` - Tests for ReportOpenPO
- `test_report_integration.py` - Integration tests across multiple reports

## Benefits of This Structure

1. **Improved Readability**: Each report's tests are isolated in their own file
2. **Easier Maintenance**: When modifying a specific report, you only need to focus on its corresponding test file
3. **Better Organization**: Tests are logically grouped by functionality
4. **Parallel Testing**: Individual test files can be run independently
5. **Reduced Cognitive Load**: Smaller files are easier to understand and navigate

## Running Tests

Run all report tests:
```bash
pytest tests/reports/
```

Run tests for a specific report:
```bash
pytest tests/reports/test_report_daily_sales.py
```

Run with verbose output:
```bash
pytest tests/reports/ -v
```

## Shared Fixtures

All test files use fixtures defined in the root `conftest.py`:
- `mock_config` - Mock configuration object
- `mock_odata_client` - Mock OData client
- `sample_invoice_data` - Sample invoice data for testing
- `sample_inventory_data` - Sample inventory data for testing

## Migration Notes

The original `test_reports.py` file (1,080+ lines) has been split into these smaller, focused test files. A backup of the original file is available as `test_reports_backup.py`.
