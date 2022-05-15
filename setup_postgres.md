# Setting up Postgres

The steps are:

- [install dependencies](#install_dependencies)
- [create user/role](#create_role)
- [create databases](#create_databases)
- [create and fill tables](#create_and_fill_tables)


## Install dependencies
First install postgres and postgis. On ubuntu

`sudo apt install postgres`

It would be better to have a postgres version >= 13. Then install the according postgis

`sudo apt install postgres-14-postgis`

If you have postgres 13, change the command.
If you install using only `sudo apt install postgis` it may automatically install an old version of postgres (9.6 usually, the minimum requirement) and install the extension on that version. You can check the extensions in `/usr/share/postgres/14/extensions` and you should see a lot of postgis symlinks (if they are in `/usr/share/postgres/9.6/extensions`, you know they are attached to the wrong postgres installation)

##### Other pip dependencies

Maybe some sql/geo/alchemy packages.

`pip install geoalchemy2`


## Create role
Once you installed postgres, you can enter with the command line tool `psql`.
If you try to enter and it says that your role does not exist, you have to creat it.
Postgres automatically creates a `postgres` role, so you can enter by `psql postgres` or with `sudo su -u postgres` and then `psql`.
Once you entered as postgres, you create your own role with:

`CREATE ROLE yourname WITH SUPERUSER CREATEDB CREATEROLE LOGIN ENCRYPTED PASSWORD 'alphapw';`

changing yourname with your user name and password with a better one.
If you type `\du` in the psql shell, you should get a list of roles with the attributes.

## Create databases
For the backend, we need 4 databases (which inside will have other tables).
You can either create them manually in the `psql` shell, or launch the .sql file provided with

`psql -f create_dbs.sql`

that should create the 4 databases.

Enable postgis on the opendata_ve_pg database with (not sure how to do it from the sql file)

`psql -d opendata_ve_pg -c 'CREATE EXTENSION postgis;'`

If some are missing, check in `config.py` if the names changed.

## Create and fill tables
Run the python script

`python populate_db_v2.py`

## Troubleshooting
Error:
`ImportError: cannot import name 'get_raw_jwt' from 'flask_jwt_extended'` or

`ImportError:cannot import name 'verify_jwt_in_request' from 'flask_jwt_extended'`

Downgrade flask-jwt-extended: `pip install Flask-JWT-Extended==3.19`

------------------
Error:
`ImportError: cannot import name 'safe_str_cmp' from 'werkzeug.security'`

Downgrade werkzeug: `pip install Werkzeug==2.0.0`
and jinja: `pip install jinja2==3.0.3`


------------------
Error:
`sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedObject) type "geometry" does not exist`

Enable postgis on the opendata_ve_pg database with (not sure how to do it from the sql file)

`psql -d opendata_ve_pg -c 'CREATE EXTENSION postgis;'`
