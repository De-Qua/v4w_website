
To start a freshly new database:

1. Start the postgres container 
```
docker compose up -d
```
It will automatically create the databases with postgis extensions in some of them

2. From the main flask folder run the alembic upgrade
```
flask db upgrade
```
It will create all the tables and relationships

3. From the db folder restore all the data
```
./restore_data.sh
```
It will restore all the data

If you want to dump all the data it is necessary to dump with the `data-only` flag! Otherwise there are problems with alembic since it will delete and recreate all the tables!
If you want you can run the script
```
./restore_data.sh
```
which will dump all the data of the different databases in the folder `db_dump`!

Evviva!


TODO
install functions
in opendata CREATE EXTENSION pg_trgm;