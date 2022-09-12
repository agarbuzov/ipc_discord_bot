import pytest

from flask import session

from ..app import app


@pytest.fixture()
def app():
    session["bot"] = {"name": "Test"}
    app.config.update({
        "TESTING": True
    })
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_request(client):
    response = client.get("/")
    assert response.status_code == 302
