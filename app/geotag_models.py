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

# # geouser_table = db.table('geouser',
# #                             db.Column('geouser_id', db.Integer(), db.ForeignKey('geouser.id')),
# #                             db.Column('layer_datagroup_id', db.Integer(), db.ForeignKey('datagroup.id')))
# #                             #info={'bind_key': 'geotag'})

layer_tag_table = db.Table('LayerTag',
                            db.Column('layer_id', db.Integer(), db.ForeignKey('Layer.id')),
                            db.Column('tag_id', db.Integer(), db.ForeignKey('Tag.id')),
                            info={'bind_key': 'geotag'}
                            )

layer_item_tag_table = db.Table('LayerItemTag',
                            db.Column('layer_item_id', db.Integer(), db.ForeignKey('LayerItem.id')),
                            db.Column('tag_id', db.Integer(), db.ForeignKey('Tag.id')),
                            info={'bind_key': 'geotag'})

layer_datagroup_table = db.Table('LayerDatagroup',
                            db.Column('layer_id', db.Integer(), db.ForeignKey('Layer.id')),
                            db.Column('datagroup_id', db.Integer(), db.ForeignKey('Datagroup.id')),
                            info={'bind_key': 'geotag'})
class Geouser(db.Model):
    __tablename__ = 'Geouser'
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    nickname = db.Column(db.String(32), unique=True, nullable=False)
    password = db.Column(db.String(160), nullable=False)
    active = db.Column(db.Boolean(), default=False)
    confirmed_at = db.Column(db.DateTime())
    ## Relations
    tags = db.relationship('Tag', backref=db.backref('creator'))
    layers = db.relationship('Layer', backref=db.backref('owner'))
    layer_items = db.relationship('LayerItem', backref=db.backref('owner'))
    extra_data_groups = db.relationship('LayerItemExtraDataGroup', backref=db.backref('owner'))
    
    def __str__(self):
        return self.name

class Language(db.Model):
    __bind_key__ = 'geotag'
    __tablename__ = 'Language'
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

    def __str__(self):
        return self.name
class Tag(db.Model):
    __bind_key__ = 'geotag'
    __tablename__ = 'Tag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    ## ForeignKey
    geouser_id = db.Column(db.Integer, db.ForeignKey("Geouser.id"), nullable=False)
    # layer_id = db.Column(db.Integer, db.ForeignKey("Layer.id"))
    # layer_item_id = db.Column(db.Integer, db.ForeignKey("LayerItem.id"))
    # creator = user.id

class Visibility(db.Model):
    __tablename__ = 'Visibility'
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    # Relations
    layers = db.relationship('Layer', lazy=True, backref=db.backref('visibility', lazy=True))
    
    def __str__(self):
        return self.name    

class Layer(db.Model):
    __tablename__ = 'Layer'
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False) #internal name
    url = db.Column(db.String(255), nullable=False) #L'url che verra' usata per www.dequa.it/layer/layer_url
    date_creation = db.Column(db.DateTime())
    date_start = db.Column(db.DateTime())
    date_end = db.Column(db.DateTime())
    date_last_modification = db.Column(db.DateTime())
    active = db.Column(db.Boolean(), default=False)
    password = db.Column(db.String(255))
    default_icon = db.Column(db.String(255)) # Url interno agli asset
    ## Relations
    layer_translations = db.relationship('LayerTranslation', lazy=True, backref=db.backref('layer', lazy=True))
    tags = db.relationship('Tag', secondary=layer_tag_table, backref=db.backref('layers', lazy=True))
    layer_items = db.relationship('LayerItem', lazy=True, backref=db.backref('layer', lazy=True))
    datagroups = db.relationship('LayerItemExtraDataGroup', secondary=layer_datagroup_table, backref=db.backref('layers', lazy=True))
    ## ForeignKey
    geouser_id = db.Column(db.Integer, db.ForeignKey("Geouser.id"), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey("Language.id"), nullable=False)
    visibility_id = db.Column(db.Integer, db.ForeignKey("Visibility.id"), nullable=False)
    contribution_id = db.Column(db.Integer, db.ForeignKey("Contribution.id"), nullable=False)
    # datagroup_id = db.Column(db.Integer, db.ForeignKey("datagroup.id"), nullable=False)
#     # owner = user.id
#     # visibility = LayerVisibility.id
#     # contribution_policy = LayerContributionPolicy.id
#     # default_language = language.id

class LayerContributionPolicy(db.Model):
    __tablename__ = 'Contribution'
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    # Relations
    layers = db.relationship('Layer', lazy=True, backref=db.backref('contribution', lazy=True))

    def __str__(self):
        return self.name 

class LayerTranslation(db.Model):
    __tablename__ = 'LayerTranslation'
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    abstract = db.Column(db.String(255))
    description = db.Column(db.String(255))

    language_id = db.Column(db.Integer, db.ForeignKey("Language.id"), nullable=False)
    layer_id = db.Column(db.Integer, db.ForeignKey("Layer.id"), nullable=False)
    
#     # layer = layer.id
#     # language = language.id
    
class LayerItemExtraDataGroup(db.Model):
    __tablename__ = 'Datagroup'
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    keyname = db.Column(db.String(255), nullable=False)
    ## Relations
    parameters = db.relationship('LayerItemExtraDataParameter', lazy=True, backref=db.backref('datagroup', lazy=True))
    layer_items = db.relationship('LayerItem', lazy=True, backref=db.backref('datagroup', lazy=True))
    ## ForeignKeys
    geouser_id = db.Column(db.Integer, db.ForeignKey("Geouser.id"), nullable=False)
    # layer_id = db.Column(db.Integer, db.ForeignKey("layer.id"), nullable=False)


class LayerItemExtraDataType(db.Model):
    __tablename__ = 'Datatype'
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    ## Relations
    parameters = db.relationship('LayerItemExtraDataParameter', lazy=True, backref=db.backref('datatype', lazy=True))


class LayerItemExtraDataParameter(db.Model):
    __tablename__ = 'LayerItemDatagroupParameter'       
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    keyname = db.Column(db.String(255), nullable=False)
    ## Relations
    translations = db.relationship('LayerItemExtraDataParameterTranslation', lazy=True, backref=db.backref('parameter', lazy=True))
    parameter_values = db.relationship('LayerItemExtraDataParameterValue', lazy=True, backref=db.backref('parameter', lazy=True))
    ## ForeignKeys
    datagroup_id = db.Column(db.Integer, db.ForeignKey("Datagroup.id"), nullable=False)
    datatype_id = db.Column(db.Integer, db.ForeignKey("Datatype.id"), nullable=False)
    paramval_translation_id = db.Column(db.Integer, db.ForeignKey("LayerItemDatagroupParameterValueTranslation.id"), nullable=False)

class LayerItemExtraDataParameterTranslation(db.Model):
    __tablename__ = 'LayerItemDatagroupParameterTranslation'       
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    ## ForeignKeys
    language_id = db.Column(db.Integer, db.ForeignKey("Language.id"), nullable=False)
    parameter_id = db.Column(db.Integer, db.ForeignKey("LayerItemDatagroupParameter.id"), nullable=False)


    # LayerItemExtraDataParameterId = LayerItemExtraDataParameter.id
    # language = language.id


class LayerItem(db.Model):
    __tablename__ = 'LayerItem'
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)

    lat = db.Column(db.Float(), nullable=False)
    lng = db.Column(db.Float(), nullable=False)

    icon = db.Column(db.String(255)) # Url interno agli asset
    active = db.Column(db.Boolean(), default=False)
    approved = db.Column(db.Boolean(), default=False)

    date_creation = db.Column(db.DateTime())
    date_start = db.Column(db.DateTime())
    date_end = db.Column(db.DateTime())
    date_last_modification = db.Column(db.DateTime())

    ## Relations
    translations = db.relationship('LayerItemTranslation', lazy=True, backref=db.backref('layer_item', lazy=True))
    tags = db.relationship('Tag', secondary=layer_item_tag_table, backref=db.backref('layer_items', lazy=True))
    parameter_values = db.relationship('LayerItemExtraDataParameterValue', lazy=True, backref=db.backref('layer_item', lazy=True))
    ## ForeignKeys
    geouser_id = db.Column(db.Integer, db.ForeignKey("Geouser.id"), nullable=False)
    layer_id = db.Column(db.Integer, db.ForeignKey("Layer.id"), nullable=False)
    datagroup_id = db.Column(db.Integer, db.ForeignKey("Datagroup.id"))

#     # owner = user.id
#     # layer = layer.id
#     # data_group = LayerItemExtraDataGroup.id

class LayerItemTranslation(db.Model):
    __tablename__ = 'LayerItemTranslation'
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    abstract = db.Column(db.String(255))
    description = db.Column(db.String(255))
    image_url = db.Column(db.String(255))
    video_url = db.Column(db.String(255))
    external_url = db.Column(db.String(255))
    ## ForeignKeys
    language_id = db.Column(db.Integer, db.ForeignKey("Language.id"), nullable=False)
    layer_item_id = db.Column(db.Integer, db.ForeignKey("LayerItem.id"), nullable=False)


#     # layer_item = layerItem.id
#     # language = language.id


class LayerItemExtraDataParameterValue(db.Model):
    __tablename__ = 'LayerItemDatagroupParameterValue' 
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    ## ForeignKeys
    layer_item_id = db.Column(db.Integer, db.ForeignKey("LayerItem.id"), nullable=False)
    parameter_id = db.Column(db.Integer, db.ForeignKey("LayerItemDatagroupParameter.id"), nullable=False)
    paramval_translation_id = db.Column(db.Integer, db.ForeignKey("LayerItemDatagroupParameterValueTranslation.id"), nullable=False)


class LayerItemExtraDataParameterValueTranslations(db.Model):
    __tablename__ = 'LayerItemDatagroupParameterValueTranslation' 
    __bind_key__ = 'geotag'
    id = db.Column(db.Integer(), primary_key=True)
    value = db.Column(db.String(255))
    ## Relationship
    parameters = db.relationship('LayerItemExtraDataParameterValue', lazy=True, backref=db.backref('value_translation', lazy=True))
    ## ForeignKeys
    language_id = db.Column(db.Integer, db.ForeignKey("Language.id"), nullable=False)
  
    # language = language.id