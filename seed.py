from models import db, Crypto
from app import app, seed_cryptos

db.drop_all()
db.create_all()

# db.create_all()

seed_cryptos()