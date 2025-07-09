# keycloak_utils.py

import requests
import json
from config import (
    KEYCLOAK_HOST, KEYCLOAK_REALM, KEYCLOAK_ADMIN_CLI_CLIENT_ID,
    KEYCLOAK_ADMIN_USERNAME, KEYCLOAK_ADMIN_PASSWORD,
    KEYCLOAK_TOKEN_ENDPOINT, KEYCLOAK_ADMIN_TOKEN_ENDPOINT,
    KEYCLOAK_USERS_API, KEYCLOAK_CLIENTS_API
)

def get_keycloak_admin_token():
    payload = {
        "grant_type": "password",
        "client_id": KEYCLOAK_ADMIN_CLI_CLIENT_ID,
        "username": KEYCLOAK_ADMIN_USERNAME,
        "password": KEYCLOAK_ADMIN_PASSWORD
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    print(f"Attempting to get admin token from {KEYCLOAK_ADMIN_TOKEN_ENDPOINT}...")
    response = requests.post(KEYCLOAK_ADMIN_TOKEN_ENDPOINT, data=payload, headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]

def get_user_token(username, password, client_id):
    payload = {
        "grant_type": "password",
        "client_id": client_id,
        "username": username,
        "password": password
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    print(f"Attempting to get token for user '{username}' from {KEYCLOAK_TOKEN_ENDPOINT}...")
    response = requests.post(KEYCLOAK_TOKEN_ENDPOINT, data=payload, headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]

def create_keycloak_user(admin_token, username, email, password):
    user_data = {
        "enabled": True,
        "username": username,
        "email": email,
        "firstName": f"Student",
        "lastName": f"Test_{username.split('@')[0]}",
        "emailVerified": True,
        "credentials": [
            {
                "type": "password",
                "value": password,
                "temporary": False
            }
        ]
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}"
    }
    print(f"Creating user '{username}' in Keycloak...")
    response = requests.post(KEYCLOAK_USERS_API, data=json.dumps(user_data), headers=headers)
    try:
        response.raise_for_status()
        print(f"Successfully created user: {username}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            print(f"User '{username}' already exists. Skipping creation.")
        else:
            raise e
    return username

def get_keycloak_user_id(admin_token, username):
    headers = {
        "Authorization": f"Bearer {admin_token}"
    }
    print(f"Fetching user ID for '{username}'...")
    response = requests.get(f"{KEYCLOAK_USERS_API}?username={username}", headers=headers)
    response.raise_for_status()
    users = response.json()
    if not users:
        raise Exception(f"User '{username}' not found after creation attempt.")
    return users[0]['id']

def get_client_uuid(admin_token, client_id):
    headers = {
        "Authorization": f"Bearer {admin_token}"
    }
    print(f"Fetching UUID for client '{client_id}'...")
    response = requests.get(f"{KEYCLOAK_CLIENTS_API}?clientId={client_id}", headers=headers)
    response.raise_for_status()
    clients = response.json()
    if not clients:
        raise Exception(f"Client '{client_id}' not found.")
    return clients[0]['id']

def get_client_role_representation(admin_token, client_uuid, role_name):
    headers = {
        "Authorization": f"Bearer {admin_token}"
    }
    print(f"Fetching role '{role_name}' for client UUID '{client_uuid}'...")
    response = requests.get(f"{KEYCLOAK_CLIENTS_API}/{client_uuid}/roles/{role_name}", headers=headers)
    response.raise_for_status()
    return response.json()

def assign_client_role_to_user(admin_token, user_uuid, client_uuid, role_representation):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}"
    }
    print(f"Assigning role '{role_representation['name']}' to user UUID '{user_uuid}'...")
    response = requests.post(f"{KEYCLOAK_USERS_API}/{user_uuid}/role-mappings/clients/{client_uuid}",
                             data=json.dumps([role_representation]), headers=headers)
    response.raise_for_status()
    print(f"Successfully assigned role.")