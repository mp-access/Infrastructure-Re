from datetime import datetime

import requests
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import (
    BACKEND_URL, BACKEND_CLIENT_ID, COURSE_SLUG, EXAMPLE_SLUG,
    API_KEY, STUDENT_CREDENTIALS_FILE, FIRST_SUBMISSIONS_FILE, TASK_FILE_ID,
    SUBMISSION_MODE, MAX_PARALLEL_SUBMISSIONS
)
from keycloak_utils import get_user_token # Assuming this function is blocking

def submit_example(student_info, submission_code_content, submission_url_template, api_key, backend_client_id):
    student_username = student_info["username"]
    student_password = student_info["password"]

    try:
        student_token = get_user_token(student_username, student_password, backend_client_id)

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
            "Authorization": f"Bearer {student_token}"
            # "X-API-Key": api_key
        }

        print(f"Submitting solution for '{student_username}' at time {datetime.now()}")
        response = requests.post(submission_url_template, data=json.dumps(submission_dto), headers=headers)
        response.raise_for_status()
        print(f"Submission for '{student_username}' successful! Status: {response.status_code}")
    except requests.exceptions.HTTPError as e:
        print(f"Submission for '{student_username}' FAILED: {e.response.status_code} - {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"An HTTP request error occurred for '{student_username}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred during submission for '{student_username}': {e}")

def submit_solutions_workflow(mode="parallel", max_parallel_workers=10):

    if not mode in ("consecutive", "parallel"):
        raise ValueError("Invalid mode supplied. Must be 'parallel' or 'consecutive'")

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

        print(f"\n--- Processing Submissions for Each Student to Example '{EXAMPLE_SLUG}' ({mode.upper()} mode) ---")

        if mode == "consecutive":
            for i, student_info in enumerate(student_credentials):
                current_submission_content_entry = submission_contents_data[i]
                submission_code_content = current_submission_content_entry["submission"]["content"]
                submit_example(student_info, submission_code_content, submission_url_template, API_KEY, BACKEND_CLIENT_ID)
                print(f"Processed {i + 1}/{len(student_credentials)} submissions.")
        elif mode == "parallel":
            with ThreadPoolExecutor(max_workers=max_parallel_workers) as executor:
                future_per_student = {
                    executor.submit(
                        submit_example,
                        student_credentials[i],
                        submission_contents_data[i]["submission"]["content"],
                        submission_url_template,
                        # API_KEY,
                        BACKEND_CLIENT_ID
                    ): student_credentials[i]["username"]
                    for i in range(len(student_credentials))
                }

                for i, future in enumerate(as_completed(future_per_student)):
                    student_username = future_per_student[future]
                    try:
                        future.result()
                    except Exception as exc:
                        print(f"'{student_username}' generated an exception: {exc}")
                    print(f"Completed {i + 1}/{len(student_credentials)} parallel submissions.")

    except FileNotFoundError as e:
        print(f"\nError: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

    print("\n--- Solution Submission Complete ---")

if __name__ == "__main__":
    submit_solutions_workflow(mode=SUBMISSION_MODE, max_parallel_workers=MAX_PARALLEL_SUBMISSIONS)