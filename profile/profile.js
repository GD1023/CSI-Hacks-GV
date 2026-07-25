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

// Plain text/select columns, read and written as-is. transcript_link and
// school_profile_link are handled separately below -- they hold a Storage
// path (populated by uploading a PDF), not free text.
const TEXT_FIELDS = [
    'name', 'grade', 'school', 'school_type', 'interests', 'time_commitments',
    'counselor_name', 'working_style', 'college_preferences', 'personal_narrative',
    'additional_notes', 'schedule_type', 'competition_team_preference',
    'travel_constraints', 'budget_constraints', 'portfolio_link',
];

const ALL_FIELDS = [...TEXT_FIELDS, ...NUMBER_FIELDS, ...LIST_FIELDS, 'transcript_link', 'school_profile_link'];

// Transcript/school-profile PDFs live in a private Storage bucket, one file
// per user per kind, at "<user_id>/<kind>.pdf" (upsert on re-upload). The
// profiles columns store that path, and we turn it into a short-lived signed
// URL on read since the bucket isn't public.
const DOCUMENT_BUCKET = 'profile-documents';
const MAX_FILE_BYTES = 10 * 1024 * 1024; // 10MB
const DOCUMENTS = [
    { kind: 'transcript', column: 'transcript_link', fileInputId: 'transcript_file', currentLabelId: 'transcript_current' },
    { kind: 'school-profile', column: 'school_profile_link', fileInputId: 'school_profile_file', currentLabelId: 'school_profile_current' },
];

function arrayToTextarea(value) {
    return Array.isArray(value) ? value.join('\n') : '';
}

function textareaToArray(value) {
    return value
        .split('\n')
        .map((line) => line.trim())
        .filter((line) => line.length > 0);
}

async function showCurrentDocument(path, currentLabelId) {
    const label = document.getElementById(currentLabelId);
    if (!path) {
        label.textContent = 'No file uploaded yet.';
        return;
    }
    const { data, error } = await supabase.storage
        .from(DOCUMENT_BUCKET)
        .createSignedUrl(path, 60 * 60);
    if (error || !data) {
        label.textContent = 'A file is on record, but the link could not be generated right now.';
        return;
    }
    label.innerHTML = '';
    const link = document.createElement('a');
    link.href = data.signedUrl;
    link.target = '_blank';
    link.rel = 'noopener';
    link.textContent = 'View current file';
    label.append(link);
}

async function uploadDocument(file, kind) {
    const path = `${user.id}/${kind}.pdf`;
    const { error } = await supabase.storage
        .from(DOCUMENT_BUCKET)
        .upload(path, file, { upsert: true, contentType: 'application/pdf' });
    if (error) throw error;
    return path;
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
    DOCUMENTS.forEach((doc) => {
        showCurrentDocument(profile[doc.column], doc.currentLabelId);
    });
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    status.textContent = 'Saving...';
    status.classList.remove('form-status-error');
    button.disabled = true;

    // Only upload (and only include in the payload) a document whose file
    // input actually has a new file selected -- file inputs can't be
    // pre-filled, so an empty input here just means "no change," not "clear
    // the existing file."
    const uploadedPaths = {};

    for (const doc of DOCUMENTS) {
        const file = document.getElementById(doc.fileInputId).files[0];
        if (!file) continue;

        if (file.size > MAX_FILE_BYTES) {
            status.textContent = `${file.name} is larger than 10MB. Please upload a smaller PDF.`;
            status.classList.add('form-status-error');
            button.disabled = false;
            return;
        }

        try {
            uploadedPaths[doc.column] = await uploadDocument(file, doc.kind);
        } catch (uploadError) {
            status.textContent = uploadError.message;
            status.classList.add('form-status-error');
            button.disabled = false;
            return;
        }
    }

    const payload = { id: user.id, ...uploadedPaths };

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

    DOCUMENTS.forEach((doc) => {
        if (uploadedPaths[doc.column]) {
            showCurrentDocument(uploadedPaths[doc.column], doc.currentLabelId);
        }
    });

    status.textContent = 'Saved!';
});
