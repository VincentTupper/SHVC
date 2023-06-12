def get_db_connection():
	conn = sql.connect('shvc.db')
	conn.row_factory=sql.Row
	return conn

def get_product(product_id):
	conn = get_db_connection()
	foundproduct = conn.execute('SELECT * from products WHERE productid = ?', (product_id,)).fetchone()
	conn.close()
	if foundproduct is None:
		abort(404)
	return foundproduct

def get_username(session):
	try:
		return session['username']
	except:
		return ''

def get_usertype(session):
	try:
		return session['usertype']
	except:
		return ''

def get_basket(session):
	try:
		return session['Basket']
	except:
		return ''


def get_totalprice(session):
	totalprice = 0
	for x in session['Basket']:
		quantity = int(x[1])
		price = float(x[2])
		if quantity >1:
			totalprice = totalprice + (quantity * price)
		elif quantity == 1:
			totalprice = totalprice + price
			totalprice = round(totalprice,4)
	return totalprice
