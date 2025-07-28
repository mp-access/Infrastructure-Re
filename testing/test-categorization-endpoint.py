from datetime import datetime

import requests
import json
from config import (
    BACKEND_URL, BACKEND_CLIENT_ID, SUPERVISOR_USERNAME, SUPERVISOR_PASSWORD,
    COURSE_SLUG, API_KEY, EXAMPLE_SLUG
)
from keycloak_utils import (get_user_token)

def call_categorization_endpoint(payload: dict):
    try:
        supervisor_token = get_user_token(SUPERVISOR_USERNAME, SUPERVISOR_PASSWORD, BACKEND_CLIENT_ID)
        print(f"Obtained Supervisor Token: {supervisor_token[:100]}...")

        register_participants_url = f"{BACKEND_URL}/courses/{COURSE_SLUG}/examples/{EXAMPLE_SLUG}/categorize"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {supervisor_token}",
            "X-API-Key": API_KEY
        }
        print(f"Before calling the endpoint: {datetime.now().isoformat()}")
        response = requests.post(register_participants_url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        print(f"After calling the endpoint: {datetime.now().isoformat()}")
        print(f"Categorization request successful! Status: {response.status_code}")
        print(f"Response body: {response.content}")

    except requests.exceptions.RequestException as e:
        print(f"\n!!! An HTTP request error occurred: {e}")
        if e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
    except Exception as e:
        print(f"\n!!! An unexpected error occurred: {e}")

if __name__ == "__main__":
    submissionIds = list(range(802, 912))
    payload = {"submissionIds": submissionIds} # add submissions that you have stored locally and that have an embedding.
    call_categorization_endpoint(payload)