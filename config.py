import json

with open("config.json") as f:
    CONFIG = json.load(f)

with open("oauth_client_secret.json") as f:
    OAUTH_CLIENT_SECRET = json.load(f)
    
with open("db_secret.json") as f:
    DB_SECRETS = json.load(f)
