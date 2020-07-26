import os
basedir = os.path.abspath(os.path.dirname(__file__))
class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'indovina-indovinello'
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'dequa.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER') #"smtps.aruba.it"
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25) #587
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None #1
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') #"info@dequa.it"
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') # QUA INSERIRE LA PASSWORD DELL'ACCOUNT
    ADMINS = ['info@dequa.it']
