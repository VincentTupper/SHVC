from flask import Flask, render_template, url_for, flash, redirect, request, abort, session
from forms import get_db_connection, get_product, get_username, get_usertype, get_basket, get_totalprice
import sqlite3 as sql
from flask_bcrypt import Bcrypt
from flask_session import Session
import datetime


app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'acd65166a5237a864d37'
Session(app)


@app.errorhandler(404)
def error404(e):
	return render_template('404.html')

@app.route("/")
@app.route("/index")
def index():
	print(get_usertype(session))
	return render_template('index.html', username = get_username(session), usertype = get_usertype(session))

@app.route("/about")
def about():
	return render_template('about.html', username = get_username(session), usertype = get_usertype(session))

@app.route("/shop")
def shop():
	con = sql.connect('shvc.db')
	con.row_factory = sql.Row
	cur = con.cursor()
	cur.execute("select * from Products")
	productshop = cur.fetchall();

	cur.execute("select * from ProductPop ORDER BY Count DESC LIMIT 5")
	productpop = cur.fetchall();
	return render_template('shop.html', productshop=productshop, productpop=productpop, username = get_username(session), usertype = get_usertype(session))

@app.route("/addtobasket", methods = ['POST', 'GET'])
def addtobasket():
	if request.method == 'POST':
		product = request.form['product']
		price = request.form['price']
		quantity = request.form['quantity']

		if get_basket(session) == '':
			session['Basket'] = []
		session['Basket'].append([product, quantity, price])

		message = product + ' x' + quantity + ' successfully added to basket!'
		flash(message, 'success')
		
	con = sql.connect('shvc.db')
	con.row_factory = sql.Row
	cur = con.cursor()
	cur.execute("select * from Products")
	productshop = cur.fetchall();
	cur.execute("select * from ProductPop ORDER BY Count DESC LIMIT 5")
	productpop = cur.fetchall();
	return render_template('shop.html', productshop=productshop, productpop=productpop, username = get_username(session), usertype = get_usertype(session))
	con.close()

@app.route("/cart", methods = ['POST', 'GET'])
def cart():
	return render_template('cart.html', username = get_username(session), usertype = get_usertype(session), basket = session['Basket'], totalprice = get_totalprice(session))

@app.route("/removefrombasket", methods = ['POST', 'GET'])
def removefrombasket():
	if request.method == 'POST':
		product = int(request.form['product'])-1
		del session['Basket'][product]
	return render_template('cart.html', username = get_username(session), usertype = get_usertype(session), basket = session['Basket'], totalprice = get_totalprice(session))

@app.route("/removeallfrombasket", methods = ['POST', 'GET'])
def removeallfrombasket():
	if request.method == 'POST':
		session['Basket'] = ''
		flash('Successfully removed all items from basket', 'success')
	return render_template('cart.html', username = get_username(session), usertype = get_usertype(session), basket = session['Basket'])

@app.route("/checkout", methods = ['POST', 'GET'])
def checkout():
	for x in session['Basket']:
		product = x[0]
		with sql.connect('shvc.db') as con:
			try:
				cur = con.cursor()
				stock = cur.execute("SELECT Stock FROM Products WHERE Product = '?' ".replace("?", product)).fetchall()[0][0]
				if stock == 0 or stock <0:
					message = product + ' is out of stock! Please choose another product!'
					flash (message, 'danger')
					return render_template('cart.html', username = get_username(session), usertype = get_usertype(session), basket = session['Basket'], totalprice = get_totalprice(session))
				stock = stock -1
				cur.execute("UPDATE Products SET stock=? WHERE Product=?", (stock, product))

				count = cur.execute("SELECT count FROM ProductPop WHERE Product='?' ".replace("?", product)).fetchall()[0][0]
				count += 1
				cur.execute("UPDATE ProductPop SET count=? WHERE Product=?", (count, product))
			except Exception as error:
				flash(error)

	username = get_username(session)
	products = ''
	quantity = ''
	date = datetime.datetime.now()
	datex = date.strftime("%x")
	totalprice = get_totalprice(session)
	for x in session['Basket']:
		products = products + x[0] + ','
		quantity = quantity + x[1] + ','
	products = products[:-1]
	quantity = quantity[:-1]
	
	with sql.connect('shvc.db') as con:
		try:
			cur = con.cursor()
			userid = cur.execute("SELECT userid FROM User WHERE username = '?' ".replace("?", username)).fetchall()[0][0]
			cur.execute("INSERT INTO Orders (UserID, Product, Quantity, TotalPrice, Date) VALUES(?,?,?,?,?)", (userid, products, quantity, totalprice, datex))
		except Exception as error:
			flash(error)

	flash('Thank you for Shopping with SHVC, Please collect your order from the bar!', 'success')
	session['Basket'] = ''
	return render_template('cart.html', username = get_username(session), usertype = get_usertype(session), basket = session['Basket'])
	con.close()

@app.route("/datalist")
def datalist():
	con = sql.connect("shvc.db")
	con.row_factory = sql.Row
	cur = con.cursor()
	cur.execute("select * from Products")
	productrows = cur.fetchall();
	cur.execute("select * from User")
	userows = cur.fetchall();
	return render_template('datalist.html', productrows=productrows, userows=userows, username = get_username(session), usertype = get_usertype(session))

@app.route("/admin")
def admin():
	return render_template('admin.html', username = get_username(session), usertype = get_usertype(session))

@app.route("/addrec", methods = ['POST', 'GET'])
def addrec():
	if request.method == 'POST':
		ean = request.form['ean']
		product = request.form['prd']
		price = request.form['prc']
		stock = request.form['stk']

		if not ean:
			flash('An EAN is required!', 'danger')
		elif not product:
			flash('A Product name is required!', 'danger')
		elif not price:
			flash('A Price is required!', 'danger')
		elif not stock:
			flash('A Stock quantity is required!', 'danger')
		else:
			with sql.connect("shvc.db") as con:
				try:
					cur = con.cursor()
					cur.execute("INSERT INTO products (ean, product, price, stock) VALUES(?,?,?,?)", (ean, product, price, stock))
					con.commit()
					flash('Product has been added!', 'success')
				except:
					flash('ProductID already exists! Please try another', 'danger')
	return render_template('admin.html', username = get_username(session), usertype = get_usertype(session))
	con.close()

@app.route("/edit", methods=('GET', 'POST'))
def edit():
	if request.method == 'POST':
		ean = request.form['ean']
		productid = request.form['productid']
		product = request.form['product']
		price = request.form['price']
		stock = request.form['stock']

		if not productid:
			flash('A ProductID is required!', 'danger')
		elif not ean:
			flash('An EAN is required!', 'danger')
		elif not product:
			flash('A ProductID is required!', 'danger')
		elif not price:
			flash('A Price is required!', 'danger')
		elif not stock:
			flash('A Stock quantity is required!', 'danger')
		else:
			try:
				with sql.connect("shvc.db") as con:	
					cur = con.cursor()
					cur.execute("UPDATE products SET  ean=?, product=?, price=?, stock=? WHERE productid = ?", (ean, product, price, stock, productid))
					con.commit()
					flash('Product successfully updated!', 'success')
			except:
				flash('Error updating product!', 'danger')
	return render_template('admin.html', username = get_username(session), usertype = get_usertype(session))
	con.close()

@app.route("/register", methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		email = request.form['email']
		username = request.form['username']
		password = request.form['password']
		confirm_password = request.form['confirm_password']
		usertype = 'User'

		if password != confirm_password:
			flash('Passwords do not match!', 'danger')
			return render_template('register.html', username = get_username(session), usertype = get_usertype(session))

		for letter in username:
			if (not letter.isalpha() and not letter.isdigit()):
				flash('Username contains special characters.', 'danger')
				return render_template('register.html', username = get_username(session), usertype = get_usertype(session))


		if len(username) >15 or len(username) <6:
			flash('Username does not match length requirements! Username must be between 6 and 15 characters', 'danger')
			return render_template('register.html', username = get_username(session), usertype = get_usertype(session))

		if len(password) <6 or len(password) >50:
			flash('Password must be above 6 characters in length!', 'danger')
			return render_template('register.html', username = get_username(session), usertype = get_usertype(session))

		pass_hash = bcrypt.generate_password_hash(password)
		if not email:
			flash('An Email is required!', 'danger')
		elif not username:
			flash('A Username is required!', 'danger')
		elif not password:
			flash('A Password is required!', 'danger')
		elif not confirm_password:
			flash('Please confirm your password!', 'danger')
		else:
			with sql.connect('shvc.db') as con:
				try:
					cur = con.cursor()
					cur.execute("INSERT INTO User (email, username, password, usertype) VALUES(?,?,?,?)", (email, username, pass_hash, usertype))
					con.commit()
					flash('Account successfuly created!', 'success')
					return render_template('login.html', username = get_username(session), usertype = get_usertype(session))
				except Exception as error:
					flash('Error creating account! Email may already exist.', 'danger')
	return render_template('register.html', username = get_username(session), usertype = get_usertype(session))
	con.close()

@app.route("/login", methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']

		if not email:
			flash('An Email is required!', 'danger')
		elif not password:
			flash('A Password is required!', 'danger')
		else:
			with sql.connect('shvc.db') as con:
				cur = con.cursor()
				dbpass = cur.execute("SELECT password FROM User WHERE email = '?' ".replace("?", email))
			dbpass = dbpass.fetchall()[0][0]
			checkpass = bcrypt.check_password_hash(dbpass, password)
			if checkpass == False:
				flash('Password or Email is incorrect!', 'danger')
				return render_template('login.html', username = get_username(session), usertype = get_usertype(session))
			else:
				username = cur.execute("SELECT username FROM User WHERE email = '?' ".replace("?", email)).fetchall()[0][0]
				usertype = cur.execute("SELECT usertype FROM User WHERE email = '?' ".replace("?", email)).fetchall()[0][0]
				session['username'] = username
				session['usertype'] = usertype
				flash('You have been logged in!', 'success')
				return render_template('index.html', username=get_username(session), usertype = get_usertype(session))

	return render_template('login.html', username = get_username(session), usertype = get_usertype(session))
	con.close()
  
@app.route("/account", methods=['GET', 'POST'])
def account():
	username = get_username(session)
	with sql.connect('shvc.db') as con:
		cur = con.cursor()
		email = cur.execute("SELECT email FROM User WHERE username = '?' ".replace("?", username)).fetchall()[0][0]
		userid = str(cur.execute("SELECT userid FROM User WHERE username = '?' ".replace("?", username)).fetchall()[0][0])
		orders = cur.execute("SELECT * FROM Orders WHERE userid = '?'".replace("?", userid)).fetchall()

		averageorder = str(cur.execute("SELECT AVG(TotalPrice) FROM Orders WHERE userid = '?'".replace("?", userid)).fetchall())
		averageprice = averageorder.strip("[(,)]")

	return render_template('account.html', orders = orders, averageprice = averageprice, username = get_username(session), usertype = get_usertype(session), email = email)

@app.route("/logout", methods=['GET', 'POST'])
def logout():
	session['username'] = ''
	session['usertype'] = ''
	session['Basket'] = ''

	flash('You have been logged out', 'success')
	return render_template('index.html', username = get_username(session), usertype = get_usertype(session))

if __name__ == '__main__':
	app.run(debug=True)

#admin@shvc.com
#admin123
#https://sqliteonline.com/syntax/create_index
#https://www.buycott.com/search?term=shiraz&type=product
#https://flask-bcrypt.readthedocs.io/en/latest/