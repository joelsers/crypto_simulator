from models import db, Crypto
from app import app, seed_cryptos
# from sqlalchemy import create_engine

# engine = create_engine('postgresql://')
db.drop_all()
# Crypto.__table__.drop(engine)
db.create_all()

# db.create_all()

seed_cryptos()