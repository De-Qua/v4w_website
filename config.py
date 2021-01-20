import os
basedir = os.path.abspath(os.path.dirname(__file__))
class Config(object):
    # Version
    VERSION = '0.1.4'
    API_VERSION = '1.0'
    # Secret key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'indovina-indovinello'
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'dequa.db')
    SQLALCHEMY_BINDS = {
        "trackusage": 'sqlite:///' + os.path.join(basedir, 'trackusage.db'),
        "users": 'sqlite:///' + os.path.join(basedir, 'users.db'),
        "ideas": 'sqlite:///' + os.path.join(basedir, 'ideas.db'),
        "feed_err": 'sqlite:///' + os.path.join(basedir, 'feed_err.db')
        }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # TrackUsage
    TRACK_USAGE_USE_FREEGEOIP = False
    TRACK_USAGE_INCLUDE_OR_EXCLUDE_VIEWS = 'include'
    TRACK_USAGE_COOKIE = False
    # Flask-Security
    SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT') or 'indovina-indovinello'
    SECURITY_POST_LOGIN_VIEW = '/admin/'
    SECURITY_POST_LOGOUT_VIEW = '/admin/'
    SECURITY_POST_REGISTER_VIEW = '/admin/'
    SECURITY_REGISTERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False
    # Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER') #"smtps.aruba.it"
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25) #587
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None #1
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') #"info@dequa.it"
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') # QUA INSERIRE LA PASSWORD DELL'ACCOUNT
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') #"info@dequa.it"
    ADMINS = ['info@dequa.it']
    # Sitemap
    # SITEMAP_URL_SCHEME = 'HTTPS'
    # SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS = False # se True, lista tutte (anche admin ecc) le pagine sulla sitemap
    # Token
    JWT_SECRET_KEY = SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'indovina-indovinello'
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
