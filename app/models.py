"""
Ogni volta che si cambia qualcosa da terminale
flask db migrate
flask db upgrade

Se dà errori provare
flask db stamp head
flask db migrate
flask db upgrade
"""
from app import db
from datetime import datetime

# # TODO: FUTUREWARNING
# .format is deprecated
# dovremmo cambiare a
#return _prepare_from_string(" ".join(pjargs))
#
# /opt/anaconda3/lib/python3.7/site-packages/pyproj/crs/crs.py:55: FutureWarning: '+init=<authority>:<code>' syntax is deprecated. '<authority>:<code>' is the preferred initialization method. When making the change, be mindful of axis order changes:
# https://pyproj4.github.io/pyproj/stable/gotchas.html#axis-order-changes-in-proj-6
# return _prepare_from_string(" ".join(pjargs))

class Location(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    latitude = db.Column(db.Float,index=True,nullable=False)
    longitude = db.Column(db.Float,index=True,nullable=False)
    street_id = db.Column(db.Integer,db.ForeignKey("street.id"))
    housenumber = db.Column(db.String(8),index=True)
    pois = db.relationship("Poi", backref="location", lazy="dynamic")
    def __repr__(self):

        return "({street}) {neighborhood} {housenumber}".format(street=self.street.name,housenumber=self.housenumber,neighborhood=self.street.neighborhood)

"""
Tabella per collegamento molti-a-molti Area-Street
"""
area_streets = db.Table("area_streets",
    db.Column("area_id", db.Integer, db.ForeignKey("area.id"),primary_key=True),
    db.Column("street_id", db.Integer, db.ForeignKey("street.id"),primary_key=True)
    )

"""
Area indica una zona (senza vincoli rispetto alle altre zone o sestieri)
che puo essere un sottoinsieme di un sestiere o appartenere a piu sestieri
Esempio: Santa Marta, Baia del Re
"""
class Area(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64), index=True, nullable=False)
    shape = db.Column(db.PickleType)
    streets = db.relationship("Street",secondary=area_streets,
        lazy = "subquery", backref=db.backref("areas",lazy="dynamic"))
    def __repr__(self):
        return "{name} ({neighborhoods}) {streets}".format(name=self.name,neighborhoods=self.neighborhood,streets=self.street)
"""
Strade intere (senza numeri)
Hanno:
 - nome: nome della strada
 - nome_alt: nome alternativo usato per la ricerca
 - neighborhood_id: relazione con il sestiere a cui appartiene
 - shape: un poligono che ha la forma della strada
 - locations: la relazione con la tabella degli indirizzi (uno a molti)
"""
class Street(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64),index=True)
    name_alt = db.Column(db.String(64),index=True)
    neighborhood_id = db.Column(db.Integer,db.ForeignKey("neighborhood.id"))
    shape = db.Column(db.PickleType) # db.Column(db.String(512)) #opzione 2 con una stringa json
    locations = db.relationship("Location",backref="street",lazy="dynamic")
    def __repr__(self):
        return self.name #return "{name} ({neighborhood})".format(name=self.name,neighborhood=self.neighborhood)

"""
Sestieri:
 - name: nome del sestiere (consideriamo anche Sant'Elena e le isole)
 - zipcode: codice di avviamento postale del sestiere
 - streets: relazione con le strade in quel sestiere (uno a molti)
"""
class Neighborhood(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(16),index=True)
    zipcode = db.Column(db.Integer,nullable=False)
    streets = db.relationship("Street",backref="neighborhood",lazy="dynamic")
    shape = db.Column(db.PickleType)
    def __repr__(self):
        return self.name #return "{name} {zipcode}".format(name=self.name,zipcode=self.zipcode)

poi_types =  db.Table("poi_types",
    db.Column("poi_id",db.Integer,db.ForeignKey("poi.id"),primary_key=True),
    db.Column("type_id",db.Integer,db.ForeignKey("poi_category_type.id"),primary_key=True)
    )

"""
POI = Punti di Interesse
Comprende bar, caffe, negozi, chiese, ecc.
 - name: nome
 - location_id:
"""
class Poi(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(128),index=True)
    location_id = db.Column(db.Integer,db.ForeignKey("location.id"))
    categorytype_id = db.Column(db.Integer,db.ForeignKey("poi_category_type.id"))
    opening_hours = db.Column(db.String(256))
    wheelchair = db.Column(db.String(8))
    last_change = db.Column(db.DateTime,default=datetime.utcnow)
    types = db.relationship("PoiCategoryType",secondary=poi_types,
        lazy = "subquery", backref=db.backref("pois",lazy="dynamic"))
    def __repr__(self):
        return "{name}\nAddress: {address})".format(
        name=self.name, address=self.location)

class PoiCategory(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(32),index=True,unique=True)
    types = db.relationship("PoiCategoryType",backref="category",lazy="dynamic")

class PoiCategoryType(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(32),index=True)
    category_id = db.Column(db.Integer,db.ForeignKey("poi_category.id"))
    subtype = db.Column(db.String(32),index=True)
