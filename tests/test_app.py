"""
Tests for the Mergington High School Management System API

Uses TestClient from FastAPI and follows the AAA (Arrange-Act-Assert) pattern.
Each test is isolated by snapshotting and restoring the in-memory `activities`
dictionary from `src.app` using an autouse fixture.
"""

import copy
import uuid
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def snapshot_activities():
    """Snapshot and restore the `activities` dict between tests."""
    snapshot = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(snapshot)


@pytest.fixture
def client():
    return TestClient(app)


def test_get_activities(client):
    # Arrange: nothing special to set up

    # Act
    resp = client.get("/activities")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]


def test_signup_and_prevent_duplicates(client):
    # Arrange
    activity_name = "Chess Club"
    unique_email = f"test-{uuid.uuid4().hex}@example.com"
    encoded_activity = quote(activity_name)
    initial_count = len(activities[activity_name]["participants"])

    # Act - first signup
    resp1 = client.post(f"/activities/{encoded_activity}/signup", params={"email": unique_email})

    # Assert - first signup succeeds
    assert resp1.status_code == 200
    assert unique_email in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == initial_count + 1

    # Act - attempt duplicate signup
    resp2 = client.post(f"/activities/{encoded_activity}/signup", params={"email": unique_email})

    # Assert - duplicate prevented
    assert resp2.status_code == 400
    assert "already signed up" in resp2.json().get("detail", "")
    assert len(activities[activity_name]["participants"]) == initial_count + 1


def test_remove_participant(client):
    # Arrange: sign up a fresh participant to remove
    activity_name = "Chess Club"
    unique_email = f"remove-{uuid.uuid4().hex}@example.com"
    encoded_activity = quote(activity_name)

    signup_resp = client.post(f"/activities/{encoded_activity}/signup", params={"email": unique_email})
    assert signup_resp.status_code == 200
    assert unique_email in activities[activity_name]["participants"]
    initial_count = len(activities[activity_name]["participants"])

    # Act - remove the participant
    del_resp = client.delete(f"/activities/{encoded_activity}/participants", params={"email": unique_email})

    # Assert - removal succeeded
    assert del_resp.status_code == 200
    assert unique_email not in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == initial_count - 1

    # Act - removing again should return 404
    del_again = client.delete(f"/activities/{encoded_activity}/participants", params={"email": unique_email})
    assert del_again.status_code == 404
