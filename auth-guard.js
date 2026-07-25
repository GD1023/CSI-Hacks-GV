import { supabase } from './supabase-client.js';

const { data: { session } } = await supabase.auth.getSession();

if (!session) {
    window.location.href = '/login';
} else {
    document.body.classList.remove('gated');
}
