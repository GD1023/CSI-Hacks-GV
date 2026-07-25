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

function initActiveNavLink() {
    const path = window.location.pathname.replace(/\/index\.html$/, '').replace(/\/$/, '') || '/';

    document.querySelectorAll('.site-header nav > a[href]').forEach((link) => {
        const href = link.getAttribute('href').replace(/\/$/, '') || '/';
        if (href === path) {
            link.classList.add('nav-current');
        }
    });
}

function initScrollReveal() {
    const elements = document.querySelectorAll(
        '.card, .hero, .veer, .geetansh, .locked-card, .form-card'
    );
    if (!elements.length) return;

    if (!('IntersectionObserver' in window)) {
        elements.forEach((el) => el.classList.add('is-visible'));
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    elements.forEach((el, i) => {
        el.classList.add('reveal');
        el.style.transitionDelay = `${Math.min(i, 6) * 60}ms`;
        observer.observe(el);
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
initActiveNavLink();
initScrollReveal();
updateAuthNav();
supabase.auth.onAuthStateChange(() => updateAuthNav());
