import { supabase } from '../supabase-client.js';
import { fetchProfileFields, renderList, renderText, renderDocumentLink } from '../profile-view.js';
import { renderAdvice } from '../advice-client.js';

const { data: { session } } = await supabase.auth.getSession();

const profile = await fetchProfileFields(session.user.id, [
    'current_courses', 'completed_courses', 'ap_courses', 'remaining_requirements',
    'academic_strengths', 'academic_weaknesses', 'gpa', 'schedule_type',
    'max_courses_per_term', 'school_profile_link',
]);

renderList('pd-current-courses', profile.current_courses, 'No current courses added yet.');
renderList('pd-completed-courses', profile.completed_courses, 'No completed courses added yet.');
renderList('pd-ap-courses', profile.ap_courses, 'No AP courses added yet.');
renderList('pd-remaining-requirements', profile.remaining_requirements, 'No remaining requirements added yet.');
renderList('pd-academic-strengths', profile.academic_strengths, 'No strengths added yet.');
renderList('pd-academic-weaknesses', profile.academic_weaknesses, 'No weaknesses added yet.');
renderText('pd-gpa', profile.gpa, 'Not set');
renderText('pd-schedule-type', profile.schedule_type, 'Not set');
renderText('pd-max-courses', profile.max_courses_per_term, 'Not set');
await renderDocumentLink('pd-school-profile', profile.school_profile_link);
renderAdvice('ai-advice', 'courses');
