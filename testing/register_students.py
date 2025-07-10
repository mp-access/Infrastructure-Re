import requests
import json
from config import (
    BACKEND_URL, BACKEND_CLIENT_ID, SUPERVISOR_USERNAME, SUPERVISOR_PASSWORD,
    COURSE_SLUG, NUM_STUDENTS_TO_CREATE, STUDENT_BASE_PASSWORD,
    API_KEY, STUDENT_CREDENTIALS_FILE
)
from keycloak_utils import (
    get_keycloak_admin_token, get_user_token, create_keycloak_user,
    get_keycloak_user_id, get_client_uuid, create_or_get_client_role,
    assign_client_role_to_user, assign_master_realm_admin_roles
)

def register_students_workflow():
    print("--- Starting User Registration and Course Enrollment ---")
    try:
        admin_token = get_keycloak_admin_token()
        print(f"Obtained Keycloak Admin Token: {admin_token[:100]}...")

        assign_master_realm_admin_roles(admin_token)

        supervisor_token = get_user_token(SUPERVISOR_USERNAME, SUPERVISOR_PASSWORD, BACKEND_CLIENT_ID)
        print(f"Obtained Supervisor Token: {supervisor_token[:100]}...")

        backend_client_uuid = get_client_uuid(admin_token, BACKEND_CLIENT_ID)
        print(f"Backend client UUID: {backend_client_uuid}")

        course_role_representation = create_or_get_client_role(admin_token, backend_client_uuid, COURSE_SLUG)
        print(f"Obtained client role representation for '{COURSE_SLUG}'.")

        student_registration_ids = []
        student_credentials = []

        print(f"\n--- Creating {NUM_STUDENTS_TO_CREATE} Students in Keycloak ---")
        for i in range(NUM_STUDENTS_TO_CREATE):
            username = f"student{i + 1}@uzh.ch"
            password = STUDENT_BASE_PASSWORD

            create_keycloak_user(admin_token, username, username, password)

            user_uuid = get_keycloak_user_id(admin_token, username)

            assign_client_role_to_user(admin_token, user_uuid, backend_client_uuid, course_role_representation)

            student_credentials.append({"username": username, "password": password})
            student_registration_ids.append(username)

        with open(STUDENT_CREDENTIALS_FILE, 'w') as f:
            json.dump(student_credentials, f, indent=4)
        print(f"\nSaved student credentials to {STUDENT_CREDENTIALS_FILE}")

        # add students to course via the backend endpoint (required such that the participant count is shown correctly)
        register_participants_url = f"{BACKEND_URL}/courses/{COURSE_SLUG}/participants"
        payload_registration_ids = student_registration_ids
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {supervisor_token}",
            "X-API-Key": API_KEY
        }
        print(f"\n--- Registering {len(payload_registration_ids)} Participants to Course '{COURSE_SLUG}' ---")
        response = requests.post(register_participants_url, data=json.dumps(payload_registration_ids), headers=headers)
        response.raise_for_status()
        print(f"Participants registered successfully! Status: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"\n!!! An HTTP request error occurred: {e}")
        if e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
    except Exception as e:
        print(f"\n!!! An unexpected error occurred: {e}")

    print("\n--- User Registration and Course Enrollment Complete ---")