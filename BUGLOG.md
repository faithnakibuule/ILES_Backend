# ILES Bug Log — Week 5 Testing
**Module:** M4 — Review Workflow  
**Author:** Sserunkuuma Joshua  
**Date:** Week 5, Monday  

---

## Summary Table
| Bug # | Location | Description | Status |
|-------|----------|-------------|--------|
| BUG-001 | `logbook/views.py` — `send_back` action | View returns `None` instead of a DRF `Response` | 🔧 IN PROGRESS |
| BUG-002 | `reviews/tests.py` — `test_sent_back_back_log_notifies_student` | Fails because of BUG-001 (same root cause) | 🔧 IN PROGRESS |
| BUG-003 | `logbook/tests.py` — `test_unsubmitted_log_before_deadline_is_not_overdue` | Test setup passes a `CustomUser` object to `placement` field instead of an `InternshipPlacement` instance | 🔧 IN PROGRESS |

---

## BUG-001

**Description:**  
The `send_back` custom action in `LogViewSet` does not return a `Response` object. Django REST Framework requires every view to return a `Response`, but this function returns `None` (implicitly, because there is no `return` statement at the end of the action).

**Error Message:**