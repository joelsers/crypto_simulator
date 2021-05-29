import unittest
from unittest import TestCase

from app import app
from models import db, connect_db, User, Crypto, UserCrypto

# Use test database and don't clutter tests with SQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///crypto_sim'
app.config['SQLALCHEMY_ECHO'] = False

# Make Flask errors be real errors, rather than HTML pages with error info
app.config['TESTING'] = True

db.drop_all()
db.create_all()


class CryptoSimulatorTestCase(TestCase):

    def setUp(self):

        test_user = User(email = 'email@email.com', username = 'user', password = 'password', USDT = 1)

        db.session.add(test_user)
        db.session.commit()

        

        test_crypto = Crypto(name ="BTCUSDT", price = 1, volume = 0)

        db.session.add(test_crypto)
        db.session.commit()

        

        test_user_crypto = UserCrypto(name = "USDCUSDT", price = 1, amount = 1, user_crypto = 1)

        db.session.add(test_user_crypto)
        db.session.commit()

        

    def tearDown(self):

        db.session.rollback()

    def test_buy_crypto(self):

        with app.test_client() as client:
            url = "/cryptos/buy/BTCUSDT"
            user = User.query.get_or_404(1)
            crypto = Crypto.query.get_or_404(1)
            user_crypto = UserCrypto.query.get_or_404(1)





            resp = client.get(url)
            print(resp)

            
            

            self.assertEqual(resp.status_code, 201)

