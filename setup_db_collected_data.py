from app import app, db

db.create_all(bind="collected_data")
