-- Ensure no duplicate (user_id, project_id) pairs in recommendations
select user_id, project_id, count(*) as cnt
from {{ ref('match_user_recommendation') }}
group by user_id, project_id
having count(*) > 1
