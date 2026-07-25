import { supabase } from './supabase-client.js';

async function updateAuthNav() {
    const container = document.getElementById('nav-auth');
    if (!container) return;

    const { data: { session } } = await supabase.auth.getSession();

    if (session) {
        container.innerHTML = `
            <span class="nav-user">${session.user.email}</span>
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

updateAuthNav();
supabase.auth.onAuthStateChange(() => updateAuthNav());
