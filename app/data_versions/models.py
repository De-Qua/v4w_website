# """
# Ogni volta che si cambia qualcosa da terminale
# flask db migrate
# flask db upgrade

# Se dà errori provare
# flask db stamp head
# flask db migrate
# flask db upgrade
# """
import warnings
from app import db
import pdb
import datetime
from sqlalchemy import CheckConstraint
from flask_sqlalchemy import SQLAlchemy

##################
## CURRENT DATA ##
##################

class CurrentData(db.Model):
    __tablename__ = "CurrentData"
    __bind_key__ = "data_versions"

    id = db.Column(db.Integer, primary_key=True)

    # Foreign keys to the latest versioned entries
    street_graph_id = db.Column(
        db.Integer,
        db.ForeignKey("GraphStreet.id"),
        nullable=False
    )
    waterbus_graph_id = db.Column(
        db.Integer,
        db.ForeignKey("GraphStreetWaterbus.id"),
        nullable=False
    )
    water_graph_id = db.Column(
        db.Integer,
        db.ForeignKey("GraphWater.id"),
        nullable=False
    )
    tide_id = db.Column(
        db.Integer,
        db.ForeignKey("TideNew.id"),
        nullable=False
    )

    # Relationships to access the actual objects
    street_graph = db.relationship("GraphStreet", lazy=True)
    waterbus_graph = db.relationship("GraphStreetWaterbus", lazy=True)
    water_graph = db.relationship("GraphWater", lazy=True)  
    tide = db.relationship("TideNew", lazy=True)

    updated_at = db.Column(db.DateTime, nullable=False)  # timestamp of last update

############
## GRAPHS ##
############

class GraphStreet(db.Model):
    __tablename__ = 'GraphStreet'
    __bindkey__ = 'data_versions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    # Define relationship (one GraphStreet → many GraphStreetWaterbus)
    waterbus_graphs = db.relationship(
        "GraphStreetWaterbus",
        backref="graphstreet",
        cascade="all, delete-orphan",
        lazy=True
    )
    
    def __str__(self):
        return self.name


class GraphStreetWaterbus(db.Model):
    __tablename__ = 'GraphStreetWaterbus'
    __bindkey__ = 'data_versions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    gtfs_number = db.Column(db.Integer, nullable=False)
    valid_from = db.Column(db.DateTime, nullable=False)
    valid_to = db.Column(db.DateTime, nullable=False)
    # Foreign key to indicate which GraphStreet it was derived from
    graphstreet_id = db.Column(
        db.Integer,
        db.ForeignKey("GraphStreet.id", ondelete="CASCADE"),
        nullable=False
    )
    
    def __str__(self):
        return self.name
    
class GraphWater(db.Model):
    __tablename__ = 'GraphWater'
    __bindkey__ = 'data_versions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    
    def __str__(self):
        return self.name

##########
## TIDE ##
##########

class TideNew(db.Model):
    __tablename__ = "TideNew"
    __bindkey__ = 'data_versions'
    id = db.Column(db.Integer(), primary_key=True)
    id_station = db.Column(db.String(8))
    station = db.Column(db.String(64))
    short_name = db.Column(db.String(16))
    latDMSN = db.Column(db.Float)
    lonDMSE = db.Column(db.Float)
    latDDN = db.Column(db.Float)
    lonDDE = db.Column(db.Float)
    updated_at = db.Column(db.DateTime)
    uploaded_at = db.Column(db.DateTime)
    value = db.Column(db.Float)
    
    def __str__(self):
        return f"{self.updated_at} - {self.value}"


