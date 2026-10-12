import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture
def client():
    """Arrange: provide a TestClient with a clean in-memory activity store for each test."""
    original_activities = {
        activity_name: {
            key: value[:] if isinstance(value, list) else value
            for key, value in details.items()
        }
        for activity_name, details in activities.items()
    }

    activities.clear()
    activities.update(original_activities)

    with TestClient(app) as test_client:
        yield test_client

    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_index(client):
    """Arrange: a browser requests the app root. Act: call the endpoint. Assert: redirect to the static homepage."""
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activities(client):
    """Arrange: the app has the preloaded activities. Act: request the activities list. Assert: the API returns the expected activity names."""
    response = client.get("/activities")

    assert response.status_code == 200
    assert set(response.json().keys()) == {
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Soccer Team",
        "Basketball Club",
        "Drama Club",
        "Art Workshop",
        "Math Olympiad",
        "Science Club",
    }


def test_signup_for_activity_adds_participant(client):
    """Arrange: choose a valid activity and a new email. Act: submit the signup request. Assert: the API succeeds and the participant is added."""
    email = "new.student@mergington.edu"

    response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Chess Club"
    assert email in activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    """Arrange: use an email already registered for the activity. Act: submit the signup request. Assert: the API rejects the duplicate with a 400 error."""
    email = "michael@mergington.edu"

    response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_signup_for_missing_activity_returns_404(client):
    """Arrange: pick an activity name that does not exist. Act: submit the request. Assert: the API returns a 404 error."""
    response = client.post("/activities/Unknown Activity/signup", params={"email": "student@mergington.edu"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_participant_removes_email(client):
    """Arrange: choose a participant that is already in the list. Act: delete the participant from the activity. Assert: the email is removed from the activity."""
    email = "michael@mergington.edu"

    response = client.delete(f"/activities/Chess Club/participants/{email}")

    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from Chess Club"
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_missing_participant_returns_404(client):
    """Arrange: select an email not present in the activity list. Act: call the delete route. Assert: the API returns a 404 error."""
    response = client.delete("/activities/Chess Club/participants/not.here@mergington.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in activity"
