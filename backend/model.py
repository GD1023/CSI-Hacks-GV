import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from supabase import create_client

load_dotenv()

API_KEY = os.getenv("API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Fields that are internal bookkeeping (storage paths, timestamps, the row id
# itself) rather than signal the counselor prompt should reason about.
_PROFILE_DROP_FIELDS = {"id", "updated_at", "transcript_link", "school_profile_link"}


def _competition_to_text(row):
    """Flatten one competitions row into a single string for embedding."""
    parts = [
        row.get("name"),
        row.get("category"),
        row.get("grade_levels"),
        row.get("team_or_solo"),
        row.get("description"),
    ]
    return " | ".join(str(p) for p in parts if p)


def clean_profile(profile: dict) -> dict:
    """Drop internal-only fields and empty values before showing the LLM a profile."""
    return {
        key: value
        for key, value in profile.items()
        if key not in _PROFILE_DROP_FIELDS and value not in (None, "", [])
    }


class ChatBot:
    def __init__(self):
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        try:
            response = supabase.table("competitions").select("*").execute()
            competitions = response.data or []
        except Exception as exc:
            # Most likely schema.sql hasn't been run against the live Supabase
            # project yet (the competitions table doesn't exist there). Don't
            # crash the whole bot over it -- just retrieve nothing until it does.
            print(f"Warning: could not load competitions table ({exc}). Retrieval will return no matches.")
            competitions = []

        self.embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.vectorstore = FAISS.from_texts(
            texts=[_competition_to_text(row) for row in competitions] or [""],
            embedding=self.embedding,
            metadatas=competitions or [{}],
        )
        self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=API_KEY)

    def chat(self, profile: dict) -> dict:
        """Run the counselor prompt for one student profile (a dict shaped like a
        public.profiles row -- see context_schema.json for an example) and return
        the model's answer parsed as a dict of the six advice sections.
        """
        profile = clean_profile(profile)
        profile_json = json.dumps(profile, indent=2)

        # Retrieval is scoped to the fields that actually predict a good
        # competition match -- searching on the whole profile blob would dilute
        # the signal with unrelated fields like GPA or travel constraints.
        retrieval_signal = " ".join(
            str(value)
            for value in (
                profile.get("interests"),
                profile.get("intended_majors"),
                profile.get("interest_areas"),
                profile.get("extracurriculars"),
                profile.get("competition_history"),
                profile.get("competition_team_preference"),
            )
            if value
        )
        docs = self.vectorstore.similarity_search(retrieval_signal or profile_json, k=7)
        context = "\n".join(doc.page_content for doc in docs)

        prompt = f'''
    You are a counselor with the responsibility of looking at a student's profile from the
    perspective of a college admission officer -- but keep in mind this is general peer-style
    guidance, not a professional or official evaluation, so avoid presenting anything as a
    guaranteed outcome.

    STUDENT APPLICATION
    {profile_json}

    RELEVANT SUPPORTING MATERIAL (retrieved based on this student's profile)
    {context}

    Analyze their application across these 4 aspects:
    1. Courses & rigor -- look at their current courses relative to their stated interests:
       how rigorous is their schedule, how well does it connect to their interest field, and
       what would a smart next-step study plan look like.
    2. Clubs & involvement -- look at their current clubs/school involvement and determine how
       well it signals depth of commitment and leadership potential relative to their intended
       major, rather than just breadth of participation.
    3. Competitions & awards -- using ONLY the competitions that actually appear in the
       RELEVANT SUPPORTING MATERIAL above, recommend which ones fit this student's interests,
       time availability, and team/solo preference. Never invent a competition that wasn't
       retrieved -- if nothing retrieved fits well, say so honestly.
    4. Testing & college prep -- look at their test scores (or lack of them) and remaining
       graduation requirements relative to their college list/preferences, and flag what's
       still missing from their profile that would sharpen this advice.

    Return your analysis as a JSON object with exactly these keys, each a short (2-4 sentence)
    recommendation string: testing, clubs, competitions, courses, career, college_prep.
    If part of the student's profile is missing, don't guess -- either skip referencing it or
    gently note that adding it would help.
    '''
        response = self.llm.invoke(prompt)
        raw = response.content.strip()

        # The model sometimes wraps the JSON in a markdown code fence and/or a
        # sentence of preamble despite being asked for raw JSON -- pull out
        # just the {...} block before parsing.
        start, end = raw.find("{"), raw.rfind("}")
        candidate = raw[start:end + 1] if start != -1 and end != -1 else raw

        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return {"raw": raw}


_bot = None


def get_bot() -> ChatBot:
    """Lazily build the ChatBot (and its FAISS index) once and reuse it across requests."""
    global _bot
    if _bot is None:
        _bot = ChatBot()
    return _bot


if __name__ == "__main__":
    # Local smoke test: `python model.py` runs the bot against the sample
    # profile in context_schema.json instead of a real Supabase row.
    with open("context_schema.json", "r", encoding="utf-8") as f:
        sample_profile = json.load(f)
    print(json.dumps(get_bot().chat(sample_profile), indent=2))
