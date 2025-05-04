--- Single sensor dashboard 
select *
from heart_frequency
where is_valid is true  and sensor_id = '1'
order by registered_at desc

select *
from oxygen_saturation
where is_valid is true and sensor_id = '1'
order by registered_at desc

select *
from temperature 
where sensor_id = '1'
order by registered_at desc

SELECT ROUND(AVG(value),0) AS avg_oxygen
FROM oxygen_saturation
WHERE is_valid is true AND registered_at >= NOW() - INTERVAL '24 hour' AND sensor_id = '1'

SELECT  ROUND(AVG(value), 0) AS avg_heart_freq
FROM heart_frequency
WHERE is_valid is true AND registered_at >= NOW() - INTERVAL '24 hour' AND sensor_id = '1'

SELECT round(cast(AVG(value) as numeric),2) AS avg_temperature
FROM temperature
WHERE registered_at >= NOW() - INTERVAL '24 hour' AND sensor_id = '1'

--- Summary dashboard
select *
from heart_frequency
where is_valid is true
order by registered_at desc

select sensor_id, avg(value)
from heart_frequency
where is_valid is true
group by sensor_id

SELECT 
    o.sensor_id,
    AVG(o.value) AS avg_oxygen,
    AVG(t.value) AS avg_temperature,
    AVG(h.value) AS avg_heart_rate
FROM 
    oxygen_saturation o
JOIN 
    temperature t ON o.sensor_id = t.sensor_id
JOIN 
    heart_frequency h ON o.sensor_id = h.sensor_id
WHERE 
    o.is_valid = TRUE AND
    h.is_valid = TRUE AND
    o.registered_at >= NOW() - INTERVAL '1 hour' AND
    t.registered_at >= NOW() - INTERVAL '1 hour' AND
    h.registered_at >= NOW() - INTERVAL '1 hour'
GROUP BY 
    o.sensor_id;