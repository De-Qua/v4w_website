-- Create all databases
CREATE DATABASE opendata_ve_pg;
CREATE DATABASE dequa_config_data;
CREATE DATABASE dequa_collected_data;
CREATE DATABASE dequa_internal;
CREATE DATABASE dequa_geotag;
CREATE DATABASE dequa_data_versions;

-- Enable PostGIS on specific databases
\connect opendata_ve_pg;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

\connect dequa_geotag;
CREATE EXTENSION IF NOT EXISTS postgis;