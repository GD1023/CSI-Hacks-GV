import os
import re
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


EXTRA_CONTEXT= ''' 
# Comprehensive Guide to U.S. College Admissions

## A Reference Article for AI Retrieval-Augmented Generation (RAG) Systems

# Introduction

The college admissions process in the United States is holistic, meaning that universities evaluate applicants based on far more than just grades or standardized test scores. Admissions officers seek students who demonstrate academic excellence, intellectual curiosity, leadership, initiative, impact within their communities, and the potential to contribute meaningfully to campus life.

While every institution evaluates applicants differently, nearly all selective colleges consider a combination of:

* Academic Performance
* Course Rigor
* Grade Point Average (GPA)
* Standardized Testing (SAT/ACT)
* Advanced Coursework (AP, IB, Dual Enrollment, Honors)
* Extracurricular Activities
* Leadership
* Research and Projects
* Community Service
* Awards and Competitions
* Essays
* Letters of Recommendation
* Demonstrated Interest (at some schools)

Highly selective universities (such as Stanford, MIT, Harvard, Princeton, Yale, Columbia, Duke, Carnegie Mellon, Caltech, and many top public universities) use holistic admissions, meaning no single factor guarantees admission.

---

# Section 1: Academic Performance

Academic performance is the single most important component of nearly every college application.

Admissions officers primarily examine:

* GPA
* Transcript
* Course rigor
* Grade trends
* Performance in core academic subjects

Rather than asking "What was the student's GPA?", admissions officers often ask:

> "Did this student maximize the opportunities available at their high school?"

A student with a 3.95 GPA while taking the hardest courses available is often viewed more favorably than a student with a 4.00 GPA who intentionally avoided challenging coursework.

---

# Section 2: Understanding GPA

## Weighted GPA

Weighted GPA gives additional value to advanced classes.

Typical weighting:

Regular Course

* A = 4.0

Honors

* A = 4.5

AP / IB / Dual Enrollment

* A = 5.0

Schools calculate weighted GPA differently.

---

## Unweighted GPA

Measures academic performance regardless of course difficulty.

Typical scale:

A = 4.0

B = 3.0

C = 2.0

D = 1.0

F = 0

Many colleges recalculate GPA using only core academic classes.

---

## Grade Trends

Admissions officers like upward trends.

Example:

Freshman Year

* Mostly B's

Sophomore

* Mostly A's

Junior

* All A's

This often reflects growth and maturity.

Conversely, declining grades during junior year may raise concerns because junior-year performance is often considered the strongest predictor of college success.

---

# Section 3: Course Rigor

Course rigor measures how academically challenging a student's schedule is.

Selective universities strongly prefer students who pursue the most rigorous coursework reasonably available at their high school.

Examples include:

* AP Courses
* IB Courses
* Honors Courses
* Cambridge A-Level Courses
* Dual Enrollment
* College Courses

Admissions officers evaluate rigor relative to the opportunities available at the student's school.

Example:

Student A

* 14 AP classes available
* Takes 12

Student B

* School offers only 4 APs
* Takes all 4

Both demonstrate exceptional rigor.

Students are not penalized for lacking opportunities their school does not provide.

---

## Core Academic Subjects

Admissions officers particularly focus on:

English

Mathematics

Science

Social Studies

Foreign Language

Strong applicants generally pursue four years of each core subject whenever possible.

---

## Mathematics Expectations

Engineering, Computer Science, Physics, Mathematics, Economics, and quantitative majors benefit from completing:

* Algebra I
* Geometry
* Algebra II
* Precalculus
* Calculus AB
* Calculus BC
* Multivariable Calculus (if available)
* Linear Algebra (optional but beneficial)
* Differential Equations (rare but impressive)

---

## Science Expectations

Competitive STEM applicants often complete:

Biology

Chemistry

Physics

AP Biology

AP Chemistry

AP Physics 1

AP Physics C

Environmental Science (optional)

---

## Humanities Expectations

Competitive humanities applicants often pursue:

AP Literature

AP Language

AP U.S. History

AP World History

AP Government

AP Economics

Advanced writing-intensive coursework.

---

# Section 4: Advanced Placement (AP) Courses

AP courses demonstrate college-level academic readiness.

Benefits include:

* Increased course rigor
* Potential college credit
* Stronger admissions profile
* Preparation for university coursework

Examples:

AP Calculus BC

AP Physics C

AP Chemistry

AP Biology

AP Computer Science A

AP Statistics

AP Economics

AP Government

AP Psychology

AP English Language

AP English Literature

Admissions officers generally care more about taking challenging AP courses and performing well in them than about accumulating a very high number of AP classes without strong grades.

---

# Section 5: AP Exams

AP exams are scored:

1

2

3

4

5

Typical interpretation:

5 = Extremely well qualified

4 = Well qualified

3 = Qualified

Selective colleges generally prefer 4s and 5s, though admissions decisions are rarely based solely on AP scores.

AP exam scores primarily:

* Validate classroom performance
* Demonstrate mastery
* Potentially earn college credit

Many colleges allow students to choose whether to report AP scores.

---

# Section 6: SAT and ACT

## SAT

The SAT measures:

Reading

Writing

Mathematics

Current maximum score:

1600

Approximate competitive ranges:

Regional Universities

* 1050–1250

Strong Public Universities

* 1250–1450

Top Public Universities

* 1400–1550

Highly Selective Universities

* 1500–1600

---

## ACT

Composite score:

1–36

Competitive ranges:

Regional Universities

* 22–28

Competitive Schools

* 28–32

Top Universities

* 33–36

---

## Test-Optional Policies

Many universities are test-optional, meaning students may choose whether to submit SAT or ACT scores.

However:

Strong SAT or ACT scores can strengthen an application, particularly when they align with or exceed the institution's middle 50% admitted student range.

Applicants should research each college's current testing policy, as these policies change over time.

---

# Section 7: Extracurricular Activities

Extracurricular activities demonstrate who a student is beyond academics.

Admissions officers evaluate:

Leadership

Initiative

Impact

Commitment

Depth

Consistency

Rather than the total number of activities, colleges value sustained involvement and meaningful contributions.

Examples:

Robotics

Research

Sports

Music

Dance

Theater

Programming

Student Government

Journalism

Debate

Business Clubs

Nonprofits

Volunteer Organizations

Employment

Family Responsibilities

Independent Projects

---

## Leadership

Leadership can include:

Club President

Team Captain

Founder

Research Team Lead

Mentor

Tutor

Event Organizer

Leadership should ideally show measurable outcomes.

Examples:

Raised $25,000

Organized conference for 400 students

Managed 40 volunteers

Expanded nonprofit to 10 chapters

Published research

Built software used by thousands

---

## Impact

Impact matters more than titles.

Examples:

Weak:

Vice President of Club

Strong:

Developed curriculum reaching 5,000 students.

Built software used across multiple schools.

Raised significant funding.

Started a statewide initiative.

Conducted original research.

Admissions officers frequently prioritize demonstrated outcomes over formal leadership positions.

---

# Section 8: Research

Research has become increasingly common among applicants to top universities.

Research opportunities include:

University laboratories

Independent research

Science fairs

Research mentorship programs

Published papers

Conference presentations

Research is especially valuable when students can clearly explain:

The problem

Their methodology

Their contribution

The results

The broader significance

---

# Section 9: Community Involvement

Community service demonstrates empathy, responsibility, and civic engagement.

Examples:

Food banks

Tutoring

Hospital volunteering

Environmental cleanups

Animal shelters

Fundraising

Local government

Youth mentorship

Religious organizations

Community organizations

Quality is generally valued more than the total number of volunteer hours.

Long-term involvement with measurable impact is especially meaningful.

---

# Section 10: Personal Projects

Independent projects showcase curiosity and initiative.

Examples:

Developing software

Publishing research

Creating educational platforms

Writing books

Launching businesses

Building hardware

Creating AI models

Engineering prototypes

Podcasts

YouTube educational channels

Open-source contributions

Projects can become central themes within college essays and interviews.

---

# Section 11: Essays

Essays allow admissions officers to understand:

Character

Motivation

Values

Growth

Reflection

Authenticity

Strong essays typically emphasize personal growth rather than listing achievements.

Common themes include:

Overcoming challenges

Intellectual curiosity

Family experiences

Research journeys

Community impact

Identity

Leadership

Failure and resilience

Admissions officers generally value genuine reflection over dramatic stories.

---

# Section 12: Letters of Recommendation

Strong recommendation letters provide insight into:

Work ethic

Curiosity

Classroom engagement

Character

Collaboration

Leadership

The strongest recommendations often come from teachers who know the student well and can provide detailed examples rather than generic praise.

---

# Section 13: Honors and Awards

Awards help admissions officers compare students on a broader scale.

Recognition may occur at multiple levels:

School

Regional

State

National

International

Generally, broader recognition carries greater weight, though context and selectivity matter.

---

# Section 14: Prestigious Competitions by Academic Field

## Computer Science

International Olympiad in Informatics (IOI)

USA Computing Olympiad (USACO)

Google Code Jam (historical)

Meta Hacker Cup

ICPC (college level)

MIT Battlecode

Congressional App Challenge

NASA Space Apps Challenge

Technovation Challenge

FIRST Robotics Competition

FIRST Tech Challenge

VEX Robotics Competition

CyberPatriot

---

## Mathematics

International Mathematical Olympiad (IMO)

USA Mathematical Olympiad (USAMO)

American Invitational Mathematics Examination (AIME)

AMC 10

AMC 12

Harvard-MIT Mathematics Tournament (HMMT)

Princeton University Mathematics Competition (PUMaC)

Math Prize for Girls

M3 Challenge

Purple Comet Math Meet

---

## Physics

International Physics Olympiad (IPhO)

USA Physics Olympiad (USAPhO)

PhysicsBowl

F=ma Exam

Princeton Physics Competition

---

## Chemistry

International Chemistry Olympiad (IChO)

US National Chemistry Olympiad (USNCO)

Chemagination

---

## Biology

International Biology Olympiad (IBO)

USA Biology Olympiad (USABO)

Genes in Space

BioGENEius Challenge

---

## Engineering

FIRST Robotics Competition

FIRST Tech Challenge

VEX Robotics

Conrad Challenge

NASA Human Exploration Rover Challenge

Engineering Design Challenge

TSA Engineering Competitions

---

## Artificial Intelligence and Machine Learning

AI4ALL Challenges

Kaggle Competitions

Google Science Fair (historical)

Regeneron Science Talent Search

Regeneron International Science and Engineering Fair (ISEF)

MIT THINK

Davidson Fellows Scholarship

---

## Business and Economics

DECA International Career Development Conference (ICDC)

Future Business Leaders of America (FBLA)

National Economics Challenge

Wharton Investment Competition

Diamond Challenge

Blue Ocean Entrepreneurship Competition

Fed Challenge

---

## Writing and Journalism

Scholastic Art & Writing Awards

John Locke Essay Competition

New York Times Student Contests

National High School Journalism Convention Competitions

---

## Debate and Public Speaking

National Speech & Debate Tournament

World Schools Debate Championship

Model United Nations Conferences

Mock Trial Competitions

---

## Science Research

Regeneron Science Talent Search (STS)

Regeneron ISEF

Junior Science and Humanities Symposium (JSHS)

Conrad Challenge

ExploraVision

Genius Olympiad

---

# Section 15: Demonstrated Interest

Some colleges track applicant engagement.

Examples include:

Campus visits

Admissions webinars

College fairs

Email interactions

Interviews

Early Decision applications

Not all institutions consider demonstrated interest, but it can matter at some private universities.

---

# Section 16: Holistic Admissions

Holistic admissions evaluate the entire applicant.

Rather than relying on formulas, admissions officers consider:

Academic achievement

Course rigor

Intellectual curiosity

Leadership

Impact

Community involvement

Essays

Recommendations

Personal context

Family background

Available opportunities

No single achievement guarantees admission.

---

# Section 17: Typical Profiles by Competitiveness

## Competitive Public Universities

Typical characteristics:

* Strong GPA
* Challenging coursework
* Several extracurriculars
* Leadership in one or two activities
* Solid essays
* Competitive SAT/ACT (if submitted)

---

## Highly Selective Universities

Typical characteristics:

* Near-perfect academic record
* Maximum feasible course rigor
* Significant leadership
* Original research or substantial projects
* Meaningful community impact
* State, national, or international recognition
* Outstanding essays
* Exceptional recommendations

---

# Section 18: Major-Specific Expectations

## Computer Science

Admissions committees often value:

Advanced mathematics

Programming experience

Algorithms

Software projects

Open-source contributions

Hackathons

AI/ML research

Cybersecurity

Robotics

USACO participation

---

## Engineering

Important factors:

Physics

Calculus

Engineering projects

Robotics

CAD

Competitions

Research

Design experience

---

## Biological Sciences

Important factors:

Biology

Chemistry

Laboratory research

Medical volunteering

Science Olympiad

USABO

Research publications

---

## Business

Important factors:

Economics

Entrepreneurship

DECA

FBLA

Investment clubs

Business ventures

Leadership

---

## Humanities

Important factors:

Writing

History

Languages

Journalism

Speech

Debate

Research

Community engagement

---

# Section 19: Common Misconceptions

Myth: More extracurricular activities always lead to stronger applications.

Reality: Colleges generally prefer depth, impact, and sustained commitment over a long list of superficial involvements.

---

Myth: A perfect SAT score guarantees admission.

Reality: Standardized testing is only one component of a holistic review.

---

Myth: Students need dozens of AP courses.

Reality: Admissions officers expect students to challenge themselves appropriately based on their school's offerings and their academic interests.

---

Myth: Community service should only be completed to satisfy application requirements.

Reality: Long-term, authentic service with meaningful contributions is viewed much more favorably than accumulating volunteer hours without sustained engagement.

---

# Section 20: Key Principles for Building a Strong College Application

The strongest applicants typically exhibit the following characteristics:

* Excellent academic performance over multiple years.
* Challenging coursework relative to available opportunities.
* Consistent involvement in a few meaningful extracurricular activities.
* Leadership demonstrated through measurable impact.
* Intellectual curiosity expressed through research, projects, or independent learning.
* Authentic and sustained community engagement.
* Thoughtful essays that reveal character and personal growth.
* Strong letters of recommendation from teachers who know the student well.
* Recognition through awards, competitions, or other accomplishments that reflect exceptional ability.
* A coherent personal narrative that connects academic interests, activities, values, and future goals.

Ultimately, successful college applications are not built around checking boxes but around presenting a compelling story of who the student is, how they have grown, what they have contributed to their communities, and how they are likely to contribute to a college campus. The admissions process seeks students who have demonstrated both achievement and potential, recognizing excellence within the context of each student's available opportunities and individual circumstances.

'''
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


def _chunk_knowledge_base(text: str) -> list:
    """Split the reference article into per-section chunks on its '---' dividers
    so retrieval can pull just the sections relevant to one profile instead of
    dumping the whole article into every prompt."""
    sections = re.split(r"\n\s*---\s*\n", text)
    return [s.strip() for s in sections if s.strip()]


def _build_index(texts):
    if not texts:
        return None, None
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(texts)
    return vectorizer, matrix


def _tfidf_retrieve(query: str, texts, vectorizer, matrix, k: int = 5):
    """Return up to k texts most similar to query, best first."""
    if not query or vectorizer is None:
        return []
    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, matrix)[0]
    ranked = scores.argsort()[::-1][:k]
    return [texts[i] for i in ranked if scores[i] > 0]


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

        # TF-IDF + cosine similarity instead of neural embeddings + FAISS --
        # that stack (torch/sentence-transformers/faiss) needs close to a GB
        # of RAM just to load, which doesn't fit Render's 512MB free tier.
        # At this corpus size, TF-IDF is plenty to match a student profile to
        # relevant competitions/reference material and costs a few MB.
        self.texts = [_competition_to_text(row) for row in competitions]
        self.vectorizer, self.matrix = _build_index(self.texts)

        self.kb_texts = _chunk_knowledge_base(EXTRA_CONTEXT)
        self.kb_vectorizer, self.kb_matrix = _build_index(self.kb_texts)

        # temperature=0 was making every response read like a restatement of
        # the input profile; a bit of headroom gets more judgment-driven phrasing.
        self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.4, api_key=API_KEY)

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
        matches = _tfidf_retrieve(retrieval_signal or profile_json, self.texts, self.vectorizer, self.matrix, k=7)
        context = "\n".join(matches)

        # Broader signal for the reference article -- it covers GPA, rigor,
        # testing, essays, etc., not just interest matching like competitions.
        kb_query = " ".join(
            str(value)
            for value in (
                profile.get("interests"),
                profile.get("intended_majors"),
                profile.get("current_courses"),
                profile.get("ap_courses"),
                profile.get("academic_strengths"),
                profile.get("academic_weaknesses"),
                profile.get("remaining_requirements"),
                profile.get("extracurriculars"),
                profile.get("honors_awards"),
                profile.get("college_preferences"),
            )
            if value
        )
        kb_matches = _tfidf_retrieve(kb_query or profile_json, self.kb_texts, self.kb_vectorizer, self.kb_matrix, k=5)
        kb_context = "\n\n".join(kb_matches)

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
    to the recommendation instead. The same rule applies to the GENERAL ADMISSIONS REFERENCE
    below -- use it to calibrate your judgment (e.g. what counts as rigorous, what SAT range is
    competitive for their college list), never quote or summarize it back at the student as if
    reciting the article were advice.

    STUDENT APPLICATION
    {profile_json}

    RELEVANT SUPPORTING MATERIAL (retrieved based on this student's profile)
    {context}

    GENERAL ADMISSIONS REFERENCE (retrieved from a college admissions guide -- background
    knowledge to calibrate your judgment against, not a source to quote)
    {kb_context}

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
