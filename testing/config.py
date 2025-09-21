from os import environ

environment = "staging"

if environment == "local":
    # --- Keycloak Configuration ---
    KEYCLOAK_HOST = "http://localhost:8080"
    KEYCLOAK_REALM = "access"
    KEYCLOAK_ADMIN_CLI_CLIENT_ID = "admin-cli"
    KEYCLOAK_ADMIN_USERNAME = "admin"
    KEYCLOAK_ADMIN_PASSWORD = "admin"

    # --- Keycloak API Endpoints ---
    KEYCLOAK_TOKEN_ENDPOINT = f"{KEYCLOAK_HOST}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
    KEYCLOAK_ADMIN_TOKEN_ENDPOINT = f"{KEYCLOAK_HOST}/realms/master/protocol/openid-connect/token"
    KEYCLOAK_USERS_API = f"{KEYCLOAK_HOST}/admin/realms/{KEYCLOAK_REALM}/users"
    KEYCLOAK_CLIENTS_API = f"{KEYCLOAK_HOST}/admin/realms/{KEYCLOAK_REALM}/clients"

    # --- Backend Configuration ---
    BACKEND_URL = "http://localhost:8081/api"
    BACKEND_CLIENT_ID = "access-client"
    API_KEY = "secret"

    # --- Test Data Parameters ---
    SUPERVISOR_USERNAME = "supervisor@uzh.ch"
    SUPERVISOR_PASSWORD = "password" # change if necessary

    COURSE_SLUG = "access-mock-course-2" # change if necessary
    EXAMPLE_SLUG = "shirt-size" # change if necessary
    TASK_FILE_ID = 9816 # look this up in the database (power-function is 51)

    NUM_STUDENTS_TO_CREATE = 5 # change if necessary
    STUDENT_BASE_PASSWORD = "password"
    SUBMISSION_MODE = "consecutive" # other mode is "consecutive"
    MAX_PARALLEL_SUBMISSIONS = 1

    # --- File Paths ---
    STUDENT_CREDENTIALS_FILE = "test-data/student_credentials.json"
    FIRST_SUBMISSIONS_FILE = "test-data/first-submissions-shirt-size-task.json"

if environment == "staging":

    # --- Keycloak Configuration ---
    KEYCLOAK_HOST = "https://access-staging.ifi.uzh.ch:8443/"
    KEYCLOAK_REALM = "access"
    KEYCLOAK_ADMIN_CLI_CLIENT_ID = "admin-cli"
    KEYCLOAK_ADMIN_USERNAME = "admin"
    KEYCLOAK_ADMIN_PASSWORD = "xxx"

    # --- Keycloak API Endpoints ---
    KEYCLOAK_TOKEN_ENDPOINT = f"{KEYCLOAK_HOST}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
    KEYCLOAK_ADMIN_TOKEN_ENDPOINT = f"{KEYCLOAK_HOST}/realms/master/protocol/openid-connect/token"
    KEYCLOAK_USERS_API = f"{KEYCLOAK_HOST}/admin/realms/{KEYCLOAK_REALM}/users"
    KEYCLOAK_CLIENTS_API = f"{KEYCLOAK_HOST}/admin/realms/{KEYCLOAK_REALM}/clients"

    # --- Backend Configuration ---
    BACKEND_URL = "https://access-staging.ifi.uzh.ch/api"
    BACKEND_CLIENT_ID = "access-client"
    API_KEY = "xxx"

    # --- Test Data Parameters ---
    SUPERVISOR_USERNAME = "supervisor@uzh.ch"
    SUPERVISOR_PASSWORD = "xxx"  # change if necessary

    COURSE_SLUG = "t-shirt-example-tests"  # change if necessary
    EXAMPLE_SLUG = "shirt-size"  # change if necessary
    TASK_FILE_ID = 6765  # look this up in the database (power-function is 51)

    NUM_STUDENTS_TO_CREATE = 200  # change if necessary
    STUDENT_BASE_PASSWORD = "die7haiZecohFahl5seedeeza5aeph"
    SUBMISSION_MODE = "consecutive"  # other mode is "consecutive"
    MAX_PARALLEL_SUBMISSIONS = 200

    # --- File Paths ---
    STUDENT_CREDENTIALS_FILE = "test-data/staging_student_credentials.json"
    FIRST_SUBMISSIONS_FILE = "test-data/first-submissions-shirt-size-task.json"
 