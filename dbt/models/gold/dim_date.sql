-- A row for every day from 2016 to 2027, so charts never skip empty days.

with days as (
    select dateadd(day, seq4(), '2016-01-01'::date) as date_day
    from table(generator(rowcount => 4383))
)

select
    date_day,
    year(date_day)                       as year,
    quarter(date_day)                    as quarter,
    month(date_day)                      as month,
    date_trunc('month', date_day)::date  as month_start,
    dayofweekiso(date_day)               as iso_weekday,
    dayofweekiso(date_day) >= 6          as is_weekend
from days
