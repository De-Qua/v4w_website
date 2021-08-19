# PREPARING POSTGRES for DEQUA

Some helpful commands to prepare for the dequa backend once you installed postgres and postgis.

#### pre-requisites
assuming you have Postgres (with postGIS) installed,
you should just access postgres command line with `psql`

### 1. CREATE THE DABASES

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
- The tables in `dequa_collected_data` should be empty at the beginning, as the name suggests.
- The tables in `dequa_config_data` can be loaded using `setup_bd_config.py`
