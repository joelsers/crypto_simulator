from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy



bcrypt = Bcrypt()

db = SQLAlchemy()


def connect_db(app):

    db.app = app
    db.init_app(app)


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )

    password = db.Column(
        db.Text,
        nullable=False
    )

    USDT = db.Column(
        db.Float,
        nullable=False,
        unique=False,
    )

    crypto = db.relationship("UserCrypto", backref="user", cascade="all, delete-orphan")

    

    @classmethod
    def signup(cls, username, email, password, USDT):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            USDT = USDT
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.
        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False


class Crypto(db.Model):
    """An individual crypto ("warble")."""

    __tablename__ = 'cryptos'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(140),
        nullable=False,
        unique = True
    )

    price = db.Column(
        db.Float,
        nullable=False,
    )

    # volume = db.Column(
    #     db.Float,
    #     nullable = False
    # )

    def serialize(self):
        return {
            'id': self.id,
            'name':self.name,
            'price':self.price
            # 'volume':self.volume
        }

    

class UserCrypto(db.Model):

    __tablename__ = 'users_crypto'

    id = db.Column(db.Integer, primary_key = True, autoincrement = True)

    name = db.Column(
        db.String(140),
        nullable=False,
        unique = False
    )

    price = db.Column(
        db.Float,
        nullable=False,
    )

    amount = db.Column(db.Float, nullable = False)

    user_crypto = db.Column(db.Integer, db.ForeignKey('users.id'))

    def serialize(self):
        return {
            'id': self.id,
            'name':self.name,
            'price':self.price,
            'amount': self.amount,
            'user-id':self.user_crypto
        }





