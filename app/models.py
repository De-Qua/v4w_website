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
import pdb
import datetime
from sqlalchemy import CheckConstraint
from flask_security import RoleMixin, UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import create_access_token
import pdb
#from app.token_helper import add_token_to_database
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
    street_id = db.Column(db.Integer,db.ForeignKey("street.id"))
    neighborhood_id = db.Column(db.Integer,db.ForeignKey("neighborhood.id"),nullable=False)
    housenumber = db.Column(db.String(8),index=True)
    shape = db.Column(db.PickleType,nullable=False)
    pois = db.relationship("Poi", backref="location", lazy="dynamic")
    def __repr__(self):
        return self._repr(id=self.id,
                          latitude=self.latitude,
                          longitude=self.longitude,
                          neighborhood=self.neighborhood.name,
                          housenumber=self.housenumber)
    # cosa ritorniamo da __str__
    def __str__(self):
        if self.housenumber and self.street:
            return "{neighborhood} {housenumber}".format(street=self.street.name,housenumber=self.housenumber,neighborhood=self.neighborhood.name)
        else:
            return "({neighborhood}) {lat},{lon}".format(neighborhood=self.neighborhood.name,lat=self.latitude,lon=self.longitude)
    def get_description(self):
        try:
            if self.housenumber:
                return fillDictionary(modelName='Location', id=self.id, name=self.street.name,housenumber=self.housenumber, neighborhood=self.neighborhood.name, zipcode=self.neighborhood.zipcode)
            else:
                return fillDictionary(modelName='Location', id=self.id, name=self.street.name, neighborhood=self.neighborhood.name, zipcode=self.neighborhood.zipcode)
        except:
            return self.__repr__()
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
        return self._repr(id=self.id,
                          name=self.name)
    def __str__(self):
        return self.name
    def get_description(self):
        return fillDictionary(modelName='Area', id=self.id, name=self.name)
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
        return self._repr(id=self.id,
                          name=self.name,
                          neighborhood=[n.name for n in self.neighborhoods.all()]
                          )
    def __str__(self):
        return self.name
    def get_description(self):
#        try:
        all_neighb = [n.name for n in self.neighborhoods.all()]
        return fillDictionary(modelName='Street',id=self.id, name=self.name, neighborhood=all_neighb)
            #"{name} ({neighborhood})".format(name=self.name,neighborhood=', '.join(all_neighb))
#        except:
#            return self.__repr__()
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
        return self._repr(id=self.id,
                          name=self.name,
                          zipcode=self.zipcode
                          )
    def __str__(self):
        return self.name
    def get_description(self):
        return fillDictionary(modelName='Neighborhood', id=self.id, name=self.name, zipcode=self.zipcode)


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
    last_change = db.Column(db.DateTime,default=datetime.datetime.utcnow,nullable=False)
    types = db.relationship("PoiCategoryType",secondary=poi_types,
        lazy = "dynamic", backref=db.backref("pois",lazy="dynamic"))
    score = db.Column(db.Integer,nullable=False,default=0)
    osm_type = db.Column(db.String(8))
    osm_id = db.Column(db.Integer,nullable=True)
    osm_other_tags = db.Column(db.String)
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
        try:
            types=[t.__str__() for t in self.types.all()]
            return fillDictionary(modelName='Poi', id=self.id, name=self.name, type=types, address="{}".format(self.location))
        except:
            return self.__repr__()
    def __repr__(self):
        return self._repr(id=self.id,
                          name=self.name,
                          types=[t.__str__() for t in self.types.all()]
                          )
    def __str__(self):
        if self.name:
            return self.name
        else:
            return "No name for POI {}".format(self.id)

class PoiCategory(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(32),index=True,unique=True,nullable=False)
    types = db.relationship("PoiCategoryType",backref="category",lazy="dynamic")
    def __repr__(self):
        return self._repr(id=self.id,
                          name=self.name,
                          types=[t.name for t in self.types.all()]
                          )
    def __str__(self):
        return self.name

class PoiCategoryType(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(32),index=True,nullable=False)
    category_id = db.Column(db.Integer,db.ForeignKey("poi_category.id"),nullable=False)
    subtype = db.Column(db.String(32),index=True)
    def __repr__(self):
        return self._repr(id=self.id,
                          name=self.name,
                          subtype=self.subtype,
                          category=self.category.name
                          )
    def __str__(self):
        return "{name} ({category})".format(
        name=self.name, category=self.category)



def fillDictionary(**kwargs):
    dict_description = {
        'modelName': '', # nome della tabella
        'id': '',
        'name': '',
        'neighborhood':[],
        'address': '',
        'housenumber':'',
        'type':[],
        'zipcode':''
    }
    #pdb.set_trace()
    for key, value in kwargs.items():
        if key in dict_description.keys():
            dict_description[key] = value
    return dict_description

###
# MODELS FOR USERS
###

roles_users_table = db.Table('roles_users',
    db.Column('users_id', db.Integer(), db.ForeignKey('users.id')),
    db.Column('roles_id', db.Integer(), db.ForeignKey('roles.id')),
    info={'bind_key': 'users'})


class Users(db.Model, UserMixin):
    __bind_key__ = 'users'
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(80))
    active = db.Column(db.Boolean(), default=False)
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Roles', secondary=roles_users_table, backref=db.backref('user', lazy=True))
    tokens = db.relationship('Tokens', lazy=True, backref=db.backref('user', lazy=True))

    def __repr__(self):
        return self._repr(id=self.id,
                          email=self.email
                          )
    def __str__(self):
        return self.email
    # def create_token(self, expiration=datetime.timedelta(minutes=10), token_type='base'):
    #     identity_for_token = {'id': self.id,
    #                           'type': token_type}
    #     token_expiration = datetime.datetime.utcnow()+expiration
    #     access_token = create_access_token(identity=identity_for_token,
    #                                        expires_delta=expiration)
    #     add_token_to_database(access_token, self)
    #     return access_token


class Roles(db.Model, RoleMixin):
    __bind_key__ = 'users'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    def __str__(self):
        return self.name
    def __hash__(self):
        return hash(self.name)


class Tokens(db.Model):
    __bind_key__ = 'users'
    id = db.Column(db.Integer(), primary_key=True)
    token = db.Column(db.String(500))
    jti = db.Column(db.String(36))
    token_type_id = db.Column(db.Integer(), db.ForeignKey('token_types.id'), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    revoked = db.Column(db.Boolean())
    expires = db.Column(db.DateTime())
    api_counter = db.relationship('TokenApiCounters', lazy=True, cascade="all, delete-orphan", backref=db.backref('token', lazy=True))

    def to_dict(self):
        return {
            'token_id': self.id,
            'jti': self.jti,
            'token_type': self.token_type,
            #'user_identity': self.user_identity,
            'revoked': self.revoked,
            'expires': self.expires
        }


types_apis_table = db.Table('types_apis',
    db.Column('token_types_id', db.Integer(), db.ForeignKey('token_types.id')),
    db.Column('apis_id', db.Integer(), db.ForeignKey('apis.id')),
    info={'bind_key': 'users'})


class TokenTypes(db.Model):
    __bind_key__ = 'users'
    id = db.Column(db.Integer(), primary_key=True)
    type = db.Column(db.String(80), unique=True)
    tokens = db.relationship('Tokens', lazy=True, backref=db.backref('type', lazy=True))
    permissions = db.relationship('Apis', secondary=types_apis_table, backref=db.backref('token', lazy=True))

    def __repr__(self):
        return self._repr(id=self.id,
                          type=self.type
                          )

    def __str__(self):
        return self.type


class Apis(db.Model):
    __bind_key__ = 'users'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    path = db.Column(db.String(100))
    api_counter = db.relationship('TokenApiCounters', lazy=True, cascade="all, delete-orphan", backref=db.backref('api', lazy=True))

    def __str__(self):
        return self.name


class TokenApiCounters(db.Model):
    __bind_key__ = 'users'
    id = db.Column(db.Integer(), primary_key=True)
    token_id = db.Column(db.Integer(), db.ForeignKey('tokens.id'), nullable=False)
    api_id = db.Column(db.Integer(), db.ForeignKey('apis.id'), nullable=False)
    count = db.Column(db.Integer(), nullable=False, default=0)


class Languages(db.Model):
    __bind_key__ = 'errors'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(30), unique=True)
    code = db.Column(db.String(5), unique=True)
    translations = db.relationship('ErrorTranslations', lazy=True, cascade="all, delete-orphan", backref=db.backref('language', lazy=True))

    def __str__(self):
        return f"{self.code} - {self.name}"


class ErrorGroups(db.Model):
    __bind_key__ = 'errors'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(10), unique=True)
    codes = db.relationship('ErrorCodes', lazy=True, backref=db.backref('group', lazy=True))

    def __str__(self):
        return self.name


class ErrorCodes(db.Model):
    __bind_key__ = 'errors'
    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.Integer(), unique=True)
    description = db.Column(db.String(100))
    group_id = db.Column(db.Integer(), db.ForeignKey('error_groups.id'))
    translations = db.relationship('ErrorTranslations', lazy=True, cascade="all, delete-orphan", backref=db.backref('code', lazy=True))

    def __str__(self):
        return f"{self.code} - {self.description}"


class ErrorTranslations(db.Model):
    __bind_key__ = 'errors'
    id = db.Column(db.Integer(), primary_key=True)
    code_id = db.Column(db.Integer(), db.ForeignKey('error_codes.id'))
    language_id = db.Column(db.Integer(), db.ForeignKey('languages.id'))
    message = db.Column(db.String(200))


###
# FLASK USAGE
###
class FlaskUsage(db.Model):
    __tablename__ = 'flask_usage'
    __bind_key__ = 'trackusage'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(128))
    ua_browser = db.Column(db.String(16))
    ua_language = db.Column(db.String(16))
    ua_platform = db.Column(db.String(16))
    ua_version = db.Column(db.String(16))
    blueprint = db.Column(db.String(16))
    view_args = db.Column(db.String(64))
    status = db.Column(db.Integer)
    remote_addr = db.Column(db.String(24))
    xforwardedfor = db.Column(db.String(24))
    authorization = db.Column(db.Boolean)
    ip_info = db.Column(db.String(1024))
    path = db.Column(db.String(32))
    speed = db.Column(db.Float)
    datetime = db.Column(db.DateTime)
    username = db.Column(db.String(128))
    track_var = db.Column(db.String(128))

####
# TABELLA INIZIATIVE E VOTI
####
class Ideas(db.Model):
    __tablename__ = 'Ideas' # nome della tabella nel file ideas.db
    __bind_key__ = 'ideas' # bind per SQLAlchemy del file ideas.db

    id = db.Column(db.Integer(), primary_key=True)
    idea_title = db.Column(db.String(128))
    idea_short_description = db.Column(db.String(256))
    num_of_votes = db.Column(db.Integer)
    # basic methods
    def __repr__(self):
        return self._repr(id=self.id,
                          title=self.idea_title,
                          description=self.idea_short_description,
                          votes=self.num_of_votes
                          )
    def __str__(self):
        return "{}, {}".format(self.idea_title, self.idea_short_description)
    # get and set
    def get_id(self):
        return self.id
    def get_title(self):
        return self.idea_title
    def set_title(self, new_title):
        self.idea_title = new_title
    def get_description(self):
        return self.idea_short_description
    def set_description(self, new_description):
        self.idea_short_description = new_description
    def get_num_of_votes(self):
        return self.num_of_votes
    def set_num_of_votes(self, new_num):
        self.num_of_votes = new_num
    # up- or down-vote
    def upvote(self):
        self.num_of_votes += 1
    def downvote(self):
        self.num_of_votes -= 1

######
# TABELLE PER FEEDBACK E ERRORI
######
class Feedbacks(db.Model):
    __tablename__ = "Feedbacks"
    __bind_key__ = "feed_err"

    id = db.Column(db.Integer(), primary_key=True)
    version = db.Column(db.String(16))
    datetime = db.Column(db.DateTime)
    name = db.Column(db.String(128))
    email = db.Column(db.String(128))
    category = db.Column(db.String(256))
    searched_string = db.Column(db.String(128))
    searched_start = db.Column(db.String(128))
    searched_end = db.Column(db.String(128))
    found_string = db.Column(db.String(128))
    found_start = db.Column(db.String(128))
    found_end = db.Column(db.String(128))
    feedback = db.Column(db.String(512))
    json = db.Column(db.String())
    start_coord = db.Column(db.String())
    end_coord = db.Column(db.String())
    report = db.Column(db.String(256))
    solved = db.Column(db.Boolean, default=False)

class Errors(db.Model):
    __tablename__ = "Errors"
    __bind_key__ = "feed_err"

    id = db.Column(db.Integer(), primary_key=True)
    version = db.Column(db.String(16))
    datetime = db.Column(db.DateTime)
    error_type = db.Column(db.String(256))
    error_message = db.Column(db.String(256))
    url = db.Column(db.String(256))
    method = db.Column(db.String(256))
    browser = db.Column(db.String(256))
    pickle = db.Column(db.String(256))
    report = db.Column(db.String(256))
    solved = db.Column(db.Boolean, default=False)
