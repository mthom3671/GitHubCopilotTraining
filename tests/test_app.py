from uuid import uuid4

from fastapi.testclient import TestClient

from src.app import app


client = TestClient(app)


def unique_email() -> str:
    return f"student-{uuid4().hex[:8]}@mergington.edu"


def test_root_redirects_to_static_index() -> None:
    response = client.get("/", follow_redirects=False)

    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_expected_data() -> None:
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, dict)
    assert "Chess Club" in payload
    assert "participants" in payload["Chess Club"]


def test_signup_successful_adds_participant() -> None:
    email = unique_email()

    response = client.post(f"/activities/Chess Club/signup?email={email}")

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Chess Club"

    activities_response = client.get("/activities")
    participants = activities_response.json()["Chess Club"]["participants"]
    assert email in participants


def test_signup_unknown_activity_returns_404() -> None:
    email = unique_email()

    response = client.post(f"/activities/Unknown Club/signup?email={email}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_email_returns_400() -> None:
    email = unique_email()
    first_signup = client.post(f"/activities/Drama Club/signup?email={email}")
    assert first_signup.status_code == 200

    duplicate_signup = client.post(f"/activities/Drama Club/signup?email={email}")

    assert duplicate_signup.status_code == 400
    assert duplicate_signup.json()["detail"] == "Student already signed up"


def test_unregister_successful_removes_participant() -> None:
    email = unique_email()
    signup = client.post(f"/activities/Art Club/signup?email={email}")
    assert signup.status_code == 200

    unregister = client.delete(f"/activities/Art Club/participants?email={email}")

    assert unregister.status_code == 200
    assert unregister.json()["message"] == f"Removed {email} from Art Club"

    activities_response = client.get("/activities")
    participants = activities_response.json()["Art Club"]["participants"]
    assert email not in participants


def test_unregister_unknown_activity_returns_404() -> None:
    email = unique_email()

    response = client.delete(f"/activities/Unknown Club/participants?email={email}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_missing_participant_returns_404() -> None:
    email = unique_email()

    response = client.delete(f"/activities/Science Club/participants?email={email}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in this activity"