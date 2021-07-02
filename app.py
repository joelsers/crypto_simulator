import os
import re

from flask import Flask, render_template, request, flash, redirect, session, g, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc
from forms import UserAddForm, LoginForm, BuyForm, SellForm
from models import db, connect_db, User, Crypto, UserCrypto
import requests


CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL','postgresql:///crypto_sim')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] =  os.environ.get('SECRET_KEY', 'dyFN9ghkd5778')
toolbar = DebugToolbarExtension(app)

connect_db(app)

BASE_URL = 'https://api1.binance.com/api/v3/'

def seed_cryptos():
    total = 0

    crypto_request = requests.get(f'{BASE_URL}ticker/price')
    crypto_json = crypto_request.json()
    
    crypto_volume_request = requests.get(f'{BASE_URL}ticker/24hr')
    crypto_volume_json = crypto_volume_request.json()

    for crypto_currency in crypto_json:
        if crypto_json[total]["symbol"][-4:] == "USDT":
            crypto = Crypto(name = crypto_json[total]["symbol"], price = crypto_json[total]["price"], volume = (float(crypto_volume_json[total]["volume"])* float(crypto_json[total]["price"])))
            total += 1
            db.session.add(crypto)
            db.session.commit()
        else:
            total +=1


def update_crypto_price(crypto_name):
    total = 0

    crypto_request = requests.get(f'{BASE_URL}ticker/price')
    crypto_json = crypto_request.json()

    crypto = Crypto.query.filter_by(name = crypto_name).first()

    for crypto_currency in crypto_json:
        try:
            if crypto_name == crypto_json[total]["symbol"]:
                crypto.price = crypto_json[total]["price"]
                total += 1
                db.session.add(crypto)
                db.session.commit()
            else:
                total +=1
        except AttributeError:
            print('Ooops. Something happened')


def update_user_crypto_price(crypto_name):
    total = 0

    crypto_request = requests.get(f'{BASE_URL}ticker/price')
    crypto_json = crypto_request.json()

    crypto = UserCrypto.query.filter_by(name = crypto_name).first()

    for crypto_currency in crypto_json:
        try:
            if crypto_name == crypto_json[total]["symbol"]:
                crypto.price = crypto_json[total]["price"]
                total += 1
                db.session.add(crypto)
                db.session.commit()
            else:
                total +=1
        except AttributeError:
            print('Ooops. Something happened')

def buy_crypto_func(crypto_name, form):

    crypto = Crypto.query.filter_by(name = crypto_name).first()

    user = User.query.get_or_404(g.user.id)

    users_usdt = UserCrypto.query.filter_by(name = 'USDCUSDT')

    usdts = [usdt for usdt in users_usdt]

    user_crypto = [crypto for crypto in user.crypto]

    crypto_names = [crypto.name for crypto in user_crypto]

    
        

    for usdt in usdts:
        if user.id == usdt.user_crypto:
            user_money = usdt

    update_crypto_price(crypto_name)

    if crypto_name == 'USDCUSDT':
        flash("You can't trade that directly", "danger")
        return False
    print(f'*********************************************{float(form.amount.data)}------------------------------------------------------')
    if user_money.amount - (float(form.amount.data) * crypto.price) > 1 and crypto.name not in crypto_names and float(form.amount.data) > 0.00000000:

        bought_crypto = UserCrypto(
            name = crypto.name,
            price = crypto.price,
            amount = float(form.amount.data),
            user_crypto = g.user.id
            )
        
        db.session.add(bought_crypto)
        db.session.commit()


        user_money.amount -= bought_crypto.price * bought_crypto.amount

        db.session.add(user)
        db.session.commit()

        return True

        

    elif user_money.amount - (float(form.amount.data) * crypto.price) > 1 and crypto.name in crypto_names:

        bought_coin = crypto_names.index(crypto.name)

        user.crypto[bought_coin].amount += float(form.amount.data)
        user_money.amount -= user.crypto[bought_coin].price * float(form.amount.data)
        print(f'************************************{float(form.amount.data)}------------------------------------------------------')
        db.session.add(user)
        db.session.commit()
        return True
        

    else:
        print(f'************************************{float(form.amount.data)}------------------------------------------------------')
        flash("You can't buy that much", "danger")
        return False


    

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
            flash("Username or Email already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    if g.user:
        flash("Already logged in", "danger")
        return redirect(f"/user/{g.user.id}")

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

@app.errorhandler(500)
def page_not_found(e):
    
    return render_template('500.html')

@app.errorhandler(404)
def page_not_found(e):
    
    return render_template('404.html')

@app.route('/')
def redirect_home():

    return redirect('/cryptos')

# @app.route('/test')
# def test_volume():

#     crypto_volume_request = requests.get(f'{BASE_URL}ticker/24hr')
#     crypto_json = crypto_volume_request.json()
#     print(crypto_json)
#     return render_template('test.html')

ROWS_PER_PAGE = 10

@app.route('/cryptos')
def show_home():
    
    # total = 0

    # crypto_request = requests.get(f'{BASE_URL}ticker/price')
    # crypto_volume_request = requests.get(f'{BASE_URL}ticker/24hr')
    # crypto_json = crypto_request.json()
    # print(crypto_volume_request)
    # for crypto in crypto_json:
    #     try:
    #         if crypto_json[total]["symbol"][-4:] == "USDT":
    #             crypto_symbol = crypto_json[total]["symbol"]

    #             crypto_price = crypto_json[total]["price"]
        
    #             edit_crypto = Crypto.query.filter_by(name = crypto_symbol).first()
        
    #             edit_crypto.price = crypto_price
    #             total += 1
    #             db.session.add(edit_crypto)
                
    #         else:
    #             total += 1
    #     except AttributeError:
    #         print("uh oh. something happened")

    

    search = request.args.get('q')
    searched = False
    if not search:
        page = request.args.get('page',1,type=int)
        cryptos = Crypto.query.order_by(Crypto.volume.desc()).paginate(page = page, per_page=ROWS_PER_PAGE)
    else:
        searched = True
        cryptos = Crypto.query.filter(Crypto.name.like(f"%{search.upper()}%")).all()

    db.session.commit()
       
    return render_template('home.html',cryptos = cryptos, searched = searched)
    
percent_change = 0
user_positive = True

@app.route('/user/<user_id>')
def show_user(user_id):
    

    user = User.query.get_or_404(user_id)

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/login")
    elif g.user.id != user.id:
        flash("Access unauthorized.", "danger")
        return redirect(f"/user/{g.user.id}")

    crypto_request = requests.get(f'{BASE_URL}ticker/price')
    crypto_json = crypto_request.json()

    crypto_volume_request = requests.get(f'{BASE_URL}ticker/24hr')
    crypto_volume_json = crypto_volume_request.json()

    users_cryptos = [crypto for crypto in user.crypto if crypto.amount > 0.000000009999999999999999]
    
    users_cryptos_names = [crypto.name for crypto in users_cryptos ]
    total = 0
    value = 0

    
    for crypto in crypto_json:
        crypto_symbol = crypto_json[total]["symbol"]
        crypto_price = crypto_json[total]["price"]
        crypto_open_price = crypto_volume_json[total]["openPrice"]
        if crypto_symbol in users_cryptos_names:
            
            edit_crypto = UserCrypto.query.order_by(UserCrypto.price.desc()).filter_by(name = crypto_symbol).first()
            
            edit_crypto.price = crypto_price
            
                
            db.session.add(edit_crypto)
            db.session.commit()
            
            total+=1
        else:
            total +=1

    for crypto in users_cryptos:
        
        value += crypto.price * crypto.amount

    percent_change = 0

    difference = value - user.USDT
    negative_difference = user.USDT - value

    if difference >= 0:
        user_positive = True
        percent_change = difference/ (user.USDT * 100)
    elif difference < 0:
        user_positive = False
        percent_change = negative_difference / (user.USDT * 100)
        

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/login")
    else:
        return render_template('users/user.html', user=user, users_cryptos=users_cryptos, value = value, user_positive = user_positive, percent_change = percent_change)



@app.route('/cryptos/<crypto_name>', methods = ['GET'])
def show_crypto(crypto_name):

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/login")

    update_crypto_price(crypto_name)

    crypto_kline_request = requests.get(f'{BASE_URL}klines?symbol={crypto_name}&interval=3m')
    crypto_kline_json = crypto_kline_request.json()
    

    user = User.query.get_or_404(g.user.id)

    users_usdt = UserCrypto.query.filter_by(name = 'USDCUSDT')

    usdts = [usdt for usdt in users_usdt]

    user_crypto = [crypto for crypto in user.crypto]

    crypto_names = [crypto.name for crypto in user_crypto]

    users_cryptos_names = [crypto.name for crypto in user_crypto]

    crypto = Crypto.query.filter_by(name = crypto_name).first()

    try:
        coin = users_cryptos_names.index(crypto.name)
        crypto_amount = user.crypto[coin].amount
    except ValueError:
        crypto_amount = 0
        
    for usdt in usdts:
        if user.id == usdt.user_crypto:
            user_money = usdt

    USDT = user_money.amount

    crypto = Crypto.query.filter_by(name = crypto_name).first()
    
    difference = float(crypto.price) - float(crypto_kline_json[0][1])
    negative_difference = float(crypto_kline_json[0][1]) - float(crypto.price)

    if difference >= 0:
        user_positive = True
        percent_change = difference / float(crypto_kline_json[0][1]) * 100
    elif difference < 0:
        user_positive = False
        percent_change = negative_difference / float(crypto_kline_json[0][1]) * 100

    return render_template('crypto.html', crypto = crypto, USDT = USDT, crypto_amount = crypto_amount, percent_change=percent_change,user_positive=user_positive)


@app.route('/cryptos/<crypto_name>/buy', methods = ['GET', 'POST'])
def buy_crypto(crypto_name):

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/login")

    user = User.query.get_or_404(g.user.id)

    users_usdt = UserCrypto.query.filter_by(name = 'USDCUSDT')

    usdts = [usdt for usdt in users_usdt]

    user_crypto = [crypto for crypto in user.crypto]

    crypto_names = [crypto.name for crypto in user_crypto]

    users_cryptos_names = [crypto.name for crypto in user_crypto]

    crypto = Crypto.query.filter_by(name = crypto_name).first()

    try:
        bought_coin = users_cryptos_names.index(crypto.name)
        crypto_amount = user.crypto[bought_coin].amount
    except ValueError:
        crypto_amount = 0
        

    for usdt in usdts:
        if user.id == usdt.user_crypto:
            user_money = usdt

    USDT = user_money.amount

    crypto = Crypto.query.filter_by(name = crypto_name).first()
    
    if crypto_name == 'USDCUSDT':
        flash("You can't trade that directly", "danger")
        return redirect('/cryptos/USDCUSDT')

    crypto = Crypto.query.filter_by(name = crypto_name).first()

    update_crypto_price(crypto_name)

    form_max = (USDT- 5) / crypto.price

    buyform = BuyForm()

    if buyform.validate_on_submit():
        
        if buy_crypto_func(crypto_name, buyform):
        
            return redirect(f'/user/{g.user.id}')
        else:
            return redirect(f'/cryptos/{crypto.name}/buy')

    return render_template('crypto_buy.html', crypto = crypto, buyform = buyform, USDT = USDT, crypto_amount = crypto_amount, form_max = form_max)


@app.route('/cryptos/<crypto_name>/sell', methods = ['GET', 'POST'])
def sell_crypto(crypto_name):


    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/login")

    crypto = Crypto.query.filter_by(name = crypto_name).first()

    update_crypto_price(crypto_name)

    user = User.query.get_or_404(g.user.id)

    users_usdt = UserCrypto.query.filter_by(name = 'USDCUSDT')

    usdts = [usdt for usdt in users_usdt]

    user_crypto = [crypto for crypto in user.crypto]

    crypto_names = [crypto.name for crypto in user_crypto]

    users_cryptos_names = [crypto.name for crypto in user_crypto]
    try:
        sold_coin = users_cryptos_names.index(crypto.name)
        crypto_amount = user.crypto[sold_coin].amount
    except ValueError:
        crypto_amount = 0
        
    
        

    for usdt in usdts:
        if user.id == usdt.user_crypto:
            user_money = usdt

    USDT = user_money.amount

    if crypto_name == 'USDCUSDT':
        flash("You can't trade that directly", "danger")
        return redirect('/cryptos/USDCUSDT')

    sellform = SellForm()

    if sellform.validate_on_submit():

        update_crypto_price(crypto_name)

        user = User.query.get_or_404(g.user.id)

        users_cryptos = [crypto for crypto in user.crypto]

        users_cryptos_names = [crypto.name for crypto in users_cryptos]

        for user_crypto in users_cryptos:
            if crypto.name == user_crypto.name:
                usdt = users_cryptos_names.index("USDCUSDT")
                sold_coin = users_cryptos_names.index(crypto.name)
                
                if float(sellform.amount.data) <= user.crypto[sold_coin].amount and float(sellform.amount.data) > 0.00000000:
                    user.crypto[sold_coin].amount -= float(sellform.amount.data)
                    user.crypto[usdt].amount += user_crypto.price * float(sellform.amount.data)

                    db.session.add(user)
                    db.session.commit()

                    return redirect(f'/user/{g.user.id}')
                else:
                    flash("You can't sell that much", "danger")
                    return redirect(f"/cryptos/{crypto.name}/sell")

    return render_template('crypto_sell.html', crypto = crypto, sellform = sellform, USDT = USDT, crypto_amount = crypto_amount)


@app.route('/api')
def test_api():

    return jsonify('{}')


@app.route('/api/cryptos')
def get_all_cryptos():

    cryptos = [crypto.serialize() for crypto in Crypto.query.all()]

    return jsonify(cryptos = cryptos)


@app.route('/api/<crypto_name>')
def get_crypto_api(crypto_name):

    crypto = Crypto.query.filter_by(name = crypto_name).first()

    response = crypto.serialize()

    return jsonify(response = response)

@app.route('/api/buy/<crypto_name>', methods = ["POST"])
def buy_crypto_api(crypto_name):


    crypto = Crypto.query.filter_by(name = crypto_name).first()

    user = User.query.get_or_404(request.json["user-id"])

    total = 0

    crypto_request = requests.get(f'{BASE_URL}ticker/price')
    crypto_json = crypto_request.json()

    users_cryptos = [crypto for crypto in user.crypto]

    users_cryptos_names = [crypto.name for crypto in users_cryptos]

    usdt = users_cryptos_names.index("USDCUSDT")

    for sym in crypto_json:
        crypto_symbol = crypto_json[total]["symbol"]
        crypto_price = crypto_json[total]["price"]

        if crypto_symbol in users_cryptos_names:

            edit_crypto = UserCrypto.query.filter_by(name = crypto_symbol).first()
            
            edit_crypto.price = crypto_price

            db.session.add(edit_crypto)
            db.session.commit()

            total+=1
        else:
            total +=1

    if crypto.price * request.json["amount"] < user.USDT - 1 and crypto.name not in users_cryptos_names:

        bought_crypto = UserCrypto(
                name = crypto_name,
                price = crypto.price,
                amount = request.json["amount"],
                user_crypto = request.json["user-id"]
                )

        db.session.add(bought_crypto)
        db.session.commit()

        user.crypto[usdt].amount -= bought_crypto.price * bought_crypto.amount

        db.session.add(user)
        db.session.commit()

        response = jsonify(bought_crypto=bought_crypto.serialize())

        return (response, 201)

    elif request.json["amount"] * crypto.price < user.USDT - 1 and crypto.name in users_cryptos_names:

        bought_coin = users_cryptos_names.index(crypto.name)

        user.crypto[bought_coin].amount += request.json["amount"]
        user.crypto[usdt].amount -= user.crypto[bought_coin].price * request.json["amount"]

        db.session.add(user)
        db.session.commit()

        response = {"name":crypto_name,"price" : crypto.price,"amount" : request.json["amount"], "user-id" : request.json["user-id"]}

        return (response, 201)
    
    else:

        return jsonify('{error}')

    

@app.route('/api/sell/<crypto_name>', methods = ["POST"])
def sell_crypto_api(crypto_name):

    crypto = Crypto.query.filter_by(name = crypto_name).first()

    user = User.query.get_or_404(request.json["user-id"])

    users_cryptos = [crypto for crypto in user.crypto]

    users_cryptos_names = [crypto.name for crypto in users_cryptos]

    for user_crypto in users_cryptos:
        if crypto.name == user_crypto.name:
            usdt = users_cryptos_names.index("USDCUSDT")
            sold_coin = users_cryptos_names.index(crypto.name)

            if request.json["amount"] <= user.crypto[sold_coin].amount:
                user.crypto[sold_coin].amount -= request.json["amount"]
                user.crypto[usdt].amount += user_crypto.price * request.json["amount"]

                db.session.add(user)
                db.session.commit()

                response = {"name":crypto_name,"price" : crypto.price,"amount" : request.json["amount"], "user-id" : request.json["user-id"]}
                
                return (response, 201)

            else:

                return jsonify({"can't sell that much"})
                

