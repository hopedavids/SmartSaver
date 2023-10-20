from flask import url_for, redirect
from flask_dance.contrib.google import make_google_blueprint, google


google = make_google_blueprint(scope=["profile", "email"])


@google.route("/run")
def index():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v2/userinfo")
    assert resp.ok, resp.text
    email = resp.json()["email"]
    # You can now use the email to authenticate the user in your system
    return f"Logged in as {email}"

@google.route("/login/google")
def loggin():
    if not google.authorized:
        return redirect(url_for("google.loggin"))
    return redirect(url_for("index"))

@google.route("/logout")
def logout():
    google = blueprint.backend
    token = google_blueprint.token["access_token"]
    resp = google.post(
        "/o/oauth2/revoke",
        params={"token": token},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.ok, resp.text
    return redirect(url_for("index"))
