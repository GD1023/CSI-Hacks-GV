import { supabase } from '../supabase-client.js';

const form = document.getElementById('login-form');
const status = document.getElementById('login-status');
const button = form.querySelector('button[type="submit"]');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    status.textContent = 'Logging in...';
    status.classList.remove('form-status-error');
    button.disabled = true;

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const { error } = await supabase.auth.signInWithPassword({ email, password });

    if (error) {
        status.classList.add('form-status-error');
        button.disabled = false;

        if (error.message === 'Email not confirmed') {
            status.textContent = '';
            status.append('Email not confirmed. Check your inbox (and spam folder) for the confirmation link, or ');
            const resendLink = document.createElement('a');
            resendLink.href = '#';
            resendLink.textContent = 'resend the email';
            resendLink.addEventListener('click', async (evt) => {
                evt.preventDefault();
                status.textContent = 'Resending...';
                status.classList.remove('form-status-error');
                const { error: resendError } = await supabase.auth.resend({ type: 'signup', email });
                if (resendError) {
                    status.textContent = resendError.message;
                    status.classList.add('form-status-error');
                } else {
                    status.textContent = 'Confirmation email sent. Check your inbox.';
                }
            });
            status.append(resendLink);
            status.append('.');
        } else {
            status.textContent = error.message;
        }
        return;
    }

    window.location.href = '/';
});
