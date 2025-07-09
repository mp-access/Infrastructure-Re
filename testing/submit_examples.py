import requests
import json
import os
import random

from config import (
    BACKEND_URL, BACKEND_CLIENT_ID, COURSE_SLUG, EXAMPLE_SLUG,
    API_KEY, STUDENT_CREDENTIALS_FILE, FIRST_SUBMISSIONS_FILE, TASK_FILE_ID
)
from keycloak_utils import get_user_token, get_keycloak_user_id, get_keycloak_admin_token


def submit_solutions_workflow():
    print("--- Starting Solution Submission ---")
    try:
        # Load student credentials from the file
        if not os.path.exists(STUDENT_CREDENTIALS_FILE):
            raise FileNotFoundError(
                f"Student credentials file '{STUDENT_CREDENTIALS_FILE}' not found. "
                "Please run register_users.py first."
            )
        with open(STUDENT_CREDENTIALS_FILE, 'r') as f:
            student_credentials = json.load(f)
        print(f"Loaded {len(student_credentials)} student credentials from {STUDENT_CREDENTIALS_FILE}")

        # Load submission content data
        if not os.path.exists(FIRST_SUBMISSIONS_FILE):
            raise FileNotFoundError(
                f"Submission content file '{FIRST_SUBMISSIONS_FILE}' not found. "
                "Please ensure it's in the same directory."
            )
        with open(FIRST_SUBMISSIONS_FILE, 'r') as f:
            submission_contents_data = json.load(f)
        print(f"Loaded {len(submission_contents_data)} submission content entries from {FIRST_SUBMISSIONS_FILE}")

        # Ensure we have enough submission data for the number of students
        if len(submission_contents_data) < len(student_credentials):
            print(f"WARNING: Not enough submission content entries ({len(submission_contents_data)}) "
                  f"for all students ({len(student_credentials)}). Some students will be skipped.")
            # Adjust student_credentials to match available submission data
            student_credentials = student_credentials[:len(submission_contents_data)]

        # Generate a single random taskFileId for all submissions
        # Using a large range to simulate a Long in Kotlin
        common_task_file_id = random.randint(1000000000, 9999999999)
        print(f"Using common taskFileId: {common_task_file_id}")

        # Get admin token to lookup user UUIDs if needed (though backend uses authentication.name)
        # This is only for the print statement if you want to verify the UUID.
        admin_token = None
        try:
            admin_token = get_keycloak_admin_token()
        except Exception as e:
            print(f"Could not get admin token to lookup user UUIDs: {e}. Proceeding without UUID lookup.")

        # 4. Call Submission Endpoint for Each Student
        submission_url_template = f"{BACKEND_URL}/courses/{COURSE_SLUG}/examples/{EXAMPLE_SLUG}/submit"

        print(f"\n--- Processing Submissions for Each Student to Example '{EXAMPLE_SLUG}' ---")
        for i, student_info in enumerate(student_credentials):
            student_username = student_info["username"]
            student_password = student_info["password"]

            # Get the specific content for this student
            current_submission_content_entry = submission_contents_data[i]
            submission_code_content = current_submission_content_entry["submission"]["content"]

            # Get token for the specific student
            student_token = get_user_token(student_username, student_password, BACKEND_CLIENT_ID)
            print(f"Obtained token for {student_username}")

            # Determine userId for the DTO.
            # IMPORTANT NOTE: Your Kotlin backend's `evaluateExampleSubmission` method
            # sets `submission.userId = authentication.name`.
            # `authentication.name` from Keycloak JWT is typically the `preferred_username` claim,
            # which is usually the email (e.g., student1@uzh.ch), NOT the Keycloak UUID.
            # If you strictly need the UUID to be *sent* in the DTO, your backend Kotlin code
            # would need to be changed to retrieve it from the JWT claims or by querying Keycloak.
            # For now, we set it to the username/email as that's what the backend will use.
            # If you still want to send the UUID from here, you'd need to fetch it:
            # student_keycloak_uuid = get_keycloak_user_id(admin_token, student_username) if admin_token else None

            submission_dto = {
                "restricted": True,
                "userId": student_username,  # Backend will overwrite this with authentication.name (email)
                "command": "GRADE",
                "files": [
                    {
                        "taskFileId": TASK_FILE_ID,
                        "content": submission_code_content
                    }
                ]
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {student_token}",
                "X-API-Key": API_KEY
            }

            print(f"Submitting solution for '{student_username}' (Entry {i + 1})...")
            response = requests.post(submission_url_template, data=json.dumps(submission_dto), headers=headers)
            try:
                response.raise_for_status()  # Check for HTTP errors
                print(f"Submission for '{student_username}' successful! Status: {response.status_code}")
            except requests.exceptions.HTTPError as e:
                print(f"Submission for '{student_username}' FAILED: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                print(f"An error occurred during submission for '{student_username}': {e}")

    except requests.exceptions.RequestException as e:
        print(f"\n!!! An HTTP request error occurred: {e}")
        if e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
    except FileNotFoundError as e:
        print(f"\n!!! Error: {e}")
    except Exception as e:
        print(f"\n!!! An unexpected error occurred: {e}")

    print("\n--- Solution Submission Complete ---")


if __name__ == "__main__":
    submit_solutions_workflow()