import { supabase } from './supabase-client.js';

function initTermsGate() {
    const modal = document.getElementById('terms-modal');
    if (!modal) return;

    const form = document.querySelector('form.form-card');
    const checkbox = document.getElementById('terms-checkbox');
    const acceptBtn = document.getElementById('terms-accept');
    if (!form || !checkbox || !acceptBtn) return;

    let accepted = false;

    checkbox.addEventListener('change', () => {
        acceptBtn.disabled = !checkbox.checked;
    });

    // Runs before login.js/signup.js's own submit handler (script.js loads first),
    // so the first click is intercepted and the real submit only happens after accepting.
    form.addEventListener('submit', (e) => {
        if (!accepted) {
            e.preventDefault();
            e.stopImmediatePropagation();
            modal.classList.remove('modal-hidden');
        }
    });

    acceptBtn.addEventListener('click', () => {
        accepted = true;
        modal.classList.add('modal-hidden');
        form.requestSubmit();
    });
}

async function updateAuthNav() {
    const container = document.getElementById('nav-auth');
    const restrictedLinks = document.querySelectorAll('.nav-restricted');

    const { data: { session } } = await supabase.auth.getSession();

    restrictedLinks.forEach((link) => {
        link.style.display = session ? 'inline' : 'none';
    });

    if (!container) return;

    if (session) {
        container.innerHTML = `
            <span class="nav-user">${session.user.email}</span>
            <a href="/profile">Profile</a>
            <a href="#" id="nav-logout">Sign Out</a>
        `;
        document.getElementById('nav-logout').addEventListener('click', async (e) => {
            e.preventDefault();
            await supabase.auth.signOut();
            window.location.href = '/';
        });
    } else {
        container.innerHTML = `
            <a href="/login">Login</a>
            <a href="/signup">Sign Up</a>
        `;
    }
}

initTermsGate();
updateAuthNav();
supabase.auth.onAuthStateChange(() => updateAuthNav());
