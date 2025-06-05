SELECT 'CREATE DATABASE api_management_db' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'api_management_db')\gexec

SELECT 'CREATE DATABASE kong_db' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'kong_db')\gexec

SELECT 'CREATE DATABASE user_service_db' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'user_service_db')\gexec

SELECT 'CREATE DATABASE vendor_service_db' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'vendor_service_db')\gexec

SELECT 'CREATE DATABASE event_service_db' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'event_service_db')\gexec