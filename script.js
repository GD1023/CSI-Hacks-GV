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

initTermsModal();
updateAuthNav();
supabase.auth.onAuthStateChange(() => updateAuthNav());
