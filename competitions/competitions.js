import { supabase } from '../supabase-client.js';
import { fetchProfileFields, renderList, renderText } from '../profile-view.js';

const { data: { session } } = await supabase.auth.getSession();

const profile = await fetchProfileFields(session.user.id, [
    'honors_awards', 'competition_history', 'competition_hours_per_week',
    'competition_team_preference', 'travel_constraints', 'budget_constraints',
]);

renderList('pd-honors-awards', profile.honors_awards, 'No honors or awards added yet.');
renderList('pd-competition-history', profile.competition_history, 'No competition history added yet.');
renderText('pd-competition-hours', profile.competition_hours_per_week, 'Not set');
renderText('pd-competition-team-pref', profile.competition_team_preference, 'Not set');
renderText('pd-travel-constraints', profile.travel_constraints, 'Not set');
renderText('pd-budget-constraints', profile.budget_constraints, 'Not set');
