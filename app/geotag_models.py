"""
Ogni volta che si cambia qualcosa da terminale
flask db migrate
flask db upgrade

Se dà errori provare
flask db stamp head
flask db migrate
flask db upgrade
"""
import warnings
from app import db
import pdb
import datetime
from sqlalchemy import CheckConstraint
from flask_sqlalchemy import SQLAlchemy

class GeotagUser(db.Model):
    __tablename__ = 'geotag_user'
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    nickname = db.Column(db.String(32), unique=True, nullable=False)
    password = db.Column(db.String(160), nullable=False)
    active = db.Column(db.Boolean(), default=False)
    confirmed_at = db.Column(db.DateTime())
    # Relations
    tags = db.relationship('Tag', backref=db.backref('creator'))
    layers = db.relationship('Layer', backref=db.backref('owner'))
    layer_items = db.relationship('LayerItem', backref=db.backref('owner'))
    extra_data_groups = db.relationship('LayerItemExtraDataGroup', backref=db.backref('owner'))
    

class Language(db.Model):
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    code = db.Column(db.String(2), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    # Relations
    layers = db.relationship('Layer', lazy=True, backref=db.backref('default_language', lazy=True))
    layer_translations = db.relationship('LayerTranslation', lazy=True, backref=db.backref('language', lazy=True))
    layer_item_translations = db.relationship('LayerItemTranslation', lazy=True, backref=db.backref('language', lazy=True))
    parameters = db.relationship('LayerItemExtraDataParameterTranslation', lazy=True, backref=db.backref('language', lazy=True))
    paramval_translation = db.relationship('LayerItemExtraDataParameterValueTranslations', lazy=True, backref=db.backref('language', lazy=True))

class Tag(db.Model):
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)

    geotag_user_id = db.Column(db.Integer, db.ForeignKey("geotag_user.id"), nullable=False)
    layer_id = db.Column(db.Integer, db.ForeignKey("layer.id"), nullable=False)
    layer_item_id = db.Column(db.Integer, db.ForeignKey("layer_item.id"), nullable=False)
    # creator = user.id

class Visibility(db.Model):
    __tablename__ = 'visibility'
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    # Relations
    layers = db.relationship('Layer', lazy=True, backref=db.backref('visibility', lazy=True))
    

geotag_user_table = db.table('geotag_user',
                            db.Column('geotag_user_id', db.Integer(), db.ForeignKey('geotag_user.id')),
                            db.Column('layer_datagroup_id', db.Integer(), db.ForeignKey('datagroup.id')))
                            #info={'bind_key': 'geotag'})

layer_tag_table = db.Table('layer_tag',
                            db.Column('layer_id', db.Integer(), db.ForeignKey('layer.id')),
                            db.Column('tag_id', db.Integer(), db.ForeignKey('tag.id')))
                            #info={'bind_key': 'geotag'})

layer_datagroup_table = db.Table('layer_datagroup',
                            db.Column('layer_id', db.Integer(), db.ForeignKey('layer.id')),
                            db.Column('datagroup_id', db.Integer(), db.ForeignKey('datagroup.id')))
                            #info={'bind_key': 'geotag'})

class Layer(db.Model):
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False) #L'url che verra' usata per www.dequa.it/layer/layer_url
    date_creation = db.Column(db.DateTime())
    date_start = db.Column(db.DateTime())
    date_end = db.Column(db.DateTime())
    date_last_modification = db.Column(db.DateTime())
    active = db.Column(db.Boolean(), default=False)
    password = db.Column(db.String(255))
    default_icon = db.Column(db.String(255)) # Url interno agli asset
    # Relations
    layer_translations = db.relationship('LayerTranslation', lazy=True, backref=db.backref('layer', lazy=True))
    tags = db.relationship('Tag', secondary=layer_tag_table, backref=db.backref('layers', lazy=True))
    layer_items = db.relationship('LayerItem', lazy=True, backref=db.backref('layer', lazy=True))
    datagroups = db.relationship('LayerItemExtraDataGroup', secondary=layer_datagroup_table, backref=db.backref('layers', lazy=True))
    
    geotag_user_id = db.Column(db.Integer, db.ForeignKey("geotag_user.id"), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey("language.id"), nullable=False)
    visibility_id = db.Column(db.Integer, db.ForeignKey("visibility.id"), nullable=False)
    policy_id = db.Column(db.Integer, db.ForeignKey("policy.id"), nullable=False)
    datagroup_id = db.Column(db.Integer, db.ForeignKey("datagroup.id"), nullable=False)
    # owner = user.id
    # visibility = LayerVisibility.id
    # contribution_policy = LayerContributionPolicy.id
    # default_language = language.id

class LayerContributionPolicy(db.Model):
    __tablename__ = 'policy'
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    # Relations
    layers = db.relationship('Layer', lazy=True, backref=db.backref('policy', lazy=True))
    
class LayerTranslation(db.Model):
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    abstract = db.Column(db.String(255))
    description = db.Column(db.String(255))

    language_id = db.Column(db.Integer, db.ForeignKey("language.id"), nullable=False)
    layer_id = db.Column(db.Integer, db.ForeignKey("layer.id"), nullable=False)
    
    # layer = layer.id
    # language = language.id
    
class LayerItemExtraDataGroup(db.Model):
    __tablename__ = 'datagroup'
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    keyname = db.Column(db.String(255), nullable=False)
    # Relations
    parameters = db.relationship('LayerItemExtraDataParameter', lazy=True, backref=db.backref('datagroup', lazy=True))
    layer_items = db.relationship('LayerItem', lazy=True, backref=db.backref('datagroup', lazy=True))

    geotag_user_id = db.Column(db.Integer, db.ForeignKey("geotag_user.id"), nullable=False)
    layer_id = db.Column(db.Integer, db.ForeignKey("layer.id"), nullable=False)

class LayerItemExtraDataType(db.Model):
    __tablename__ = 'datatype'
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    # Relations
    parameters = db.relationship('LayerItemExtraDataParameter', lazy=True, backref=db.backref('datatype', lazy=True))


class LayerItemExtraDataParameter(db.Model):
    __tablename__ = 'parameter'       
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    keyname = db.Column(db.String(255), nullable=False)
    # Relations
    translations = db.relationship('LayerItemExtraDataParameterTranslation', lazy=True, backref=db.backref('parameter', lazy=True))
    parameter_values = db.relationship('LayerItemExtraDataParameterValue', lazy=True, backref=db.backref('parameter', lazy=True))

    datagroup_id = db.Column(db.Integer, db.ForeignKey("datagroup.id"), nullable=False)
    datatype_id = db.Column(db.Integer, db.ForeignKey("datatype.id"), nullable=False)
    paramval_translation_id = db.Column(db.Integer, db.ForeignKey("paramval_translation.id"), nullable=False)

class LayerItemExtraDataParameterTranslation(db.Model):
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))

    language_id = db.Column(db.Integer, db.ForeignKey("language.id"), nullable=False)
    parameter_id = db.Column(db.Integer, db.ForeignKey("parameter.id"), nullable=False)


    # LayerItemExtraDataParameterId = LayerItemExtraDataParameter.id
    # language = language.id

layer_item_tag_table = db.Table('layer_item_tag',
                            db.Column('layer_item_id', db.Integer(), db.ForeignKey('layer_item.id')),
                            db.Column('tag_id', db.Integer(), db.ForeignKey('tag.id')),
                            info={'bind_key': 'geotag'})


class LayerItem(db.Model):
    __tablename__ = 'layer_item'
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)

    lat = db.Column(db.Integer(), nullable=False)
    lng = db.Column(db.Integer(), nullable=False)

    icon = db.Column(db.String(255)) # Url interno agli asset
    active = db.Column(db.Boolean(), default=False)
    approved = db.Column(db.Boolean(), default=False)

    date_creation = db.Column(db.DateTime())
    date_start = db.Column(db.DateTime())
    date_end = db.Column(db.DateTime())
    date_last_modification = db.Column(db.DateTime())

    # Relations
    translations = db.relationship('LayerItemTranslation', lazy=True, backref=db.backref('layer_item', lazy=True))
    tags = db.relationship('Tag', secondary=layer_item_tag_table, backref=db.backref('layer_items', lazy=True))
    parameter_values = db.relationship('LayerItemExtraDataParameterValue', lazy=True, backref=db.backref('layer_item', lazy=True))

    geotag_user_id = db.Column(db.Integer, db.ForeignKey("geotag_user.id"), nullable=False)
    layer_id = db.Column(db.Integer, db.ForeignKey("layer.id"), nullable=False)
    datagroup_id = db.Column(db.Integer, db.ForeignKey("datagroup.id"), nullable=False)

    # owner = user.id
    # layer = layer.id
    # data_group = LayerItemExtraDataGroup.id

class LayerItemTranslation(db.Model):
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    abstract = db.Column(db.String(255))
    description = db.Column(db.String(255))
    image_url = db.Column(db.String(255))
    video_url = db.Column(db.String(255))
    external_url = db.Column(db.String(255))

    language_id = db.Column(db.Integer, db.ForeignKey("language.id"), nullable=False)
    layer_item_id = db.Column(db.Integer, db.ForeignKey("layer_item.id"), nullable=False)


    # layer_item = layerItem.id
    # language = language.id


class LayerItemExtraDataParameterValue(db.Model):
    __tablename__ = 'parameter_value' 
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)

    layer_item_id = db.Column(db.Integer, db.ForeignKey("layer_item.id"), nullable=False)
    parameter_id = db.Column(db.Integer, db.ForeignKey("parameter.id"), nullable=False)
    paramval_translation_id = db.Column(db.Integer, db.ForeignKey("paramval_translation.id"), nullable=False)


class LayerItemExtraDataParameterValueTranslations(db.Model):
    __tablename__ = 'paramval_translation' 
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    value = db.Column(db.String(255))

    parameters = db.relationship('LayerItemExtraDataParameterValue', lazy=True, backref=db.backref('value_translation', lazy=True))
    
    language_id = db.Column(db.Integer, db.ForeignKey("language.id"), nullable=False)
  
    # language = language.id