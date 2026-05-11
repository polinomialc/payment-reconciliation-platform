# Screenshot Placement Guide

Save real application screenshots in this folder after running the local demos.

Do not commit screenshots that contain private data, personal browser information, API tokens, or local credentials.

## Recommended Files

| File name | Source | What it should show |
| --- | --- | --- |
| `streamlit_operations_dashboard.png` | `http://localhost:8501` | Operations dashboard with KPIs, aging, and exception overview |
| `streamlit_receipt_reconciliation.png` | `http://localhost:8501/?view=receipt&receipt=receipt_ref_001` | Receipt-level reconciliation with line outcomes and payment groups |
| `bookstack_knowledge_library.png` | `http://localhost:6875` | BookStack shelves/books showing procedures and business knowledge |
| `metabase_aging_exposure.png` | `http://localhost:3000` | Metabase card for open exposure by aging bucket |
| `metabase_management_dashboard.png` | `http://localhost:3000` | Full Metabase dashboard with KPI cards and charts |

## Suggested README Use

After screenshots are added, link them from the root README under a `Demo Screenshots` section.

Example:

```md
## Demo Screenshots

### Streamlit Operations
![Streamlit operations dashboard](docs/screenshots/streamlit_operations_dashboard.png)

### Metabase Reporting
![Metabase management dashboard](docs/screenshots/metabase_management_dashboard.png)

### BookStack Knowledge Library
![BookStack knowledge library](docs/screenshots/bookstack_knowledge_library.png)
```
