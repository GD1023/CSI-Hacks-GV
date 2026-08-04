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

AP Calculus AB

AP Calculus BC

AP Biology

AP Chemistry

AP Physics 1

AP Physics 2

AP Physics C Mechanics

AP Physics C Electricity & Magnetism

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

Berkeley Math Tournament (BMT)

Stanford Math Tournament (SMT)

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

Hackathons

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


Here are some more competitions and context:

Academic Competition: American Mathematics Competitions (AMC) 10/12 – a rigorous 75-minute, 25-question multiple-choice math contest that serves as the primary gateway to the AIME and prestigious national math teams. Keywords: mathematics, problem-solving, logic, algebra, geometry, number theory
---
Academic Competition: National Science Bowl – a fast-paced, buzzer-style academic competition hosted by the U.S. Department of Energy covering biology, chemistry, physics, energy, and mathematics. Keywords: STEM, quiz bowl, teamwork, science, buzzer competition
---
Academic Competition: Science Olympiad – a nationwide team competition with 23 STEM events per division, from lab experiments to building devices like airplanes and bridges. Keywords: hands-on, engineering, biology, physics, chemistry, build events
---
Academic Competition: U.S. National Chemistry Olympiad – a tiered exam competition for high school students that begins with a local exam and advances to a national study camp and international competition. Keywords: chemistry, lab, theoretical, international, olympiad
---
Academic Competition: Physics Bowl – a 45-minute, 40-question multiple-choice physics exam administered by the AAPT, with Division 1 for algebra-based and Division 2 for calculus-based physics. Keywords: physics, mechanics, electricity, magnetism, standardized
---
Academic Competition: F=ma Exam – a 75-minute, 25-question multiple-choice mechanics exam that serves as the first round for U.S. Physics Team selection. Keywords: Newton's laws, kinematics, energy, momentum, olympiad pathway
---
Academic Competition: National History Day (NHD) – a project-based competition where students create exhibits, documentaries, papers, or performances on a historical theme. Keywords: history, research, primary sources, project-based, public speaking
---
Academic Competition: NAQT Quiz Bowl – a buzzer-based academic trivia competition covering literature, science, history, and pop culture, with local and national championship tournaments. Keywords: trivia, buzzer, general knowledge, teamwork, academic challenge
---
Academic Competition: United States Academic Decathlon – a 10-event competition where teams of nine students compete across honors, scholastic, and varsity GPA divisions. Keywords: interdisciplinary, GPA-based, team, comprehensive, academics
---
Academic Competition: Conrad Challenge – a team-based innovation competition where students design solutions to global problems in areas like aerospace, health, and sustainability. Keywords: innovation, entrepreneurship, STEM, social impact, prototyping
---
Academic Competition: DECA Competitive Events – business and marketing competitions with role-plays, case studies, and written events for emerging leaders. Keywords: business, marketing, finance, hospitality, career preparation
---
Academic Competition: FBLA (Future Business Leaders of America) – competitive events and leadership conferences for students interested in business and entrepreneurship. Keywords: business, leadership, competition, networking, career
---
Academic Competition: HOSA - Future Health Professionals – health science competitions with events in biomedical science, clinical skills, and health policy. Keywords: medicine, health science, clinical skills, leadership, career
---
Academic Competition: Mock Trial – a simulation of a court case where students act as attorneys and witnesses, competing in regional and state tournaments. Keywords: law, debate, public speaking, critical thinking, teamwork
---
Academic Competition: Model United Nations (MUN) – a simulation of UN committees where students debate global issues and draft resolutions. Keywords: diplomacy, international relations, debate, public speaking, global affairs
---
Academic Competition: Model Congress – a simulation of U.S. legislative proceedings where students propose and debate bills. Keywords: government, civics, debate, legislation, public policy
---
Academic Competition: National Academic League – a team-based academic competition where students answer questions and complete collaborative challenges aligned with national standards. Keywords: teamwork, standards-based, interdisciplinary, buzzer, collaboration
---
Academic Competition: PicoCTF – a cybersecurity competition where students solve challenges in reverse engineering, cryptography, and web exploitation. Keywords: cybersecurity, hacking, cryptography, computer science, capture the flag
---
Academic Competition: Space Settlement Design Competition – a team-based engineering competition where students design a space settlement and present proposals to industry judges. Keywords: aerospace, engineering, design, teamwork, space
---
Academic Competition: World of 8 Billion Video Contest – a competition where students create short videos about global challenges related to population growth. Keywords: video production, global issues, advocacy, creativity, population
---
Art Competition: Scholastic Art & Writing Awards – the nation's longest-running creative recognition program for grades 7-12, with categories in art, writing, and multimedia. Keywords: art, writing, creative, portfolio, scholarship
---
Art Competition: Congressional Art Competition – a nationwide high school visual arts competition with winners displayed in the U.S. Capitol for one year. Keywords: visual arts, painting, drawing, photography, national recognition
---
Art Competition: All American High School Film Festival – a film festival where student works are screened in Times Square with over $500,000 in prizes and scholarships. Keywords: filmmaking, cinema, video production, scholarship, film festival
---
Art Competition: NAACP ACT-SO – a yearlong achievement program with 33 competitions in STEM, humanities, business, and performing, visual, and culinary arts for African American high school students. Keywords: arts, humanities, STEM, cultural, achievement
---
Art Competition: Freedom 250 American Heroes Student Art Contest – a national art contest honoring American heroes for the nation's 250th anniversary, with prizes from NEH. Keywords: art, history, patriotism, visual arts, national contest
---
Art Competition: National Young Composers Challenge – a composition competition where winning orchestral and ensemble pieces are performed and recorded by a professional orchestra. Keywords: music, composition, orchestra, performance, classical
---
Art Competition: Princeton 10-Minute Play Contest – a playwriting competition judged by Princeton theater faculty, open to 11th graders. Keywords: theater, playwriting, dramatic writing, Princeton, competition
---
Art Competition: The Edit Digital Storytelling Challenge – a free competition where students create 30-90 second video news reports on wellness topics. Keywords: video, journalism, storytelling, digital media, wellness
---
Art Competition: International Compost Awareness Week Poster Contest – an environmental art competition with a $500 prize for the winning poster. Keywords: art, environmental, sustainability, design, poster
---
Entrepreneurship Competition: Blue Ocean Competition – a business pitch competition where high school students present innovative ideas to receive feedback and prize money. Keywords: entrepreneurship, pitch, business plan, innovation, venture
---
Entrepreneurship Competition: Stevens High School Entrepreneurship and AI Pitch Competition – a video pitch competition for business ideas integrating artificial intelligence, with cash prizes. Keywords: AI, entrepreneurship, pitch, innovation, technology
---
Entrepreneurship Competition: Innovator Competition (Jacobson Institute) – a competition where high school students pitch business ideas and compete for seed capital. Keywords: entrepreneur, pitch, seed funding, innovation, business
---
Entrepreneurship Competition: BUILD's Design Challenge – a design-thinking competition where students create solutions to real-world challenges. Keywords: design thinking, entrepreneurship, prototyping, social impact, innovation
---
Entrepreneurship Competition: Samsung Solve for Tomorrow – a competition where students create STEM solutions for community problems, with $2 million in prizes for schools. Keywords: STEM, community service, engineering, innovation, social impact
---
Writing Competition: New York Times Student Writing Contests – monthly writing contests for ages 13-19 on topics ranging from reviews to editorials to narratives. Keywords: writing, journalism, opinion, creativity, New York Times
---
Writing Competition: AFSA National High School Essay Contest – an essay competition on international relations, with prizes including Semester at Sea tuition. Keywords: international relations, essay, history, scholarship, global affairs
---
Writing Competition: Jane Austen Essay Contest – a scholarship essay competition on a new Austen theme each year, sponsored by the Jane Austen Society. Keywords: literature, Jane Austen, essay, scholarship, humanities
---
Writing Competition: Stossel in the Classroom – an essay and video competition on entrepreneurship and innovation with $20,000 in prizes. Keywords: entrepreneurship, innovation, economics, media, essay
---
Writing Competition: Breakthrough Junior Challenge – a video competition where students explain a big scientific idea in physics, life sciences, or math for college scholarships. Keywords: science, video, communication, physics, scholarship
---
Science Fair: Regeneron International Science and Engineering Fair (ISEF) – the world's largest pre-college science competition, with affiliated local and regional fairs. Keywords: research, science fair, international, STEM, presentation
---
Science Fair: Regeneron Science Talent Search – the nation's oldest and most prestigious science and math competition for high school seniors. Keywords: research, STEM, senior, competition, prestigious
---
Science Fair: National Science Bowl Regional Competitions – qualifying tournaments held across the U.S. for teams to advance to the national championship in Washington, D.C. Keywords: qualification, regional, competition, science, math
---
Science Fair: eCYBERMISSION – a virtual STEM competition for grades 6-9 where teams identify and solve community problems. Keywords: STEM, community, problem-solving, middle school, team
---
Science Fair: Davidson Fellows Scholarship – a scholarship program for students under 18 with significant projects in science, technology, engineering, mathematics, or humanities. Keywords: scholarship, research, innovation, advanced, fellowship
---
Science Fair: BioGENEius Challenge – a competition for high school students conducting biotechnology research. Keywords: biotechnology, genetics, research, life sciences, STEM
---
Science Fair: Physics Olympiad – a series of exams leading to the U.S. Physics Team and International Physics Olympiad. Keywords: physics, olympiad, mechanics, advanced, competition
---
Science Fair: Biology Olympiad – a competition for high school students with exams in molecular, cellular, and organismal biology. Keywords: biology, genetics, ecology, evolution, olympiad
---
Science Fair: Linguistics Olympiad – a competition where students solve linguistic puzzles using logic and analytical reasoning. Keywords: linguistics, logic, puzzles, analytical, language
---
Fall High School Sports: Football – a team sport played in the fall, governed by state athletic associations like GHSA. Keywords: athletics, team, contact, fall season, competitive
---
Fall High School Sports: Cross Country – a distance running sport contested in the fall, building endurance and team scoring. Keywords: running, endurance, team, fall sport, track
---
Fall High School Sports: Volleyball – a team sport played indoors in the fall, focusing on serving, setting, and spiking. Keywords: athletics, team, indoor, fall, competitive
---
Fall High School Sports: Girls Soccer – a fall team sport emphasizing footwork, strategy, and cardiovascular fitness. Keywords: soccer, team, fall, endurance, competitive
---
Fall High School Sports: Boys Tennis – a fall team sport developing hand-eye coordination and strategic play. Keywords: tennis, racquet, fall, singles, doubles
---
Fall High School Sports: Girls Swim and Dive – a fall aquatic sport combining swimming races and diving events. Keywords: swimming, diving, aquatic, fall, competitive
---
Winter High School Sports: Boys Basketball – a winter team sport focused on shooting, dribbling, and defensive strategy. Keywords: basketball, winter, team, athletic, competitive
---
Winter High School Sports: Girls Basketball – a winter team sport that builds agility, teamwork, and shooting skills. Keywords: basketball, winter, athletic, team, competitive
---
Winter High School Sports: Wrestling – an individual winter sport emphasizing strength, technique, and weight-class competition. Keywords: wrestling, grappling, winter, individual, strength
---
Winter High School Sports: Boys Swim and Dive – a winter aquatic competition with individual and relay events. Keywords: swimming, diving, winter, aquatic, competitive
---
Winter High School Sports: Gymnastics – a winter sport developing flexibility, balance, and strength through apparatus routines. Keywords: gymnastics, flexibility, balance, winter, artistic
---
Spring High School Sports: Track and Field – a spring sport with running, jumping, and throwing events for individual and team competition. Keywords: running, jumping, throwing, spring, competitive
---
Spring High School Sports: Baseball – a spring team sport focused on hitting, pitching, and fielding strategy. Keywords: baseball, spring, bat, ball, team
---
Spring High School Sports: Softball – a spring team sport similar to baseball with fast-pitch and slow-pitch variations. Keywords: softball, spring, bat, ball, team
---
Spring High School Sports: Girls Tennis – a spring racquet sport with singles and doubles competition. Keywords: tennis, spring, racquet, singles, doubles
---
Spring High School Sports: Boys Soccer – a spring team sport requiring footwork, strategy, and endurance. Keywords: soccer, spring, team, endurance, competitive
---
Spring High School Sports: Golf – a spring individual sport emphasizing precision, course management, and mental focus. Keywords: golf, spring, individual, precision, strategy
---
Club Sport: Archery – a club sport teaching precision and focus, with opportunities for competition at archery ranges. Keywords: archery, precision, target, hand-eye coordination, discipline
---
Club Sport: Badminton – a racquet sport focusing on agility, speed, and hand-eye coordination, played in singles and doubles. Keywords: badminton, racquet, agility, doubles, singles
---
Club Sport: Pickleball – a paddle sport combining elements of tennis, badminton, and ping-pong, growing in popularity. Keywords: pickleball, paddle, hand-eye, agility, recreational
---
Club Sport: Table Tennis – a fast-paced indoor sport emphasizing reflexes, spin, and precision. Keywords: ping-pong, table tennis, reflex, spin, hand-eye
---
Club Sport: Ultimate Frisbee – a non-contact team sport combining elements of football and soccer with a flying disc. Keywords: ultimate, frisbee, non-contact, team, endurance
---
Club Sport: Cricket – a bat-and-ball team sport with a global following, emphasizing timing, strategy, and fielding. Keywords: cricket, bat, ball, team, strategy
---
Club Sport: Rock Climbing – an indoor or outdoor climbing club that builds strength, flexibility, and problem-solving. Keywords: climbing, rock, strength, problem-solving, adventure
---
Club Sport: Chess – a strategic board game played competitively in clubs and tournaments. Keywords: chess, strategy, logic, competition, critical thinking
---
Club Sport: Cornhole – a recreational club activity involving throwing bags at a raised platform. Keywords: cornhole, recreational, team, coordination, throwing
---
Club Sport: Petanque – a French boules sport emphasizing precision throwing and strategy. Keywords: petanque, boules, precision, strategy, recreational
---
Intramural Sport: Intramural Basketball – campus-based recreational basketball leagues for fun and fitness. Keywords: intramural, basketball, recreation, campus, fitness
---
Intramural Sport: Intramural Volleyball – recreational volleyball leagues with co-ed and gender-specific divisions. Keywords: intramural, volleyball, recreation, campus, team
---
Intramural Sport: Intramural Flag Football – non-contact football leagues emphasizing fun and participation. Keywords: flag football, intramural, non-contact, recreation, team
---
Academic Club: Math Club – a student club for practicing math problems, preparing for competitions, and exploring mathematical topics. Keywords: mathematics, problem-solving, competition prep, collaboration
---
Academic Club: Science Club – a club focused on experiments, guest speakers, and exploring science topics beyond the curriculum. Keywords: science, experiments, inquiry, exploration, critical thinking
---
Academic Club: Computer Science Club – a club for learning programming languages, building projects, and preparing for hackathons. Keywords: coding, programming, algorithms, projects, hackathons
---
Academic Club: Robotics Club (FIRST Robotics) – a competition robotics team building robots for challenges like VEX or FIRST. Keywords: robotics, VEX, FIRST, engineering, programming, building
---
Academic Club: Girls Who Code – a club encouraging girls to explore computer science through projects and mentorship. Keywords: girls, coding, computer science, diversity, mentorship
---
Academic Club: DECA Club – a business club preparing students for competitive events in marketing, finance, and management. Keywords: business, marketing, finance, competition, leadership
---
Academic Club: FBLA Club – a career preparation club for students interested in business and entrepreneurship. Keywords: business, leadership, career prep, competition, networking
---
Academic Club: HOSA Club – a health science club with competitive events and career exploration in medicine and health fields. Keywords: health science, medicine, competition, career prep, leadership
---
Academic Club: Mock Trial Team – a competitive team that simulates trial proceedings and competes against other schools. Keywords: law, debate, public speaking, teamwork, competition
---
Academic Club: Model UN Team – a club where students simulate UN committees and debate international issues. Keywords: diplomacy, debate, international relations, public speaking, research
---
Academic Club: Debate Team – a competitive speech and debate club with events in Lincoln-Douglas, policy, and public forum. Keywords: debate, public speaking, argumentation, critical thinking, competition
---
Academic Club: Quiz Bowl Team – a buzzer-based trivia team competing in academic tournaments. Keywords: trivia, buzzer, academic competition, teamwork, knowledge
---
Academic Club: Speech and Debate – a co-curricular activity combining public speaking, research, and persuasive argumentation. Keywords: speech, debate, public speaking, research, persuasion
---
Academic Club: Economics Club – a club exploring economic concepts, current events, and investment strategies. Keywords: economics, finance, investment, current events, markets
---
Academic Club: Investment Club – a club for learning about stocks, markets, and portfolio management. Keywords: finance, investing, stocks, market analysis, portfolio
---
Academic Club: Entrepreneurship Club – a club focusing on business ideation, pitches, and startup strategy. Keywords: entrepreneurship, business, innovation, pitching, startups
---
Academic Club: Creative Writing Club – a club for writers to share, critique, and develop original creative works. Keywords: writing, fiction, poetry, critique, creativity
---
Academic Club: Film Appreciation Club – a club for watching and discussing films, directors, and cinematic techniques. Keywords: film, cinema, media, analysis, appreciation
---
Academic Club: Documentary Club – a club focused on creating, watching, and analyzing documentary films. Keywords: documentary, filmmaking, media literacy, social issues
---
Academic Club: Art Club – a club for creating and appreciating visual arts like painting, drawing, and sculpture. Keywords: visual arts, drawing, painting, creativity, community
---
Academic Club: Photography Club – a club for learning and practicing photography techniques and sharing work. Keywords: photography, visual arts, composition, editing, creativity
---
Academic Club: Theatre Group – a club for acting, stage production, and dramatic performance. Keywords: theater, acting, stage, production, performance
---
Academic Club: Music Production Club – a club for creating music using digital audio workstations and recording equipment. Keywords: music, production, audio, digital, creativity
---
Service Club: Key Club – a student-led service organization affiliated with Kiwanis International. Keywords: service, leadership, community, philanthropy, civic engagement
---
Service Club: National Honor Society (NHS) – a prestigious organization recognizing scholarship, leadership, service, and character. Keywords: honor society, leadership, service, character, scholarship
---
Service Club: California Scholarship Federation (CSF) – a service organization for students with strong academic records. Keywords: scholarship, service, leadership, academics, recognition
---
Service Club: Best Buddies – a club promoting one-to-one friendships between students with and without intellectual disabilities. Keywords: inclusion, friendship, disability, community, service
---
Service Club: Red Cross Club – a service club supporting Red Cross missions through blood drives, disaster relief, and health initiatives. Keywords: service, health, disaster relief, community, volunteerism
---
Service Club: Habitat for Humanity Club – a service club organizing builds and fundraising for affordable housing. Keywords: service, housing, construction, community, philanthropy
---
Service Club: Meals on Wheels – a volunteer club delivering meals to seniors and homebound individuals. Keywords: service, senior care, nutrition, community, volunteerism
---
Service Club: Save the Sound – an environmental club focused on protecting and restoring local waterways. Keywords: environment, conservation, water, restoration, service
---
Service Club: Eco Reps – an environmental club promoting sustainability and green initiatives at school. Keywords: environment, sustainability, green, club, activism
---
Service Club: Heal the Bay – a club organizing beach cleanups and advocating for ocean health. Keywords: environment, marine, cleanups, advocacy, service
---
Service Club: Kids at Heart – a club supporting children's charities and pediatric health initiatives. Keywords: charity, children, service, philanthropy, health
---
Service Club: Operation Smile – a club raising awareness and funds for cleft lip and palate surgeries worldwide. Keywords: service, health, global, charity, fundraising
---
Cultural Club: Chinese Club – a club for exploring Chinese language, culture, and community. Keywords: Chinese, language, culture, diversity, community
---
Cultural Club: French Club – a club celebrating French language, culture, and cuisine. Keywords: French, language, culture, cuisine, international
---
Cultural Club: Spanish Club – a club for learning Spanish language and exploring Hispanic cultures. Keywords: Spanish, language, culture, diversity, community
---
Cultural Club: Latin Club – a club exploring Latin language and classical Roman culture. Keywords: Latin, classics, ancient, language, history
---
Cultural Club: Korean American Student Association – a club celebrating Korean culture and fostering community. Keywords: Korean, culture, heritage, community, diversity
---
Cultural Club: Jewish Student Union – a club for Jewish students to explore identity, culture, and community. Keywords: Jewish, culture, community, heritage, identity
---
Cultural Club: Muslim Student Association – a club for Muslim students to explore faith and community. Keywords: Muslim, faith, community, culture, identity
---
Cultural Club: Multicultural Student Union – a club promoting diversity and cross-cultural understanding. Keywords: diversity, culture, inclusion, community, unity
---
Special Interest Club: Dungeons and Dragons Club – a club for playing the tabletop RPG and building storytelling skills. Keywords: D&D, roleplaying, gaming, storytelling, community
---
Special Interest Club: Board Game Club – a club for playing strategy and party board games. Keywords: board games, strategy, recreation, community, gaming
---
Special Interest Club: Culinary Arts Club – a club for cooking, baking, and exploring food culture. Keywords: cooking, baking, culinary, food, creativity
---
Special Interest Club: Gardening Club – a club for planting, maintaining gardens, and learning about botany. Keywords: gardening, botany, sustainability, outdoors, ecology
---
Special Interest Club: Beekeeping Club – a club for learning about bees and maintaining campus hives. Keywords: beekeeping, ecology, sustainability, bees, environmental
---
Special Interest Club: Bird Watching Club – a club for observing and identifying local bird species. Keywords: ornithology, birding, ecology, outdoors, observation
---
Special Interest Club: Sports Analytics Club – a club analyzing sports data using statistics and coding. Keywords: sports, analytics, data science, statistics, coding
---
Special Interest Club: Rock Band Club – a club for forming bands and performing music. Keywords: music, band, performance, rock, ensemble
---
Special Interest Club: K-Pop Dance Club – a club for learning and performing K-Pop dance choreography. Keywords: K-Pop, dance, performance, culture, choreography
---
Special Interest Club: Step Team – a club practicing step dance, a percussive dance form. Keywords: step, dance, performance, rhythm, art
---
Special Interest Club: Crochet Club – a club for learning and practicing crochet and knitting crafts. Keywords: crochet, knitting, crafting, fiber arts, creativity
---
Special Interest Club: Philosophy Club – a club exploring philosophical questions and ethical debates. Keywords: philosophy, ethics, debate, critical thinking, inquiry
---
Special Interest Club: Neuroscience Club – a club exploring brain science with lectures, discussions, and projects. Keywords: neuroscience, brain, psychology, inquiry, research
---
Special Interest Club: Rocketry Club – a club designing and building model rockets for competitions. Keywords: rocketry, aerospace, engineering, design, competition
---
Special Interest Club: Cryptography Club – a club exploring codes, ciphers, and computer security. Keywords: cryptography, codes, security, math, puzzles
---
Special Interest Club: Aerospace Club – a club for exploring aviation, space, and rocketry projects. Keywords: aerospace, aviation, space, engineering, flight
---
Special Interest Club: Movie Club – a club for watching, discussing, and analyzing films. Keywords: film, cinema, media, discussion, appreciation
---
Special Interest Club: Tea Club – a club exploring tea culture, tasting, and preparation. Keywords: tea, culture, tasting, tradition, social


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


# The 7 advice bins, matching the 7 keys the chat prompt must return. Every KB
# chunk gets tagged into exactly one of these so retrieval can be scoped per
# advice section instead of one shared blob feeding every section.
_BIN_ORDER = ["courses", "clubs", "extracurriculars", "competitions", "testing", "college_prep", "career"]

# EXTRA_CONTEXT's numbered "# Section N: ..." headings, mapped to a bin.
_SECTION_BIN_MAP = {
    1: "courses", 2: "courses", 3: "courses", 4: "courses",
    5: "testing", 6: "testing",
    7: "extracurriculars", 8: "extracurriculars", 9: "extracurriculars", 10: "extracurriculars",
    11: "college_prep", 12: "college_prep",
    13: "competitions", 14: "competitions",
    15: "college_prep", 16: "college_prep", 17: "college_prep",
    18: "career",
    19: "college_prep", 20: "college_prep",
}
_SECTION_HEADING_RE = re.compile(r"^#+\s*Section\s+(\d+)\s*:", re.MULTILINE)

# The catalog-style tail of EXTRA_CONTEXT (one-line entries like "Academic Club:
# Math Club -- ...") carries no "Section N" heading of its own, so its entries
# are tagged by category prefix instead, overriding the section-based default.
_TAIL_PREFIX_BIN_MAP = {
    "Academic Competition": "competitions",
    "Art Competition": "competitions",
    "Entrepreneurship Competition": "competitions",
    "Writing Competition": "competitions",
    "Science Fair": "competitions",
    "Fall High School Sports": "extracurriculars",
    "Winter High School Sports": "extracurriculars",
    "Spring High School Sports": "extracurriculars",
    "Club Sport": "extracurriculars",
    "Intramural Sport": "extracurriculars",
    "Academic Club": "clubs",
    "Service Club": "clubs",
    "Cultural Club": "clubs",
    "Special Interest Club": "clubs",
}
_TAIL_PREFIX_RE = re.compile(
    r"(?m)^(" + "|".join(re.escape(p) for p in _TAIL_PREFIX_BIN_MAP) + r"):"
)


def _tag_knowledge_base(chunks: list) -> list:
    """Tag each chunk (in the order _chunk_knowledge_base produced them) with one
    of _BIN_ORDER. A chunk inherits the bin of whichever '# Section N:' heading
    last preceded it; a tail-block catalog entry overrides that with its own
    category prefix since those entries don't carry a section heading."""
    tags = []
    current_section = None
    for chunk in chunks:
        heading_match = _SECTION_HEADING_RE.search(chunk)
        if heading_match:
            current_section = int(heading_match.group(1))

        tail_match = _TAIL_PREFIX_RE.search(chunk)
        if tail_match:
            tags.append(_TAIL_PREFIX_BIN_MAP[tail_match.group(1)])
        else:
            tags.append(_SECTION_BIN_MAP.get(current_section, "college_prep"))
    return tags


def _bin_indices(tags: list) -> dict:
    indices = {b: [] for b in _BIN_ORDER}
    for i, tag in enumerate(tags):
        indices[tag].append(i)
    return indices


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


def _tfidf_retrieve_bin(query: str, vectorizer, matrix, indices: list, texts: list, k: int = 10):
    """Like _tfidf_retrieve, but scoped to one bin's rows. Reuses the single
    shared TF-IDF space (matrix is row-sliced to the bin) rather than fitting a
    separate vectorizer per bin."""
    if not query or vectorizer is None or not indices:
        return []
    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, matrix[indices])[0]
    ranked = scores.argsort()[::-1][:k]
    return [texts[indices[i]] for i in ranked if scores[i] > 0]


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
        self.kb_bin_indices = _bin_indices(_tag_knowledge_base(self.kb_texts))

        # temperature=0 was making every response read like a restatement of
        # the input profile; a bit of headroom gets more judgment-driven phrasing.
        self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.4, api_key=API_KEY)

    def chat(self, profile: dict) -> dict:
        """Run the counselor prompt for one student profile (a dict shaped like a
        public.profiles row -- see context_schema.json for an example) and return
        the model's answer parsed as a dict of the seven advice sections.
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

        # Per-bin signal: each of the 7 advice bins retrieves against only the
        # profile fields relevant to that section, so e.g. testing isn't
        # diluted by extracurricular keywords and vice versa. All 7 share the
        # same fitted self.kb_vectorizer/self.kb_matrix -- only the candidate
        # rows searched (self.kb_bin_indices[bin_name]) differ per bin.
        bin_signals = {
            "courses": (
                profile.get("current_courses"),
                profile.get("completed_courses"),
                profile.get("ap_courses"),
                profile.get("academic_strengths"),
                profile.get("academic_weaknesses"),
                profile.get("remaining_requirements"),
                profile.get("schedule_type"),
            ),
            "clubs": (
                profile.get("clubs"),
                profile.get("leadership_roles"),
                profile.get("intended_majors"),
                profile.get("interest_areas"),
            ),
            "extracurriculars": (
                profile.get("extracurriculars"),
                profile.get("time_commitments"),
                profile.get("work_experience"),
                profile.get("volunteer_experience"),
            ),
            "competitions": (
                profile.get("interests"),
                profile.get("intended_majors"),
                profile.get("interest_areas"),
                profile.get("competition_history"),
                profile.get("competition_team_preference"),
                profile.get("honors_awards"),
            ),
            "testing": (
                profile.get("sat_score"),
                profile.get("act_score"),
                profile.get("psat_score"),
                profile.get("college_list"),
                profile.get("college_preferences"),
            ),
            "college_prep": (
                profile.get("personal_narrative"),
                profile.get("college_list"),
                profile.get("college_preferences"),
                profile.get("additional_notes"),
                profile.get("remaining_requirements"),
            ),
            "career": (
                profile.get("intended_majors"),
                profile.get("interest_areas"),
                profile.get("working_style"),
                profile.get("personal_narrative"),
                profile.get("interests"),
            ),
        }

        bin_context = {}
        for bin_name in _BIN_ORDER:
            query = " ".join(str(v) for v in bin_signals[bin_name] if v)
            bin_matches = _tfidf_retrieve_bin(
                query or profile_json,
                self.kb_vectorizer,
                self.kb_matrix,
                self.kb_bin_indices[bin_name],
                self.kb_texts,
                k=10,
            )
            bin_context[bin_name] = "\n\n".join(bin_matches)

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
    to the recommendation instead. The same rule applies to every SUPPORTING REFERENCE block
    below -- use it to calibrate your judgment (e.g. what counts as rigorous, what SAT range is
    competitive for their college list), never quote or summarize it back at the student as if
    reciting the reference were advice.

    STUDENT APPLICATION
    {profile_json}

    Analyze their application across these 7 aspects. Each one comes with its own SUPPORTING
    REFERENCE, retrieved specifically for that aspect -- use each block only to calibrate that
    aspect's judgment, not the others.

    1. Courses & rigor -- judge how rigorous their schedule actually is relative to their
       stated interests (not just listing it), and name a specific next-step course or two.
       SUPPORTING REFERENCE (courses & rigor)
       {bin_context["courses"]}

    2. Clubs & involvement -- judge whether their school clubs signal real depth/leadership
       for their intended major or just breadth, and say what would move them from member to
       standout (a specific role, project, or initiative). Do not name any club that is not
       verbatim in the SUPPORTING REFERENCE below as something to join -- you do not know it
       actually exists at their school.
       SUPPORTING REFERENCE (clubs & involvement)
       {bin_context["clubs"]}

    3. Extracurriculars -- using work experience, volunteering, and time commitments outside
       school, judge whether their outside-of-school activities reinforce or dilute their
       intended-major narrative, and flag any time-balance risk given their stated commitments.
       SUPPORTING REFERENCE (extracurriculars)
       {bin_context["extracurriculars"]}

    4. Competitions & awards -- using ONLY the competitions that actually appear in the
       RELEVANT SUPPORTING MATERIAL or SUPPORTING REFERENCE below, recommend which ones fit
       this student's interests, time availability, and team/solo preference, and say why over
       the alternatives retrieved. Do not name ANY competition, organization, or program that is
       not verbatim in one of those two blocks, even as a "you could look into" suggestion --
       you do not know it actually exists or fits their constraints. If both are empty or
       nothing in them fits, say plainly that the catalog didn't have a match and suggest they
       ask their counselor for options in their interest area, with no invented names.
       RELEVANT SUPPORTING MATERIAL (retrieved from the live competitions catalog)
       {context}
       SUPPORTING REFERENCE (competitions & awards guide)
       {bin_context["competitions"]}

    5. Testing -- judge their test scores against their college list/preferences specifically
       (not test scores in the abstract), and name the single highest-leverage gap to close next.
       SUPPORTING REFERENCE (testing)
       {bin_context["testing"]}

    6. College application prep -- judge their remaining graduation requirements, essay/
       narrative readiness, and college list fit, and name the single highest-leverage next step.
       SUPPORTING REFERENCE (college application prep)
       {bin_context["college_prep"]}

    7. Career fit -- judge how well their intended majors, interest areas, and working style
       actually cohere into a defensible career direction, and name one concrete way to test
       that direction before committing further (e.g. a specific kind of internship, project,
       or person to talk to).
       SUPPORTING REFERENCE (career fit)
       {bin_context["career"]}

    Return your analysis as a JSON object with exactly these keys, each a short (5-8 sentence)
    recommendation string: testing, clubs, extracurriculars, competitions, courses, career,
    college_prep. If part of the student's profile is missing, don't guess -- either skip
    referencing it or gently note that adding it would help. In your sentences, avoid filler words and focus on content. Provide many different options for the given category; for instance, competitions should have at least half a dozen competitions mentioned. Be rigorous and avoid repeating suggestions they've already mentioned.
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
