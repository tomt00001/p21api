# OData API Reference and Limitations

## Overview

This project uses the P21 OData Data Service, which exposes ERP data via the OData v4 protocol (with some legacy v3/v1 references for compatibility). The service provides stable, fast, read-only querying against defined views in the ERP database, without exposing the database server directly.

## OData Version and Implementation

- **Protocol:** OData v4 (with some v3/v1 legacy support)
- **Backend:** Epicor P21 Middleware
- **Authentication:** P21 token authentication (user credentials or consumer key)
- **Authorization:**
  - Application Security: User must have "Allow OData API Service" enabled
  - Role Level: Role must have explicit table/view permissions in 'Dataservice Permission'
- **Schema Refresh:**
  - Schema changes require a manual refresh in the admin UI ("Refresh OData API service") unless an application upgrade is performed

## Supported OData Query Options

| Option      | Supported | Notes                                                                         |
| ----------- | --------- | ----------------------------------------------------------------------------- |
| $count      | Yes       | Returns count of matching resources                                           |
| $filter     | Yes       | Supports eq, ne, gt, ge, lt, le, and, or, not, endswith, startswith, contains |
| $orderby    | Yes       | Sort results                                                                  |
| $select     | Yes       | Select specific properties                                                    |
| $skip       | Yes       | Skip N records (for paging)                                                   |
| $top        | Yes       | Limit number of records                                                       |
| Paging      | No        | No server-driven paging                                                       |
| substringof | No        | Not supported as of OData 4.0                                                 |

### Filter Data Types

- **String:** single quotes (e.g. `$filter=name eq 'John'`)
- **Numeric:** no quotes (e.g. `$filter=age eq 30`)
- **DateTime:** ISO format, no quotes (e.g. `$filter=date_created gt 2019-01-01T00:00:00.000Z`)
- **Guid:** no quotes (e.g. `$filter=id eq 5BC2E4CE-0C0A-4394-A066-29B5835424DA`)
- **Boolean:** true/false (e.g. `$filter=active eq true`)

### Example Queries

```
# Get all users, select only id
GET /odataservice/odata/table/users?$select=id

# Filter by id
GET /odataservice/odata/view/p21_view_users?$filter=id eq 'binod.mahto'

# Order by field
GET /odataservice/odata/table/users?$orderby=designer_rights asc

# Paging (manual)
GET /odataservice/odata/table/users?$top=10&$skip=10

# Count
GET /odataservice/odata/table/users?$count=true
```

### Supported $filter Expressions

- eq, ne, gt, ge, lt, le
- and, or, not
- endswith, startswith, contains

### Not Supported

- substringof
- Server-driven paging

## Schema Discovery

- The OData $metadata endpoint is available at:
  - `{base_url}/odataservice/odata/$metadata`
- To enumerate all available entity sets, properties, and navigation properties, run:
  - `uv run python fetch_odata_metadata.py` (fetches and saves the XML)
  - `uv run python parse_odata_metadata.py` (generates Markdown summary)
- The summary is written to `odata_schema/odata_schema_summary.md`.

## Administration

- To refresh the OData schema after changes:
  - Login to SOA middleware home page
  - Go to Administration > Refresh OData API service > Click "Refresh OData API service"

## References

- [OData Official Site](https://www.odata.org/)
- [Epicor P21 Documentation](https://p21.epicor.com/)

---

This file should be kept up to date as the OData API or its implementation changes.
