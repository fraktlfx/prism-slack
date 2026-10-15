import json
import base64
import secrets
import threading
import webbrowser
import urllib.parse
from pathlib import Path

import requests
from flask import Flask, make_response, redirect, request, send_file, session

_LOGIN_ACTIVE = threading.Event()


class SlackLogin:
    auth_url = "https://slack.com/openid/connect/authorize"
    token_url = "https://slack.com/api/openid.connect.token"
    userinfo_url = "https://slack.com/api/openid.connect.userInfo"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.host = "127.0.0.1"
        self.port = 5646

        self.redirect_uri = f"https://{self.host}:{self.port}/callback"
        self.scopes = ["openid", "profile"]

        plugin_dir = Path(__file__).resolve().parents[3]
        self.banner_path = plugin_dir / "Resources" / "prism_slack_logo_banner.png"
        self.favicon_path = plugin_dir / "Resources" / "slack-icon.png"

        self.app = Flask(__name__)
        self.app.secret_key = secrets.token_urlsafe(32)

        self._done = threading.Event()
        self._result = None
        self._error = None
        self._opened = False
        self.state = None
        self.nonce = None

        self._routing()

    def login(self, timeout=300):
        if _LOGIN_ACTIVE.is_set():
            raise RuntimeError("Slack login already in progress")
        _LOGIN_ACTIVE.set()
        try:
            t = threading.Thread(target=self._serve, daemon=True)
            t.start()

            threading.Timer(1.0, self._open_browser_once).start()

            self._done.wait(timeout=timeout)
            if not self._done.is_set():
                raise TimeoutError("Slack login timed out")
            if self._error:
                raise RuntimeError(self._error)
            return self._result
        finally:
            _LOGIN_ACTIVE.clear()

    def _routing(self):
        app = self.app

        @app.get("/")
        def index():
            return redirect("/login")

        @app.get("/login")
        def login_route():
            self.state = secrets.token_urlsafe(16)
            self.nonce = secrets.token_urlsafe(16)
            session["oidc_state"] = self.state
            session["oidc_nonce"] = self.nonce

            params = {
                "response_type": "code",
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "scope": " ".join(self.scopes),
                "state": self.state,
                "nonce": self.nonce,
            }
            return redirect(f"{self.auth_url}?{urllib.parse.urlencode(params)}")

        @app.get("/callback")
        def callback():
            if request.args.get("error"):
                self._finish(None, f"Slack error: {request.args.get('error')}")
                return self._page("Auth error.", 400)

            if request.args.get("state") != session.get("oidc_state"):
                self._finish(None, "Invalid state")
                return self._page("Invalid state.", 400)

            code = request.args.get("code")
            if not code:
                self._finish(None, "Missing code")
                return self._page("Missing code.", 400)

            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            try:
                resp = requests.post(self.token_url, data=data, timeout=20)
                tok = resp.json()
                if not resp.ok or not tok.get("ok"):
                    self._finish(None, f"Token exchange failed: {tok}")
                    return self._page("Token exchange failed.", 400)
                access_token = tok.get("access_token")
                id_token = tok.get("id_token")
                if not access_token or not id_token:
                    self._finish(None, "Missing tokens")
                    return self._page("Token exchange failed.", 400)
            except Exception as e:
                self._finish(None, f"Token exchange failed: {e}")
                return self._page("Token exchange failed.", 400)

            try:
                payload = id_token.split(".")[1]
                padding = "=" * (-len(payload) % 4)
                claims = json.loads(
                    base64.urlsafe_b64decode((payload + padding).encode())
                )
                if claims.get("nonce") != session.get("oidc_nonce"):
                    self._finish(None, "Nonce mismatch")
                    return self._page("Nonce mismatch.", 400)
            except Exception:
                pass

            try:
                u = requests.get(
                    self.userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=20,
                )
                data = u.json()
                if not u.ok or data.get("ok") is not True:
                    self._finish(None, f"Userinfo request failed: {data}")
                    return self._page("Userinfo request failed.", 400)
                result = {
                    "id": data.get("sub"),
                    "name": data.get("name"),
                    "token": access_token,
                }
            except Exception as e:
                self._finish(None, f"Userinfo request failed: {e}")
                return self._page("Userinfo request failed.", 400)

            self._finish(result, None)
            return self._page(
                "Authentication successful! You can close this window.", 200
            )

        @app.get("/favicon.ico")
        def favicon():
            if self.favicon_path.exists():
                return send_file(str(self.favicon_path), mimetype="image/png")
            return ("", 204)

        @app.get("/banner.png")
        def banner():
            if self.banner_path.exists():
                return send_file(str(self.banner_path), mimetype="image/png")
            return ("", 404)

    def _open_browser_once(self):
        if self._opened:
            return
        self._opened = True
        webbrowser.open(f"https://{self.host}:{self.port}/")

    def _serve(self):
        self.app.run(
            host=self.host,
            port=self.port,
            debug=False,
            use_reloader=False,
            ssl_context="adhoc",
        )

    def _finish(self, result, error):
        self._result = result
        self._error = error
        self._done.set()
        try:
            func = request.environ.get("werkzeug.server.shutdown")
            if func:
                threading.Timer(0.3, func).start()
        except Exception:
            pass

    @staticmethod
    def _page(message, status=200):
        html = f"""
        <html>
        <head><title>Prism/Slack Login</title></head>
        <body style="background:#1A1818;color:#DBB071;text-align:center;
                    font-family:Segoe UI, Arial; padding:2rem;">
            <img src="/banner.png" alt="Prism Slack Logo"
                style="width:300px; margin-bottom:20px;" />
            <h2>{message}</h2>
        </body>
        </html>
        """
        return make_response(html, status)
