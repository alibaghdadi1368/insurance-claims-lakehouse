SELECT
    pc4,
    municipality,
    gm_code,
    urbanity_level,
    CASE urbanity_level
        WHEN 1 THEN 'Very strongly urban'
        WHEN 2 THEN 'Strongly urban'
        WHEN 3 THEN 'Moderately urban'
        WHEN 4 THEN 'Hardly urban'  
        ELSE  'Not urban'
    END as urbanity_label,
    avg_woz_k_eur
FROM {{ ref('stg_postcodes') }}