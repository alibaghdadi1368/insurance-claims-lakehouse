-- unpacks the JSON and is incremental
-- Claim events out of their JSON, one row per event, duplicates removed.
-- Incremental: each run only reads rows that arrived in Bronze since the last run.
{{ config(materialized='incremental', unique_key='event_id') }}

with events as (
    SELECT
        event:event_id::string as event_id,
        event:event_type::string                   as event_type,
        event:event_ts::timestamp_ntz              as event_ts,
        event:claim_id::string                     as claim_id,
        event:policy_id::string                    as policy_id,
        event:payload:claim_type::string           as claim_type,
        event:payload:incident_date::date          as incident_date,
        event:payload:channel::string              as channel,
        event:payload:claimed_amount::number(12,2)  as claimed_amount,
        event:payload:assessed_amount::number(12,2) as assessed_amount,
        event:payload:approved_amount::number(12,2) as approved_amount,
        event:payload:paid_amount::number(12,2)     as paid_amount,
        event:payload:reason::string               as rejection_reason,
        _loaded_at
    from {{ source('bronze', 'raw_claim_events') }}
    {% if is_incremental() %}
    where _loaded_at > (select max(_loaded_at) from {{ this }})
    {% endif %}
)

-- Kafka is at-least-once: keep the first copy of every event
SELECT *
FROM events
qualify row_number() OVER(PARTITION BY event_id ORDER BY _loaded_at) = 1