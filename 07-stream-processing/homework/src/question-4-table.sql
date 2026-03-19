CREATE TABLE processed_events_aggregated (
     window_start TIMESTAMP,
     PULocationID INTEGER,
     num_trips BIGINT,
     PRIMARY KEY (window_start, PULocationID)
 );