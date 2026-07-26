import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
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

        self.texts = [_competition_to_text(row) for row in competitions]

        # TF-IDF + cosine similarity instead of neural embeddings + FAISS --
        # that stack (torch/sentence-transformers/faiss) needs close to a GB
        # of RAM just to load, which doesn't fit Render's 512MB free tier.
        # At ~300 short competition blurbs, TF-IDF is plenty to match a
        # student profile to relevant competitions and costs a few MB.
        if self.texts:
            self.vectorizer = TfidfVectorizer(stop_words="english")
            self.matrix = self.vectorizer.fit_transform(self.texts)
        else:
            self.vectorizer = None
            self.matrix = None

        # temperature=0 was making every response read like a restatement of
        # the input profile; a bit of headroom gets more judgment-driven phrasing.
        self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.4, api_key=API_KEY)

    def _retrieve(self, query: str, k: int = 7):
        """Return up to k competition texts most similar to query, best first."""
        if not query or self.vectorizer is None:
            return []
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix)[0]
        ranked = scores.argsort()[::-1][:k]
        return [self.texts[i] for i in ranked if scores[i] > 0]

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
        matches = self._retrieve(retrieval_signal or profile_json, k=7)
        context = "\n".join(matches)

        prompt = f'''
    You are a counselor with the responsibility of looking at a student's profile from the
    perspective of a college admission officer -- but keep in mind this is general peer-style
    guidance, not a professional or official evaluation, so avoid presenting anything as a
    guaranteed outcome.

    CRITICAL RULE: the student already knows their own profile -- do not spend sentences
    restating it back to them (e.g. "You are taking AP Calc and Honors Physics" is not advice,
    it's an echo). Every sentence must add something they don't already have: a specific
    judgment (rigorous/thin/misaligned and why), a named next step (a specific course,
    competition, activity type, or question to ask a counselor), or a tradeoff they haven't
    considered. If a section would otherwise just summarize their data, cut it and go straight
    to the recommendation instead.

    STUDENT APPLICATION
    {profile_json}

    RELEVANT SUPPORTING MATERIAL (retrieved based on this student's profile)
    {context}

    Analyze their application across these 6 aspects:
    1. Courses & rigor -- judge how rigorous their schedule actually is relative to their
       stated interests (not just listing it), and name a specific next-step course or two.
    2. Clubs & involvement -- judge whether their school clubs signal real depth/leadership
       for their intended major or just breadth, and say what would move them from member to
       standout (a specific role, project, or initiative).
    3. Extracurriculars -- using work experience, volunteering, and time commitments outside
       school, judge whether their outside-of-school activities reinforce or dilute their
       intended-major narrative, and flag any time-balance risk given their stated commitments.
    4. Competitions & awards -- using ONLY the competitions that actually appear in the
       RELEVANT SUPPORTING MATERIAL above, recommend which ones fit this student's interests,
       time availability, and team/solo preference, and say why over the alternatives retrieved.
       Do not name ANY competition, organization, or program that is not verbatim in the
       RELEVANT SUPPORTING MATERIAL, even as a "you could look into" suggestion -- you do not
       know it actually exists or fits their constraints. If the RELEVANT SUPPORTING MATERIAL
       is empty or nothing in it fits, say plainly that the catalog didn't have a match and
       suggest they ask their counselor for options in their interest area, with no invented
       names.
    5. Testing & college prep -- judge their test scores and remaining graduation requirements
       against their college list/preferences specifically (not test scores in the abstract),
       and name the single highest-leverage gap to close next.
    6. Career fit -- judge how well their intended majors, interest areas, and working style
       actually cohere into a defensible career direction, and name one concrete way to test
       that direction before committing further (e.g. a specific kind of internship, project,
       or person to talk to).

    Return your analysis as a JSON object with exactly these keys, each a short (2-4 sentence)
    recommendation string: testing, clubs, extracurriculars, competitions, courses, career,
    college_prep. If part of the student's profile is missing, don't guess -- either skip
    referencing it or gently note that adding it would help.
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
