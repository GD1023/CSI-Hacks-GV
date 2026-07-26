import { supabase } from '../supabase-client.js';
import { fetchProfileFields, renderList, renderText, renderMaybeLink, renderDocumentLink } from '../profile-view.js';
import { renderAdvice } from '../advice-client.js';

const { data: { session } } = await supabase.auth.getSession();

const profile = await fetchProfileFields(session.user.id, [
    'college_list', 'college_preferences', 'counselor_name', 'portfolio_link', 'transcript_link',
]);

renderList('pd-college-list', profile.college_list, 'No colleges added yet.');
renderText('pd-college-preferences', profile.college_preferences, 'Not set');
renderText('pd-counselor-name', profile.counselor_name, 'Not set');
renderMaybeLink('pd-portfolio-link', profile.portfolio_link, 'Not set');
await renderDocumentLink('pd-transcript-link', profile.transcript_link);
renderAdvice('ai-advice', 'college_prep');
