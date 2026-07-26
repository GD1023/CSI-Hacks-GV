import { supabase } from './supabase-client.js';

const API_BASE = ['localhost', '127.0.0.1'].includes(window.location.hostname)
    ? 'http://localhost:5000'
    : 'https://high-school-compass-api.onrender.com';

const CACHE_KEY = 'hsc_advice_cache';

// Keys the backend is expected to return. If a cached response is missing
// one (e.g. it was cached before a new section was added server-side), treat
// it as stale and refetch instead of serving an incomplete cached response.
const EXPECTED_KEYS = ['testing', 'clubs', 'extracurriculars', 'competitions', 'courses', 'career', 'college_prep'];

function isFreshAdvice(advice) {
    if (!advice) return false;
    if (advice.raw) return true;
    return EXPECTED_KEYS.every((key) => key in advice);
}

// One /advice call covers every section -- cache it per browser session so
// navigating between tabs doesn't re-trigger the LLM call each time.
export async function getAdvice() {
    const cached = sessionStorage.getItem(CACHE_KEY);
    if (cached) {
        try {
            const parsed = JSON.parse(cached);
            if (isFreshAdvice(parsed)) return parsed;
        } catch {
            // corrupted cache entry -- fall through and refetch
        }
    }

    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Please log in to see your personalized feedback.');

    const response = await fetch(`${API_BASE}/advice`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${session.access_token}` },
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || 'Please try again later.');

    sessionStorage.setItem(CACHE_KEY, JSON.stringify(body));
    return body;
}

export async function renderAdvice(containerId, key) {
    const container = document.getElementById(containerId);
    if (!container) return;
    try {
        const advice = await getAdvice();
        container.textContent = advice[key] || advice.raw || 'No guidance yet -- fill out more of your profile for a sharper read on this.';
    } catch (err) {
        container.textContent = err.message;
    }
}
