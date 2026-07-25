import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client

from model import get_bot

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Comma-separated list of origins allowed to call this API. Defaults to the
# deployed frontend plus common local dev servers; override via the
# ALLOWED_ORIGINS env var (set in Render's dashboard) without touching code.
DEFAULT_ORIGINS = "https://highschoolcompass.vercel.app,http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",")
    if origin.strip()
]

app = Flask(__name__)
CORS(app, origins=ALLOWED_ORIGINS)

# Build the embeddings model and FAISS index once at process startup instead
# of on the first request, so a cold start (Render free tier spins the
# service down after inactivity) doesn't eat into that request's timeout.
get_bot()


@app.route("/advice", methods=["POST"])
def advice():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing bearer token"}), 401
    access_token = auth_header[len("Bearer "):].strip()

    # A fresh client per request, authenticated as the calling user's own
    # session -- RLS on public.profiles ("auth.uid() = id") then naturally
    # scopes the query to that user's own row without us needing to know
    # their id or use a service-role key.
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.postgrest.auth(access_token)

    result = client.table("profiles").select("*").maybe_single().execute()
    profile = result.data
    if not profile:
        return jsonify({"error": "Profile not found or session expired"}), 404

    advice_result = get_bot().chat(profile)
    return jsonify(advice_result)


if __name__ == "__main__":
    # Local dev only -- Render runs this via gunicorn instead (see render.yaml),
    # which is what actually binds to Render's $PORT in production.
    app.run(port=int(os.getenv("PORT", 5000)), debug=True)
