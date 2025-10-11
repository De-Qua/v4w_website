# PREPARING POSTGRES for DEQUA

## POPULATING THE DATABASES from FILES

This section is to populate the database from the Opendata that we have collected (they are on lanassa's cloud)

#### pre-requisites
assuming you have Postgres (with postGIS) installed,
you should just access postgres command line with `psql`

### 1. CREATE THE DATABASES

Once you are in the postgres CLI, run

```
CREATE DATABASE opendata_ve_pg;
CREATE DATABASE dequa_collected_data;
CREATE DATABASE dequa_config_data;
CREATE DATABASE dequa_internal;
```

*WARNING:* this creates the databases, not the tables.
The tables will be created for example using `db.create_all(bind="..")` in python or from flask shell. See below for more information

### 2. CREATE THE TABLES

For the default settings/values, you can use these scripts:

- For the tables in `opendata_ve_pg` you can use the python script `populate_db_v2.py`. Run it and it will ask you questions.
- The tables in `dequa_internal` should be created from the first execution of flask run, as described in `flask_app.py` (otherwise `db.create_all(bind="internal")`)
- The tables in `dequa_collected_data` should be initiated using `setup_db_collected_data.py`
- The tables in `dequa_config_data` can be loaded using `setup_db_config.py`

## TRANSFERRING DB TO ANOTHER MACHINE (A to B)

This section is if you have the DB operative on your machine and you want to move it to the next one (local to staging, staging to production)

### 1. DUMPING THE DATABASES (machine A)

This has to be done on the machine where postgres is working and the databases are full

```
pg_dump -h 127.0.0.1 -p 5432 --no-owner --no-privileges dequa_internal > internal.sql
pg_dump -h 127.0.0.1 -p 5432 --no-owner --no-privileges dequa_config_data > config.sql
pg_dump -h 127.0.0.1 -p 5432 --no-owner --no-privileges dequa_collected_data > collected.sql
pg_dump -h 127.0.0.1 -p 5432 --no-owner --no-privileges opendata_ve_pg > opendata.sql
```

### 2. CREATING THE DATABASES (machine B)

This has to be done on the new machine where postgres is working, but the databases are empty

```
CREATE DATABASE opendata_ve_pg;
CREATE DATABASE dequa_collected_data;
CREATE DATABASE dequa_config_data;
CREATE DATABASE dequa_internal;
```

### 3. FILLING THE DATABASES (machine B)

This has to be done on the new machine where postgres is working, but the databases are empty

```
psql -f opendata.sql opendata_ve_pg
psql -f internal.sql dequa_internal
psql -f collected.sql dequa_collected_data
psql -f config.sql dequa_config_data
```

## Docker version

### Setup database

```bash
docker compose up -d
```

### Restore database

```bash
docker cp ./db/db_dump/opendata.sql dq_postgres:/tmp/ 

docker exec -it dq_postgres psql -U dequa -f /tmp/opendata.sql opendata_ve_pg
```