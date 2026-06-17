"""Pytest config for the Hongmen after-sales backend tests.

Currently the test suite is empty (see tests/__init__.py). This file
exists so that:

  1. `pytest` discovers the tests/ package and reports "0 collected"
     instead of "no tests ran".
  2. When future tests are added they have a known place to register
     package-level fixtures (app, db, client, auth_headers, ...).

Add fixtures here, e.g.:

    import pytest
    from app import create_app, db
    from config import TestConfig

    @pytest.fixture
    def app():
        app = create_app(TestConfig)
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()

    @pytest.fixture
    def client(app):
        return app.test_client()
"""
