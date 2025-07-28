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
API_KEY = "1234"

# --- Test Data Parameters ---
SUPERVISOR_USERNAME = "supervisor@uzh.ch"
SUPERVISOR_PASSWORD = "supervisor" # change if necessary

COURSE_SLUG = "access-mock-course" # change if necessary
EXAMPLE_SLUG = "circle-square-rect" # change if necessary
TASK_FILE_ID = 59 # look this up in the database (power-function is 51)

NUM_STUDENTS_TO_CREATE = 400 # change if necessary
STUDENT_BASE_PASSWORD = "student"
SUBMISSION_MODE = "parallel" # other mode is "consecutive"
MAX_PARALLEL_SUBMISSIONS = 1

# --- File Paths ---
STUDENT_CREDENTIALS_FILE = "test-data/student_credentials.json"
FIRST_SUBMISSIONS_FILE = "test-data/first-submissions-arithmetic-expression-task.json"