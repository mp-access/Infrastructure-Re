import requests
import json
import os
import random

from config import (
    BACKEND_URL, BACKEND_CLIENT_ID, COURSE_SLUG, EXAMPLE_SLUG,
    API_KEY, STUDENT_CREDENTIALS_FILE, FIRST_SUBMISSIONS_FILE, TASK_FILE_ID
)
from keycloak_utils import get_user_token, get_keycloak_admin_token

def submit_solutions_workflow():
    print("--- Starting Solution Submission ---")
    try:
        if not os.path.exists(STUDENT_CREDENTIALS_FILE):
            raise FileNotFoundError(
                f"Student credentials file '{STUDENT_CREDENTIALS_FILE}' not found. "
                "Please run register_users.py first."
            )

        with open(STUDENT_CREDENTIALS_FILE, 'r') as f:
            student_credentials = json.load(f)
        print(f"Loaded {len(student_credentials)} student credentials from {STUDENT_CREDENTIALS_FILE}")

        if not os.path.exists(FIRST_SUBMISSIONS_FILE):
            raise FileNotFoundError(
                f"Submission content file '{FIRST_SUBMISSIONS_FILE}' not found. "
                "Please ensure it's in the same directory."
            )
        with open(FIRST_SUBMISSIONS_FILE, 'r') as f:
            submission_contents_data = json.load(f)
        print(f"Loaded {len(submission_contents_data)} submission content entries from {FIRST_SUBMISSIONS_FILE}")

        if len(submission_contents_data) < len(student_credentials):
            print(f"WARNING: Not enough submission content entries ({len(submission_contents_data)}) "
                  f"for all students ({len(student_credentials)}). Some students will be skipped.")
            student_credentials = student_credentials[:len(submission_contents_data)]

        submission_url_template = f"{BACKEND_URL}/courses/{COURSE_SLUG}/examples/{EXAMPLE_SLUG}/submit"

        print(f"\n--- Processing Submissions for Each Student to Example '{EXAMPLE_SLUG}' ---")
        for i, student_info in enumerate(student_credentials):
            student_username = student_info["username"]
            student_password = student_info["password"]

            current_submission_content_entry = submission_contents_data[i]
            submission_code_content = current_submission_content_entry["submission"]["content"]

            student_token = get_user_token(student_username, student_password, BACKEND_CLIENT_ID)
            print(f"Obtained token for {student_username}")

            submission_dto = {
                "restricted": True,
                "userId": student_username,
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
        print(f"\nAn HTTP request error occurred: {e}")
        if e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
    except FileNotFoundError as e:
        print(f"\nError: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

    print("\n--- Solution Submission Complete ---")