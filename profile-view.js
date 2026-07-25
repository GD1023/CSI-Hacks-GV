import { supabase } from './supabase-client.js';

// Shared read-side helpers for pages that display data the user entered on
// the profile page (courses, extracurriculars, awards, etc). Mirrors the
// column names and storage layout profile.js writes to.
const DOCUMENT_BUCKET = 'profile-documents';

export async function fetchProfileFields(userId, columns) {
    const { data, error } = await supabase
        .from('profiles')
        .select(columns.join(', '))
        .eq('id', userId)
        .maybeSingle();
    if (error) throw error;
    return data || {};
}

export function renderList(containerId, items, emptyText = 'Nothing added to your profile yet.') {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';

    if (!items || !items.length) {
        const p = document.createElement('p');
        p.className = 'profile-data-empty';
        p.textContent = emptyText;
        container.append(p);
        return;
    }

    const ul = document.createElement('ul');
    ul.className = 'profile-data-list';
    items.forEach((item) => {
        const li = document.createElement('li');
        li.textContent = item;
        ul.append(li);
    });
    container.append(ul);
}

export function renderText(containerId, value, emptyText = 'Not set') {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.textContent = (value === null || value === undefined || value === '') ? emptyText : String(value);
}

export function renderMaybeLink(containerId, value, emptyText = 'Not set') {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';

    if (!value) {
        container.textContent = emptyText;
        return;
    }

    if (!/^https?:\/\//i.test(value)) {
        container.textContent = value;
        return;
    }

    const link = document.createElement('a');
    link.href = value;
    link.target = '_blank';
    link.rel = 'noopener';
    link.textContent = value;
    container.append(link);
}

export async function renderDocumentLink(containerId, path, emptyText = 'No file uploaded yet.') {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!path) {
        container.textContent = emptyText;
        return;
    }

    const { data, error } = await supabase.storage
        .from(DOCUMENT_BUCKET)
        .createSignedUrl(path, 60 * 60);

    if (error || !data) {
        container.textContent = 'A file is on record, but the link could not be generated right now.';
        return;
    }

    container.innerHTML = '';
    const link = document.createElement('a');
    link.href = data.signedUrl;
    link.target = '_blank';
    link.rel = 'noopener';
    link.textContent = 'View file';
    container.append(link);
}
