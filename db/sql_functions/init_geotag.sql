INSERT INTO public."Language"
(id, "name", code, "order")
values
(nextval('"Language_id_seq"'::regclass), 'Italiano', 'IT', 0)
,(nextval('"Language_id_seq"'::regclass), 'English', 'EN', 0);

INSERT INTO public."Contribution"
(id, "name")
VALUES(nextval('"Contribution_id_seq"'::regclass), 'Open'),
(nextval('"Contribution_id_seq"'::regclass), 'Close'),
(nextval('"Contribution_id_seq"'::regclass), 'With moderation');

INSERT INTO public."Visibility"
(id, "name")
VALUES(nextval('"Visibility_id_seq"'::regclass), 'Public'),
(nextval('"Visibility_id_seq"'::regclass), 'Private'),
(nextval('"Visibility_id_seq"'::regclass), 'Unlisted');

INSERT INTO public."Datatype"
(id, "name")
VALUES(nextval('"Datatype_id_seq"'::regclass), 'Integer'),
(nextval('"Datatype_id_seq"'::regclass), 'Boolean'),
(nextval('"Datatype_id_seq"'::regclass), 'Double'),
(nextval('"Datatype_id_seq"'::regclass), 'String'),
(nextval('"Datatype_id_seq"'::regclass), 'Date'),
(nextval('"Datatype_id_seq"'::regclass), 'Datetime');