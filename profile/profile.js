import { supabase } from '../supabase-client.js';

const { data: { session } } = await supabase.auth.getSession();
const user = session.user;

const form = document.getElementById('profile-form');
const status = document.getElementById('profile-status');
const button = form.querySelector('button[type="submit"]');

document.getElementById('email').value = user.email;

// Fields stored as Postgres text[] columns. The form collects each as a
// "one per line" textarea instead of a separate child table per list, so we
// split/join on newlines when reading and writing.
const LIST_FIELDS = [
    'current_courses', 'completed_courses', 'ap_courses', 'remaining_requirements',
    'academic_strengths', 'academic_weaknesses', 'extracurriculars', 'clubs',
    'leadership_roles', 'honors_awards', 'interest_areas', 'work_experience',
    'volunteer_experience', 'intended_majors', 'competition_history', 'college_list',
];

// Numeric columns -- an empty input should become null, not 0 or NaN.
const NUMBER_FIELDS = [
    'graduation_year', 'max_courses_per_term', 'gpa', 'sat_score', 'act_score',
    'psat_score', 'competition_hours_per_week',
];

// Plain text/select columns, read and written as-is.
const TEXT_FIELDS = [
    'name', 'grade', 'school', 'school_type', 'interests', 'time_commitments',
    'personal_narrative', 'additional_notes', 'schedule_type', 'school_profile_link',
    'transcript_link', 'competition_team_preference', 'travel_constraints',
    'budget_constraints',
];

const ALL_FIELDS = [...TEXT_FIELDS, ...NUMBER_FIELDS, ...LIST_FIELDS];

function arrayToTextarea(value) {
    return Array.isArray(value) ? value.join('\n') : '';
}

function textareaToArray(value) {
    return value
        .split('\n')
        .map((line) => line.trim())
        .filter((line) => line.length > 0);
}

const { data: profile, error: fetchError } = await supabase
    .from('profiles')
    .select(ALL_FIELDS.join(', '))
    .eq('id', user.id)
    .maybeSingle();

if (fetchError) {
    status.textContent = fetchError.message;
    status.classList.add('form-status-error');
} else if (profile) {
    TEXT_FIELDS.forEach((field) => {
        document.getElementById(field).value = profile[field] || '';
    });
    NUMBER_FIELDS.forEach((field) => {
        document.getElementById(field).value = profile[field] ?? '';
    });
    LIST_FIELDS.forEach((field) => {
        document.getElementById(field).value = arrayToTextarea(profile[field]);
    });
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    status.textContent = 'Saving...';
    status.classList.remove('form-status-error');
    button.disabled = true;

    const payload = { id: user.id };

    TEXT_FIELDS.forEach((field) => {
        payload[field] = document.getElementById(field).value || null;
    });
    NUMBER_FIELDS.forEach((field) => {
        const raw = document.getElementById(field).value;
        payload[field] = raw === '' ? null : Number(raw);
    });
    LIST_FIELDS.forEach((field) => {
        const values = textareaToArray(document.getElementById(field).value);
        payload[field] = values.length ? values : null;
    });

    const { error } = await supabase.from('profiles').upsert(payload);

    button.disabled = false;

    if (error) {
        status.textContent = error.message;
        status.classList.add('form-status-error');
        return;
    }

    status.textContent = 'Saved!';
});
