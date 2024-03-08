from dotenv import load_dotenv
from datetime import datetime, timedelta
from flask import Flask, redirect, request, jsonify, session
import os
import requests
import urllib.parse

app = Flask(__name__)
load_dotenv()

class SpotifyAPI:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_url = "https://accounts.spotify.com/authorize"
        self.token_url = "https://accounts.spotify.com/api/token"
        self.api_base_url = "https://api.spotify.com/v1"

    def login(self):
        scope = "user-read-private user-read-email"
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": scope,
            "redirect_uri": self.redirect_uri,
            "show_dialog": True
        }
        auth_url = f"{self.auth_url}?{urllib.parse.urlencode(params)}"
        return redirect(auth_url)

    def get_access_token(self, code):
        req_body = {
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(self.token_url, data=req_body)
        token_info = response.json()
        return token_info

    def refresh_token(self, refresh_token):
        req_body = {
            "grant_type": "refresh_token",
            "refesh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(self.token_url, data=req_body)
        new_token_info = response.json()
        return new_token_info

    def get_user_playlists(self, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.api_base_url + "/me/playlists", headers=headers)
        if response.status_code == 200:
            playlists_data = response.json()
            playlists = playlists_data.get("items", [])
            return playlists
        else:
            return None

class SpotifyApp:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.spotify_api = SpotifyAPI(client_id, client_secret, redirect_uri)
        self.playlists = None

    def login(self):
        return self.spotify_api.login()

    def callback(self, code):
        token_info = self.spotify_api.get_access_token(code)
        session["access_token"] = token_info["access_token"]
        session["refresh_token"] = token_info["refresh_token"]
        session["expires_at"] = datetime.now().timestamp() + token_info["expires_in"]
        return redirect("/playlists")

    def refresh_token(self):
        new_token_info = self.spotify_api.refresh_token(session["refresh_token"])
        session["access_token"] = new_token_info["access_token"]
        session["expires_at"] = datetime.now().timestamp() + new_token_info["expires_in"]
        self.playlists = None
        return redirect("/playlists")

    def get_playlists(self):
        if "access_token" not in session:
            return self.spotify_api.login()
        if datetime.now().timestamp() > session["expires_at"]:
            return self.refresh_token()
        playlists = self.spotify_api.get_user_playlists(session["access_token"])
        if playlists:
            self.playlists = playlists
            print(self.playlists)
            return jsonify(playlists)
        else:
            return jsonify({"error": "Failed to fetch playlists"})
    
@app.route("/")
def index():
    return "Welcome to my Spotify app <a href='/login'>Login with Spotify</a>"

@app.route("/login")
def login():
    return spotify_app.login()

@app.route("/callback")
def callback():
    code = request.args.get("code")
    return spotify_app.callback(code)

@app.route("/refresh-token")
def refresh_token():
    return spotify_app.refresh_token()

@app.route("/playlists")
def get_playlists():
    return spotify_app.get_playlists()

# class ConsoleManager:
#     @staticmethod
#     def display_playlists(playlists):
#         if playlists:
#             print("Listas de reproducción disponibles:")
#             for index, playlist in enumerate(playlists, start=1):
#                 print(f"{index}. {playlist['name']}")
#         else:
#             print("¡Error al obtener las listas de reproducción de Spotify!")


if __name__ == "__main__":
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET_ID")
    app.secret_key = os.getenv("APP_SECRET_ID")
    redirect_uri = "http://localhost:5000/callback"
    spotify_app = SpotifyApp(client_id, client_secret, redirect_uri)
    print("holaaaaaa",spotify_app.playlists)
    # ConsoleManager.display_playlists(spotify_app.playlists)
    
    app.run(host="0.0.0.0", debug=True)
