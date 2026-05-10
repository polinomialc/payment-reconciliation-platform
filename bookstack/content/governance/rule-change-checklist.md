# Rule Change Checklist

## Purpose

Control changes to reconciliation rules, mappings, and exception classifications.

## Checklist

1. Describe the operational issue.
2. Identify the affected source files and countries.
3. Confirm whether the issue affects matching, aging, exception handling, or reporting.
4. Add a sanitized test case.
5. Update SQL logic or mapping data.
6. Validate output totals before and after the change.
7. Update the BookStack rule page.
8. Record reviewer approval.

## Minimum Evidence

Every rule change should include:

- example source row
- expected status before the change
- expected status after the change
- affected dashboard or report
- approval note

## Ownership

The finance operations owner approves business behavior.

The data owner approves implementation and deployment.
