import { supabase } from '../supabase-client.js';
import { fetchProfileFields, renderList, renderText } from '../profile-view.js';

const { data: { session } } = await supabase.auth.getSession();

const profile = await fetchProfileFields(session.user.id, ['intended_majors', 'interest_areas', 'working_style']);

renderList('pd-intended-majors', profile.intended_majors, 'No intended majors added yet.');
renderList('pd-interest-areas', profile.interest_areas, 'No interest areas added yet.');
renderText('pd-working-style', profile.working_style, 'Not set');
