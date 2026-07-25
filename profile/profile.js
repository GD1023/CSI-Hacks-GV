import { supabase } from '../supabase-client.js';

const { data: { session } } = await supabase.auth.getSession();
const user = session.user;

const form = document.getElementById('profile-form');
const status = document.getElementById('profile-status');
const button = form.querySelector('button[type="submit"]');

document.getElementById('email').value = user.email;

const { data: profile, error: fetchError } = await supabase
    .from('profiles')
    .select('name, grade, school, interests, gpa, transcript_link')
    .eq('id', user.id)
    .maybeSingle();

if (fetchError) {
    status.textContent = fetchError.message;
    status.classList.add('form-status-error');
} else if (profile) {
    document.getElementById('name').value = profile.name || '';
    document.getElementById('grade').value = profile.grade || '';
    document.getElementById('school').value = profile.school || '';
    document.getElementById('interests').value = profile.interests || '';
    document.getElementById('gpa').value = profile.gpa ?? '';
    document.getElementById('transcript_link').value = profile.transcript_link || '';
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    status.textContent = 'Saving...';
    status.classList.remove('form-status-error');
    button.disabled = true;

    const gpaValue = document.getElementById('gpa').value;

    const { error } = await supabase.from('profiles').upsert({
        id: user.id,
        name: document.getElementById('name').value,
        grade: document.getElementById('grade').value,
        school: document.getElementById('school').value,
        interests: document.getElementById('interests').value,
        gpa: gpaValue === '' ? null : Number(gpaValue),
        transcript_link: document.getElementById('transcript_link').value,
    });

    button.disabled = false;

    if (error) {
        status.textContent = error.message;
        status.classList.add('form-status-error');
        return;
    }

    status.textContent = 'Saved!';
});
