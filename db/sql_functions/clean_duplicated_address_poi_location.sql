-- >> STEP 1 DELETE POI
create temp table poi_to_delete (id int);

insert
	into
	poi_to_delete (id)
select
	p.id
from
	(
	select
		max(id) as maxid,
		address_street,
		count(*)
	from
		address a
	group by
		address_street
	having
		count(*)= 2
) as q
inner join address a2 on
	a2.id = q.maxid
left outer join poi p on
	p.location_id = a2.location_id
where
	p.id is not null;
-- DELETE POI TYPES
delete
from
	poi_types pt
where
	pt.poi_id in (
	select
		id
	from
		poi_to_delete);
-- DELETE POI
delete
from
	poi p
where
	p.id in (
	select
		id
	from
		poi_to_delete);
-- DROP TEMP TABLE
drop table poi_to_delete;
-- >> STEP 2.1 DELETE ADDRESS
create temp table address_to_delete (add_id int,
loc_id int);

insert
	into
	address_to_delete (add_id,
	loc_id)
select
	a2.id,
	a2.location_id
from
	(
	select
		max(id) as maxid,
		address_street,
		count(*)
	from
		address a
	group by
		address_street
	having
		count(*)>1
) as q
inner join address a2 on
	a2.id = q.maxid;
	-- DELETE ADDRESS
delete
from
	address a
where
	a.id in (
	select
		add_id
	from
		address_to_delete);
	-- DROP TEMP TABLE
drop table address_to_delete;
	-- >> STEP 2.2 DELETE ADDRESS
create temp table address_to_delete (add_id int,
	loc_id int);

insert
	into
	address_to_delete (add_id,
	loc_id)
select
	a2.id,
	a2.location_id
from
	(
	select
		max(id) as maxid,
		address_street,
		count(*)
	from
		address a
	group by
		address_street
	having
		count(*)>1
) as q
inner join address a2 on
	a2.id = q.maxid;
	-- DELETE ADDRESS
delete
from
	address a
where
	a.id in (
	select
		add_id
	from
		address_to_delete);
	-- DROP TEMP TABLE
drop table address_to_delete;
	-- >> STEP 2.3 DELETE ADDRESS
create temp table address_to_delete (add_id int,
	loc_id int);

insert
	into
	address_to_delete (add_id,
	loc_id)
select
	a2.id,
	a2.location_id
from
	(
	select
		max(id) as maxid,
		address_street,
		count(*)
	from
		address a
	group by
		address_street
	having
		count(*)>1
) as q
inner join address a2 on
	a2.id = q.maxid;
	-- DELETE ADDRESS
delete
from
	address a
where
	a.id in (
	select
		add_id
	from
		address_to_delete);
	-- DROP TEMP TABLE
drop table address_to_delete;
	-- >> STEP 3 DELETE LOCATION
delete
from
	location l1
where
	l1.id in (
	select
		l.id
	from
		location l
	left outer join address a on
		a.location_id = l.id
	left outer join poi p on
		p.location_id = l.id
	where
		a.id is null
		and p.id is null
);