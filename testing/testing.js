import { supabase } from '../supabase-client.js';
import { fetchProfileFields, renderText } from '../profile-view.js';
import { renderAdvice } from '../advice-client.js';

const { data: { session } } = await supabase.auth.getSession();

const profile = await fetchProfileFields(session.user.id, ['sat_score', 'act_score', 'psat_score']);

renderText('pd-sat', profile.sat_score, 'Not set');
renderText('pd-act', profile.act_score, 'Not set');
renderText('pd-psat', profile.psat_score, 'Not set');
renderAdvice('ai-advice', 'testing');
