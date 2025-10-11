-- DROP FUNCTION public.fn_getsuggest_street(varchar, int4);

CREATE OR REPLACE FUNCTION public.fn_getsuggest_street(searchstring character varying, top integer)
 RETURNS TABLE(resulttype text, str_name character varying, str_name_alt character varying, str_name_spe character varying, str_neig character varying, shape geometry)
 LANGUAGE plpgsql
AS $function$
	BEGIN
	return query select 
		'street' resulttype
		,s."name" as str_name
		,s.name_alt as str_name_alt
		,s.name_spe as str_name_spe
		,string_agg( n."name", ', ')::character varying as str_neig
		,s.shape
	from (
		select *, greatest(SIMILARITY(s2a, searchstring), SIMILARITY(s.name_spe || ' ' || s2a, searchstring), SIMILARITY(s.name_alt, searchstring)) as sim
		from street s
		cross join regexp_split_to_table(s.name_den, '( DETTA | DETTO | O | GIA'' )') as s2a
		order by sim desc
		limit (top)
	) s
	inner join neighborhood n on st_intersects(s.shape, n.shape)
	where s.sim > 0.5
	group by
		s.id
		,s."name" 
		,s.name_alt 
		,s.name_spe 
		,s.shape
		,s.sim
	order by s.sim desc
	limit (top);
	END;
$function$
;