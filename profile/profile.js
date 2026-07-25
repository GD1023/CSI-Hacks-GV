import { supabase } from '../supabase-client.js';

const { data: { session } } = await supabase.auth.getSession();
const user = session.user;

const form = document.getElementById('profile-form');
const status = document.getElementById('profile-status');
const button = form.querySelector('button[type="submit"]');

document.getElementById('email').value = user.email;

const { data: profile, error: fetchError } = await supabase
    .from('profiles')
    .select('name, grade, school, interests')
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
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    status.textContent = 'Saving...';
    status.classList.remove('form-status-error');
    button.disabled = true;

    const { error } = await supabase.from('profiles').upsert({
        id: user.id,
        name: document.getElementById('name').value,
        grade: document.getElementById('grade').value,
        school: document.getElementById('school').value,
        interests: document.getElementById('interests').value,
    });

    button.disabled = false;

    if (error) {
        status.textContent = error.message;
        status.classList.add('form-status-error');
        return;
    }

    status.textContent = 'Saved!';
});
