from app import db
from datetime import datetime

class Location(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    latitude = db.Column(db.Float,index=True)
    longitude = db.Column(db.Float,index=True)
    street_id = db.Column(db.Integer,db.ForeignKey("street.id"))
    housenumber = db.Column(db.String(8),index=True)
    pois = db.relationship("Poi", backref="location", lazy="dynamic")
    def __repr__(self):
        return "({street}) {neighborhood} {housenumber}".format(street=self.street.name,housenumber=self.housenumber,neighborhood=self.street.neighborhood)

class Street(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64),index=True)
    name_alt = db.Column(db.String(64),index=True)
    neighborhood_id = db.Column(db.Integer,db.ForeignKey("neighborhood.id"))
    locations = db.relationship("Location",backref="street",lazy="dynamic")
    def __repr__(self):
        return "{name} ({neighborhood})".format(name=self.name,neighborhood=self.neighborhood)

class Neighborhood(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(16),index=True)
    zipcode = db.Column(db.Integer,unique=True)
    streets = db.relationship("Street",backref="neighborhood",lazy="dynamic")
    def __repr__(self):
        return "{name} {zipcode}".format(name=self.name,zipcode=self.zipcode)

poi_types =  db.Table("poi_types",
    db.Column("poi_id",db.Integer,db.ForeignKey("poi.id"),primary_key=True),
    db.Column("type_id",db.Integer,db.ForeignKey("poi_category_type.id"),primary_key=True)
    )

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
