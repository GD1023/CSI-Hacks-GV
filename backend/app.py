import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client

from model import get_bot

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

app = Flask(__name__)
CORS(app)


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
    app.run(port=5000, debug=True)
