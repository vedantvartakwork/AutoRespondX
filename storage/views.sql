-- AutoRespondX PostgreSQL Views

-- 1. Label summary: count by predicted_label
drop view if exists vw_label_summary;
create or replace view vw_label_summary as
select
    predicted_label,
    count(*) as total_count
from processed_tweets
group by predicted_label
order by total_count desc;

-- 2. Duplicate summary: exact, near, total
drop view if exists vw_duplicate_summary;
create or replace view vw_duplicate_summary as
select
    sum(case when is_duplicate then 1 else 0 end) as exact_duplicates,
    sum(case when is_near_duplicate then 1 else 0 end) as near_duplicates,
    count(*) as total_rows
from processed_tweets;

-- 3. Recent processed tweets
drop view if exists vw_recent_processed;
create or replace view vw_recent_processed as
select
    id,
    original_tweet,
    predicted_label,
    confidence,
    is_duplicate,
    is_near_duplicate,
    reply_text,
    created_at
from processed_tweets
order by created_at desc
limit 20;

-- 4. Recent reply outbox
drop view if exists vw_recent_outbox;
create or replace view vw_recent_outbox as
select
    id,
    processed_tweet_id,
    reply_text,
    reply_status,
    created_at
from reply_outbox
order by created_at desc
limit 20;

-- 5. Recent metrics
drop view if exists vw_recent_metrics;
drop view if exists vw_recent_metrics;
create or replace view vw_recent_metrics as
select
    id,
    metric_name,
    metric_value,
    batch_id,
    created_at
from metrics
order by created_at desc
limit 20;

-- 6. Complaint spike: count of 'complaint' in last 20 processed_tweets
drop view if exists vw_complaint_spike;
create or replace view vw_complaint_spike as
select
    count(*) as complaint_count_last_20
from (
    select predicted_label
    from processed_tweets
    order by created_at desc
    limit 20
) t
where predicted_label = 'complaint';
