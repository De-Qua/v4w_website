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
    __tablename__ = "current_data"
    __bind_key__ = "data_versions"

    id = db.Column(db.Integer, primary_key=True)

    # Foreign keys to the latest versioned entries
    street_graph_id = db.Column(
        db.Integer,
        db.ForeignKey("graph_street.id"),
        nullable=True
    )
    waterbus_graph_id = db.Column(
        db.Integer,
        db.ForeignKey("graph_waterbus.id"),
        nullable=True
    )
    water_graph_id = db.Column(
        db.Integer,
        db.ForeignKey("graph_water.id"),
        nullable=True
    )
    tide_id = db.Column(
        db.Integer,
        db.ForeignKey("tide_new.id"),
        nullable=True
    )

    # Relationships to access the actual objects
    street_graph = db.relationship("GraphStreet", lazy=True)
    waterbus_graph = db.relationship("GraphWaterbus", lazy=True)
    water_graph = db.relationship("GraphWater", lazy=True)  
    tide = db.relationship("TideNew", lazy=True)

    graph_updated_at = db.Column(db.DateTime)  # timestamp of last update
    graph_check_at = db.Column(db.DateTime)  # timestamp of last check
    
    def get_graphs_versions(self):
        return {
            "graph_street_version": self.street_graph.version,
            "graph_water_version": self.water_graph.version,
            "gtfs_number": self.waterbus_graph.gtfs_number,
        }

############
## GRAPHS ##
############

class GraphStreet(db.Model):
    __tablename__ = 'graph_street'
    __bind_key__ = 'data_versions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    # Define relationship (one GraphStreet → many GraphStreetWaterbus)
    waterbus_graphs = db.relationship(
        "GraphWaterbus",
        backref="graph_street",
        cascade="all, delete-orphan",
        lazy=True
    )
    
    def __str__(self):
        return f"Graph Street - v{self.version}"


class GraphWaterbus(db.Model):
    __tablename__ = 'graph_waterbus'
    __bind_key__ = 'data_versions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    gtfs_number = db.Column(db.Integer, nullable=False)
    valid_from = db.Column(db.DateTime, nullable=False)
    valid_to = db.Column(db.DateTime, nullable=False)
    # Foreign key to indicate which GraphStreet it was derived from
    graph_street_id = db.Column(
        db.Integer,
        db.ForeignKey("graph_street.id", ondelete="CASCADE"),
        nullable=False
    )
    
    def __str__(self):
        return f"{self.graph_street} | GTFS - v{self.gtfs_number}"
    
class GraphWater(db.Model):
    __tablename__ = 'graph_water'
    __bind_key__ = 'data_versions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    
    def __str__(self):
        return f"Graph Water - v{self.version}"

##########
## TIDE ##
##########

class TideNew(db.Model):
    __tablename__ = "tide_new"
    __bind_key__ = 'data_versions'
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
        return f"{self.value}cm"
    
    def get_dict(self):
        return {
            "id_station": self.id_station,
            "station": self.station,
            "short_name": self.short_name,
            "latDMSN": self.latDMSN,
            "lonDMSE": self.lonDMSE,
            "latDDN": self.latDDN,
            "lonDDE": self.lonDDE,
            "updated_at": self.updated_at,
            "uploaded_at": self.uploaded_at,
            "value": self.value,
            "tide_level": int(100*self.value)
        }


