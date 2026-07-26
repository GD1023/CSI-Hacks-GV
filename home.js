import { supabase } from './supabase-client.js';
import { fetchProfileFields } from './profile-view.js';
import { renderRadarChart } from './radar-chart.js';

function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
}

// Every category score is a weighted blend of components, each capped at 100
// via a "how many of these would count as a full score" divisor. There's no
// canonical formula for this -- these divisors were picked to feel reasonable
// (e.g. 5 AP courses maxes out rigor) rather than derived from anything.
function countComponent(count, countForFullScore) {
    return clamp((count / countForFullScore) * 100, 0, 100);
}

function coursesScore(profile) {
    const gpaComponent = profile.gpa ? clamp((profile.gpa / 5) * 100, 0, 100) : 0;
    const rigorComponent = countComponent((profile.ap_courses || []).length, 5);
    const loadComponent = countComponent(
        (profile.current_courses || []).length + (profile.completed_courses || []).length,
        12
    );
    return 0.4 * gpaComponent + 0.35 * rigorComponent + 0.25 * loadComponent;
}

function clubsScore(profile) {
    const leadershipComponent = countComponent((profile.leadership_roles || []).length, 3);
    const membershipComponent = countComponent((profile.clubs || []).length, 4);
    return 0.6 * leadershipComponent + 0.4 * membershipComponent;
}

function extracurricularsScore(profile) {
    const activitiesComponent = countComponent((profile.extracurriculars || []).length, 5);
    const experienceComponent = countComponent(
        (profile.work_experience || []).length + (profile.volunteer_experience || []).length,
        4
    );
    return 0.55 * activitiesComponent + 0.45 * experienceComponent;
}

function awardsScore(profile) {
    const honorsComponent = countComponent((profile.honors_awards || []).length, 4);
    const competitionComponent = countComponent((profile.competition_history || []).length, 5);
    const commitmentComponent = countComponent(profile.competition_hours_per_week || 0, 10);
    return 0.45 * honorsComponent + 0.4 * competitionComponent + 0.15 * commitmentComponent;
}

// Unlike the other categories, missing scores here aren't averaged in as 0 --
// SAT/ACT/PSAT are alternatives to each other (most students only take one or
// two), so the score is the average of whichever were actually reported.
function testingScore(profile) {
    const normalized = [];
    if (profile.sat_score) normalized.push(clamp(((profile.sat_score - 400) / 1200) * 100, 0, 100));
    if (profile.act_score) normalized.push(clamp(((profile.act_score - 1) / 35) * 100, 0, 100));
    if (profile.psat_score) normalized.push(clamp(((profile.psat_score - 320) / 1200) * 100, 0, 100));
    if (!normalized.length) return 0;
    return normalized.reduce((sum, value) => sum + value, 0) / normalized.length;
}

const PROFILE_COLUMNS = [
    'gpa', 'ap_courses', 'current_courses', 'completed_courses',
    'clubs', 'leadership_roles',
    'extracurriculars', 'work_experience', 'volunteer_experience',
    'honors_awards', 'competition_history', 'competition_hours_per_week',
    'sat_score', 'act_score', 'psat_score',
];

const section = document.getElementById('profile-radar-section');

async function showRadar(userId) {
    const profile = await fetchProfileFields(userId, PROFILE_COLUMNS);

    renderRadarChart('profile-radar', [
        { label: 'Courses', score: coursesScore(profile) },
        { label: 'Clubs', score: clubsScore(profile) },
        { label: 'Extracurriculars', score: extracurricularsScore(profile) },
        { label: 'Awards', score: awardsScore(profile) },
        { label: 'Testing', score: testingScore(profile) },
    ]);

    section.style.display = '';
}

function hideRadar() {
    section.style.display = 'none';
}

const { data: { session } } = await supabase.auth.getSession();
if (session) {
    await showRadar(session.user.id);
}

supabase.auth.onAuthStateChange(async (_event, newSession) => {
    if (newSession) {
        await showRadar(newSession.user.id);
    } else {
        hideRadar();
    }
});
