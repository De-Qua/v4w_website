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
from sqlalchemy import CheckConstraint
# # TODO: FUTUREWARNING
# .format is deprecated
# dovremmo cambiare a
#return _prepare_from_string(" ".join(pjargs))
#
# /opt/anaconda3/lib/python3.7/site-packages/pyproj/crs/crs.py:55: FutureWarning: '+init=<authority>:<code>' syntax is deprecated. '<authority>:<code>' is the preferred initialization method. When making the change, be mindful of axis order changes:
# https://pyproj4.github.io/pyproj/stable/gotchas.html#axis-order-changes-in-proj-6
# return _prepare_from_string(" ".join(pjargs))

"""
Tabella per collegamento molti-a-molti POI-Types
"""
poi_types =  db.Table("poi_types",
    db.Column("poi_id",db.Integer,db.ForeignKey("poi.id"),primary_key=True),
    db.Column("type_id",db.Integer,db.ForeignKey("poi_category_type.id"),primary_key=True)
    )

"""
Tabella per collegamento molti-a-molti Area-Street
"""
area_streets = db.Table("area_streets",
    db.Column("area_id", db.Integer, db.ForeignKey("area.id"),primary_key=True),
    db.Column("street_id", db.Integer, db.ForeignKey("street.id"),primary_key=True)
    )

"""
Tabella per collegamento molti-a-molti Street-Neighborhood
"""
streets_neighborhoods = db.Table("streets_neighborhoods",
    db.Column("street_id", db.Integer, db.ForeignKey("street.id"),primary_key=True),
    db.Column("neighborhood_id", db.Integer, db.ForeignKey("neighborhood.id"),primary_key=True)
    )

"""
Location indica un punto sulla mappa. Può avere un numero civico ma non è obbligatorio.
"""
class Location(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    latitude = db.Column(db.Float,index=True,nullable=False)
    longitude = db.Column(db.Float,index=True,nullable=False)
    street_id = db.Column(db.Integer,db.ForeignKey("street.id"),nullable=False)
    neighborhood_id = db.Column(db.Integer,db.ForeignKey("neighborhood.id"),nullable=False)
    housenumber = db.Column(db.String(8),index=True)
    pois = db.relationship("Poi", backref="location", lazy="dynamic")
    def __repr__(self):
        return self
    # cosa ritorniamo da __str__
    def __str__(self):
        return "({street}) {neighborhood} {housenumber}".format(street=self.street.name,housenumber=self.housenumber,neighborhood=self.street.neighborhoods.all())
    def get_description(self):
        return "({street}) {neighborhood} {housenumber}".format(street=self.street.name,housenumber=self.housenumber,neighborhood=self.street.neighborhoods.all())
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
        return self
    def __str__(self):
        return self.name
    def get_description(self):
        return self.name
"""
Strade intere (senza numeri)
Hanno:
 - nome: nome della strada
 - nome_alt: nome alternativo usato per la ricerca
 - neighborhood_id: relazione con i sestieri a cui appartiene
 - shape: un poligono che ha la forma della strada
 - locations: la relazione con la tabella degli indirizzi (uno a molti)
"""
class Street(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64),index=True,nullable=False)
    name_alt = db.Column(db.String(64),index=True)
    name_spe = db.Column(db.String(64),index=True)
    name_den = db.Column(db.String(64),index=True)
    shape = db.Column(db.PickleType, unique=True,nullable=False) # db.Column(db.String(512)) #opzione 2 con una stringa json
    locations = db.relationship("Location",backref="street",lazy="dynamic")
    neighborhoods = db.relationship("Neighborhood",secondary=streets_neighborhoods,
        lazy = "dynamic", backref=db.backref("streets",lazy="dynamic"))
    score = db.Column(db.Integer,nullable=False,default=0)
    # check constraint serve per dare dei constraint alla tabella, questi vengono controllati a db.session.commit()
    __table_args__ = (CheckConstraint(db.and_(0<=score,score<=100),name="check_score"),)
    def add_neighborhood(self,neighborhood):
        if not self.belongs(neighborhood):
            self.neighborhoods.append(neighborhood)
    def remove_neighborhood(self,neighborhood):
        if self.belongs(neighborhood):
            self.neighborhoods.remove(neighborhood)
    def belongs(self,neighborhood):
        return self.neighborhoods.filter(streets_neighborhoods.c.neighborhood_id==neighborhood.id).count() > 0
    def __repr__(self):
        return self
    def __str__(self):
        return self.name
    def get_description(self):
        return "{name} ({neighborhood})".join(name=self.name,neighborhood=self.neighborhood)

"""
Sestieri:
 - name: nome del sestiere (consideriamo anche Sant'Elena e le isole)
 - zipcode: codice di avviamento postale del sestiere
 - streets: relazione con le strade in quel sestiere (molti a molti)
"""
class Neighborhood(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(16),index=True,nullable=False)
    zipcode = db.Column(db.Integer,nullable=False)
    shape = db.Column(db.PickleType,nullable=False)
    locations = db.relationship("Location",backref="neighborhood",lazy="dynamic")
    def __repr__(self):
        return self
    def __str__(self):
        return self.name
    def get_description(self):
        return "{name} {zipcode}".format(name=self.name,zipcode=self.zipcode)

"""
POI = Punti di Interesse
Comprende bar, caffe, negozi, chiese, ecc.
 - name: nome
 - location_id:
"""
class Poi(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(128),index=True)
    name_alt = db.Column(db.String(128),index=True)
    location_id = db.Column(db.Integer,db.ForeignKey("location.id"),nullable=False)
    categorytype_id = db.Column(db.Integer,db.ForeignKey("poi_category_type.id"))
    opening_hours = db.Column(db.String(256))
    wheelchair = db.Column(db.String(8))
    toilets = db.Column(db.Boolean)
    toilets_wheelchair = db.Column(db.Boolean)
    wikipedia = db.Column(db.String(128))
    atm = db.Column(db.Boolean)
    phone = db.Column(db.String(32))
    last_change = db.Column(db.DateTime,default=datetime.utcnow,nullable=False)
    types = db.relationship("PoiCategoryType",secondary=poi_types,
        lazy = "dynamic", backref=db.backref("pois",lazy="dynamic"))
    score = db.Column(db.Integer,nullable=False,default=0)
    __table_args__ = (CheckConstraint(db.and_(0<=score,score<=100),name="check_score"),)
    def add_type(self,type):
        if not self.is_type(type):
            self.types.append(type)
    def remove_type(self,type):
        if self.is_type(type):
            self.types.remove(type)
    def is_type(self,type):
        return self.types.filter(poi_types.c.type_id==type.id).count() > 0
    def get_description(self):
        return "{name}\nAddress: {address})".format(
        name=self.name, address=self.location)
    def __repr__(self):
        return self
    def __str__(self):
        return self.name

class PoiCategory(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(32),index=True,unique=True,nullable=False)
    types = db.relationship("PoiCategoryType",backref="category",lazy="dynamic")
    def __repr__(self):
        return "{name}".format(
        name=self.name)

class PoiCategoryType(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(32),index=True,nullable=False)
    category_id = db.Column(db.Integer,db.ForeignKey("poi_category.id"),nullable=False)
    subtype = db.Column(db.String(32),index=True)
    def __repr__(self):
        return "{name} ({category})".format(
        name=self.name, category=self.category)
