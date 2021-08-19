# PYTHON SCRIPT TO POPULATE
# dequa_config_data DATABASE
import os,sys
# IMPORT FOR THE DATABASE - db is the database object
from app import app, db
from app.models import *
import json, pdb

print("&" * 40)
print("Loading the default config values for dequa backend..")
print("&" * 40)
print("")
folder = os.path.join(os.getcwd(), "config")

db.create_all(bind="config_data")

## Languages
languages_file = os.path.join(folder, 'languages.json')
with open(languages_file) as f:
    languages = json.load(f)

for language in languages:
    lang = Languages(name=language['name'],
                     code=language['code'],
                     id=language['id'])
    db.session.add(lang)

try:
    # forse non serve
    db.session.commit()
    print("Added languages in the database")
except:
    db.session.rollback()
    warnings.warn("Error while committing languages!")

error_groups_file = os.path.join(folder, 'error_groups.json')
with open(error_groups_file) as f:
    error_groups = json.load(f)

## ErrorGroups
for error_group in error_groups:
    err_group = ErrorGroups(id=error_group['id'],
                            name=error_group['name'])
    db.session.add(err_group)

try:
    # forse non serve
    db.session.commit()
    print("Added error groups in the database")
except:
    db.session.rollback()
    warnings.warn("Error while committing error groups!")

## ErrorCodes
error_codes_file = os.path.join(folder, 'error_codes.json')
with open(error_codes_file) as f:
    error_codes = json.load(f)

for error_code in error_codes:
    err_code = ErrorCodes(id=error_code['id'],
                          code=error_code['code'],
                          description=error_code['description'],
                          group_id=error_code['group_id'])
    db.session.add(err_code)

try:
    # forse non serve
    db.session.commit()
    print("Added error codes in the database")
except:
    db.session.rollback()
    warnings.warn("Error while committing error codes!")

## ErrorTranslations
error_translation_file = os.path.join(folder, 'error_translations.json')
with open(error_translation_file) as f:
    error_translations = json.load(f)

for error_translation in error_translations:
    err_translation = ErrorTranslations(id=error_translation['id'],
                                  code_id=error_translation['code_id'],
                                  language_id=error_translation['language_id'],
                                  message=error_translation['message'])
    db.session.add(err_translation)

try:
    # forse non serve
    db.session.commit()
    print("Added error translations in the database")
except:
    db.session.rollback()
    warnings.warn("Error while committing error translations!")
