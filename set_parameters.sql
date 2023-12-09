ALTER SYSTEM SET shared_buffers TO '4GB';
ALTER SYSTEM SET work_mem TO '8MB';
ALTER SYSTEM SET effective_cache_size TO '8GB';
ALTER SYSTEM SET maintenance_work_mem TO '1GB';
ALTER SYSTEM SET checkpoint_completion_target TO '0.9';
ALTER SYSTEM SET autovacuum TO 'on';

