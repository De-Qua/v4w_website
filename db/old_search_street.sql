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
	from street s
	inner join neighborhood n on st_intersects(s.shape, n.shape)
	where
		s."name" ilike ('%' || searchstring  || '%')
		or s.name_alt ilike ('%' || searchstring  || '%')
	group by
		s.id
		,s."name" 
		,s.name_alt 
		,s.name_spe 
		,s.shape
	limit (top);
	END;
$function$
;
