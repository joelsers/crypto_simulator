import os

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, BuyForm, SellForm
from models import db, connect_db, User, Crypto, UserCrypto
import requests

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///crypto_sim'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] =  'kakakakak'
toolbar = DebugToolbarExtension(app)

connect_db(app)

BASE_URL = 'https://api1.binance.com/api/v3/'

# total = 0

# crypto_request = requests.get(f'{BASE_URL}ticker/price')
# crypto_json = crypto_request.json()

# for x in crypto_json:
#     if crypto_json[total]["symbol"][-4:] == "USDT":
#         crypto = Crypto(name = crypto_json[total]["symbol"], price = crypto_json[total]["price"], volume = 0)
#         total += 1
#         db.session.add(crypto)
#         db.session.commit()
#     else:
#         total +=1

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id

def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                USDT=form.USDT.data,
            )
            db.session.commit()

            bought_crypto = UserCrypto(
            name = "USDCUSDT",
            price = 1,
            amount=form.USDT.data,
            user_crypto = user.id
            )
            db.session.add(bought_crypto)
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)

@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()

    flash("You have successfully logged out.", 'success')
    return redirect("/login")





@app.route('/')
def redirect_home():

    return redirect('/cryptos')

@app.route('/cryptos')
def show_home():

    total = 0

    crypto_request = requests.get(f'{BASE_URL}ticker/price')
    crypto_json = crypto_request.json()

    for x in crypto_json:
        if crypto_json[total]["symbol"][-4:] == "USDT":
            crypto_symbol = crypto_json[total]["symbol"]

            crypto_price = crypto_json[total]["price"]
        
            edit_crypto = Crypto.query.filter_by(name = crypto_symbol).first()
        
            edit_crypto.price = crypto_price
            total += 1
            db.session.add(edit_crypto)
            db.session.commit()
        else:
            total += 1

    cryptos = Crypto.query.all()
       
    return render_template('home.html',cryptos = cryptos)


@app.route('/user/<user_id>')
def show_user(user_id):


    total = 0

    crypto_request = requests.get(f'{BASE_URL}ticker/price')
    crypto_json = crypto_request.json()

    user = User.query.get_or_404(user_id)

    users_cryptos = [crypto for crypto in user.crypto]

    users_cryptos_names = [crypto.name for crypto in users_cryptos]

    value = 0

    for sym in crypto_json:
        crypto_symbol = crypto_json[total]["symbol"]
        crypto_price = crypto_json[total]["price"]
        if crypto_symbol in users_cryptos_names:

            edit_crypto = UserCrypto.query.filter_by(name = crypto_symbol).first()
            
        
            edit_crypto.price = crypto_price


            db.session.add(edit_crypto)
            db.session.commit()
            
            value += edit_crypto.price * edit_crypto.amount

            total+=1
        else:
            total +=1

        

    

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/") 
    else:
        return render_template('users/user.html', user=user, users_cryptos=users_cryptos, value = value)



@app.route('/cryptos/<crypto_name>', methods = ['GET', 'POST'])
def show_crypto(crypto_name):

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    crypto = Crypto.query.filter_by(name = crypto_name).first()



    buyform = BuyForm()

    sellform = SellForm()

    if buyform.validate_on_submit():

        bought_crypto = UserCrypto(
            name = crypto.name,
            price = crypto.price,
            amount = buyform.amount.data,
            user_crypto = g.user.id
            )

        db.session.add(bought_crypto)
        db.session.commit()

        edit_user = User.query.get_or_404(g.user.id)

        users_cryptos = [crypto for crypto in edit_user.crypto]

        users_cryptos_names = [crypto.name for crypto in users_cryptos]

        usdt = users_cryptos_names.index("USDCUSDT")

        edit_user.crypto[usdt].amount -= bought_crypto.price * bought_crypto.amount

        db.session.add(edit_user)
        db.session.commit()

        return redirect(f'/user/{g.user.id}')
    else:
        return render_template('crypto.html', crypto = crypto, buyform = buyform, sellform = sellform)

    
    

    if sellform.validate_on_submit():

        user = User.query.get_or_404(g.user.id)

        users_cryptos = [crypto for crypto in user.crypto]

        users_cryptos_names = [crypto.name for crypto in users_cryptos]


        for user_crypto in users_cryptos:
            if crypto.name == user_crypto.name:
                usdt = users_cryptos_names.index("USDCUSDT")
                sold_coin = users_cryptos_names.index(crypto.name)
                user.crypto[sold_coin].amount -= sellform.amount.data
                user.crypto[usdt].amount += user_crypto.price * sellform.amount.data

                db.session.add(user)
                db.session.commit()

                return redirect(f'/user/{g.user.id}')
            else:
                return render_template('crypto.html', crypto = crypto, buyform = buyform, sellform = sellform)




@app.route('/test/<user_id>')
def test_route(user_id):

    user = User.query.get_or_404(user_id)

    users_cryptos = [crypto for crypto in user.crypto]

    users_cryptos_names = [crypto.name for crypto in users_cryptos]

    usdt = users_cryptos_names.index("USDCUSDT")

    return render_template('users/test.html', user=user, usdt = usdt)


# @app.route('/cryptos/<int:crypto_id>/buy', methods = ['POST'])
# def buy_crypto(crypto_id):

#     crypto = Crypto.query.get_or_404(crypto_id)

