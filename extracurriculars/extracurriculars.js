import { supabase } from '../supabase-client.js';
import { fetchProfileFields, renderList, renderText } from '../profile-view.js';

const { data: { session } } = await supabase.auth.getSession();

const profile = await fetchProfileFields(session.user.id, [
    'extracurriculars', 'work_experience', 'volunteer_experience', 'time_commitments',
]);

renderList('pd-extracurriculars', profile.extracurriculars, 'No extracurriculars added yet.');
renderList('pd-work-experience', profile.work_experience, 'No work experience added yet.');
renderList('pd-volunteer-experience', profile.volunteer_experience, 'No volunteer experience added yet.');
renderText('pd-time-commitments', profile.time_commitments, 'Not set');
