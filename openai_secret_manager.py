import os
import json

SECRETS_FILE = "secrets.json"

def get_secret(key_name):
    with open(SECRETS_FILE) as f:
        secrets = json.load(f)
    return secrets[key_name]

def set_secret(key_name, key_value):
    if not os.path.exists(SECRETS_FILE):
        with open(SECRETS_FILE, "w") as f:
            f.write("{}")
    with open(SECRETS_FILE) as f:
        secrets = json.load(f)
    secrets[key_name] = key_value
    with open(SECRETS_FILE, "w") as f:
        json.dump(secrets, f)
