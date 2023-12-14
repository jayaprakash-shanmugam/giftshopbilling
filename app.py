from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson import ObjectId
import datetime

app = Flask(__name__)

# Connect to MongoDB Atlas Cluster
# Replace <YOUR_CONNECTION_STRING> with your actual connection string
client = MongoClient('mongodb+srv://jp:jp@cluster0.4ipjx6l.mongodb.net/?retryWrites=true&w=majority')
db = client['gift_shop']
orders_collection = db['orders']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_order', methods=['GET', 'POST'])
def create_order():
    if request.method == 'POST':
        # Process form data and insert into MongoDB
        customer_name = request.form['customer_name']
        customer_contact = request.form['customer_contact']
        gift_name = request.form['gift_name']
        gift_price = float(request.form['gift_price'])
        quantity = int(request.form['quantity'])
        total_price = gift_price * quantity
        order_date = datetime.datetime.utcnow()
        payment_method = request.form['payment_method']
        transaction_id = request.form['transaction_id']
        payment_status = request.form['payment_status']

        order_data = {
            'customer_name': customer_name,
            'customer_contact': customer_contact,
            'gifts': [{'name': gift_name, 'price': gift_price, 'quantity': quantity, 'subtotal': total_price}],
            'order_date': order_date,
            'total_price': total_price,
            'payment_method': payment_method,
            'transaction_id': transaction_id,
            'payment_status': payment_status,
        }

        orders_collection.insert_one(order_data)
        return redirect(url_for('view_orders'))

    return render_template('create_order.html')

@app.route('/view_orders', methods=['GET', 'POST'])
def view_orders():
    orders = orders_collection.find()

    if request.method == 'POST':
        order_id = request.form.get('order_id')

        if 'update_order' in request.form:
            new_payment_status = request.form.get('new_payment_status')
            orders_collection.update_one({'_id': ObjectId(order_id)}, {'$set': {'payment_status': new_payment_status}})
            return redirect(url_for('view_orders'))

        elif 'delete_order' in request.form:
            orders_collection.delete_one({'_id': ObjectId(order_id)})
            return redirect(url_for('view_orders'))

    return render_template('view_orders.html', orders=orders)

if __name__ == '__main__':
    app.run(debug=True)
