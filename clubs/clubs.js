import { supabase } from '../supabase-client.js';
import { fetchProfileFields, renderList } from '../profile-view.js';
import { renderAdvice } from '../advice-client.js';

const { data: { session } } = await supabase.auth.getSession();

const profile = await fetchProfileFields(session.user.id, ['clubs', 'leadership_roles']);

renderList('pd-clubs', profile.clubs, 'No clubs added yet.');
renderList('pd-leadership-roles', profile.leadership_roles, 'No leadership roles added yet.');
renderAdvice('ai-advice', 'clubs');
