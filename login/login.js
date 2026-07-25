import { supabase } from '../supabase-client.js';

const form = document.getElementById('login-form');
const status = document.getElementById('login-status');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    status.textContent = 'Logging in...';
    status.classList.remove('form-status-error');

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const { error } = await supabase.auth.signInWithPassword({ email, password });

    if (error) {
        status.textContent = error.message;
        status.classList.add('form-status-error');
        return;
    }

    window.location.href = '/';
});
