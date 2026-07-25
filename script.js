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

function initTermsModal() {
    const modal = document.getElementById('terms-modal');
    if (!modal) return;

    const scrollBox = document.getElementById('terms-scroll');
    const checkbox = document.getElementById('terms-checkbox');
    const acceptBtn = document.getElementById('terms-accept');

    function checkScrolled() {
        const reachedBottom = scrollBox.scrollTop + scrollBox.clientHeight >= scrollBox.scrollHeight - 10;
        if (reachedBottom) {
            checkbox.disabled = false;
        }
    }

    scrollBox.addEventListener('scroll', checkScrolled);
    checkbox.addEventListener('change', () => {
        acceptBtn.disabled = !checkbox.checked;
    });
    acceptBtn.addEventListener('click', () => {
        modal.classList.add('modal-hidden');
    });

    // Handles the case where the summary already fits without scrolling.
    checkScrolled();
}

updateAuthNav();
supabase.auth.onAuthStateChange(() => updateAuthNav());
initTermsModal();
