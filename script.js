import { supabase } from './supabase-client.js';

function initTermsModal() {
    const modal = document.getElementById('terms-modal');
    if (!modal) return;

    const checkbox = document.getElementById('terms-checkbox');
    const acceptBtn = document.getElementById('terms-accept');

    checkbox.addEventListener('change', () => {
        acceptBtn.disabled = !checkbox.checked;
    });

    acceptBtn.addEventListener('click', () => {
        modal.classList.add('modal-hidden');
    });
}

function initNavAuth() {
    const navAuth = document.getElementById('nav-auth');
    const restrictedLinks = document.querySelectorAll('.nav-restricted');

    function applyAuthState(session) {
        restrictedLinks.forEach((link) => {
            link.style.display = session ? 'inline' : 'none';
        });

        if (!navAuth) return;

        if (session) {
            navAuth.innerHTML = '<a href="#" id="logout-link">Log Out</a>';
            document.getElementById('logout-link').addEventListener('click', async (e) => {
                e.preventDefault();
                await supabase.auth.signOut();
                window.location.href = '/';
            });
        } else {
            navAuth.innerHTML = '<a href="/login">Login</a><a href="/signup">Sign Up</a>';
        }
    }

    supabase.auth.getSession().then(({ data: { session } }) => applyAuthState(session));
    supabase.auth.onAuthStateChange((_event, session) => applyAuthState(session));
}

initTermsModal();
initNavAuth();
