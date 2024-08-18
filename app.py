import requests
from flask import Flask, render_template, session, abort, redirect, request, jsonify
from flask_caching import Cache
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import cachecontrol
import google.auth.transport.requests

import functools
import pathlib
import os

import database
import config
import key

db = database.Database()

app = Flask(__name__)
app.secret_key = config.OAUTH_CLIENT_SECRET["web"]["client_secret"]
key.read_secret_key(app)

cache = Cache(app, config={"CACHE_TYPE": "simple"})

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "0" if config.CONFIG["production"] else "1"  # allow http traffic for dev

GOOGLE_CLIENT_ID = config.OAUTH_CLIENT_SECRET["web"]["client_id"]

client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "oauth_client_secret.json")
flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=[
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ],
    redirect_uri=f"{config.CONFIG['domain']}/callback"
)


# OAuth2 endpoints
# Code from https://www.youtube.com/watch?v=n4e3Cy2Tq3Q
def login_required(function):
    """
    Decorator to check if the user is logged in, and if not, return a 401 error.
    """
    
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return redirect("/login")
        else:
            return function(*args, **kwargs)
    
    return wrapper


@app.route("/login")
def login():
    # If the user is already logged in, redirect them to the dashboard
    if "google_id" in session:
        return redirect("/dashboard")
    
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)
    
    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!
    
    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)
    
    id_info = id_token.verify_oauth2_token(
        id_token=credentials.id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
    
    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")
    
    return redirect("/app")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/app")
@login_required
def dashboard():
    if not db.user_exists(session["google_id"]):
        db.add_user(session["google_id"], session["email"])
    
    return render_template("app.html")


@app.route("/api/notes")
@login_required
def get_notes():
    return jsonify(db.get_notes(session["google_id"]))


@app.route("/")
def hello_world():
    return render_template("index.html")


if __name__ == "__main__":
    app.run()
