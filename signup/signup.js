import { supabase } from '../supabase-client.js';

const form = document.getElementById('signup-form');
const status = document.getElementById('signup-status');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    status.textContent = 'Creating your account...';
    status.classList.remove('form-status-error');

    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const { error } = await supabase.auth.signUp({
        email,
        password,
        options: { data: { name } }
    });

    if (error) {
        status.textContent = error.message;
        status.classList.add('form-status-error');
        return;
    }

    status.textContent = 'Account created! Check your email to confirm before logging in.';
    form.reset();
});
