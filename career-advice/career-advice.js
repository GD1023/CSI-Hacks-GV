import { supabase } from '../supabase-client.js';

// Points at the Flask backend (app.py) run locally during development --
// update this once the backend has a real deployed URL.
const API_BASE = 'http://localhost:5000';

const SECTIONS = [
    { key: 'courses', title: 'Courses & Rigor' },
    { key: 'clubs', title: 'Clubs & Involvement' },
    { key: 'competitions', title: 'Competitions & Awards' },
    { key: 'testing', title: 'Testing & College Prep' },
    { key: 'career', title: 'Career Fit' },
    { key: 'college_prep', title: 'College Prep' },
];

const card = document.getElementById('advice-card');

function renderError(message) {
    card.innerHTML = `<h3>Something went wrong</h3><p>${message}</p>`;
}

function renderAdvice(advice) {
    card.innerHTML = SECTIONS.map(({ key, title }) => `
        <h3>${title}</h3>
        <p>${advice[key] || 'No guidance yet -- fill out more of your profile for a sharper read on this.'}</p>
    `).join('');
}

const { data: { session } } = await supabase.auth.getSession();

if (!session) {
    renderError('Please log in to see your personalized feedback.');
} else {
    try {
        const response = await fetch(`${API_BASE}/advice`, {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${session.access_token}`,
            },
        });

        const body = await response.json();

        if (!response.ok) {
            renderError(body.error || 'Please try again later.');
        } else if (body.raw) {
            // Model didn't return valid JSON -- show the raw text rather than nothing.
            card.innerHTML = `<h3>Your feedback</h3><p>${body.raw}</p>`;
        } else {
            renderAdvice(body);
        }
    } catch (err) {
        renderError('Could not reach the advice service. Is the backend running?');
    }
}
