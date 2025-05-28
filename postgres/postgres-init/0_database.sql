CREATE USER api_management WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE api_management_db TO api_management;

SELECT 'CREATE DATABASE kong_db' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'kong_db')\gexec
GRANT ALL PRIVILEGES ON DATABASE kong_db TO api_management;

SELECT 'CREATE DATABASE user_service_db' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'user_service_db')\gexec
GRANT ALL PRIVILEGES ON DATABASE user_service_db TO api_management;