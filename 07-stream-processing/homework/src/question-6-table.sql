CREATE TABLE max_tip_per_hour (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    total_tip_amount DOUBLE PRECISION,
    PRIMARY KEY (window_start, window_end)
);