"""Test package for the Hongmen after-sales backend.

Historically this directory contained 8 test_*.py files that
exercised the old services/ layer (wechat_service, product_service,
work_order_service, fault_service, admin_service). Those modules
were removed in commit bea811f when the business logic moved into
role-scoped API blueprints.

Rather than keep a suite that fails to import, the test files were
removed. The package is intentionally empty so that:

  $ pytest
  ============================= test session starts ======================
  collected 0 items
  ============================== 0 passed in 0.01s =======================

Future tests should target the new structure:

  - app/api/customer.py  (login, products, orders, faults)
  - app/api/admin.py     (user/sp/engineer/order/fault CRUD)
  - app/api/auth.py      (login_required, role_required)
  - app/services/auth_service.py  (JWT issue/decode, password hashing)
  - app/models/*.py      (WorkOrder.STATUS_FLOW, FaultCategory tree, ...)

Recommended fixtures live in conftest.py at the package root and
should construct an in-memory SQLite engine plus a `TestConfig`
subclass of Config (it was removed alongside TestConfig during the
refactor; restore it when adding tests).
"""
