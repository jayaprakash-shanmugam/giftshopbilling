import streamlit as st
from pymongo import MongoClient
from bson import ObjectId  # For handling MongoDB ObjectIDs
import datetime

# Connect to MongoDB Atlas Cluster
# Replace <YOUR_CONNECTION_STRING> with your actual connection string
client = MongoClient('mongodb+srv://jp:jp@cluster0.4ipjx6l.mongodb.net/?retryWrites=true&w=majority')
db = client['gift_shop']
orders_collection = db['orders']

# Streamlit App
# st.title('Admin Dashboard')

# CRUD Operations
st.sidebar.title("Admin dashboard")
operation = st.sidebar.selectbox("",["Create Orders", "View Orders"])

if operation == "Create Orders":
    # Admin Dashboard Operation
    st.subheader("Create Order")
    col1, col2 = st.columns(2)

    with col1:
        customer_name = st.text_input('Customer Name:')
        customer_contact = st.text_input('Customer Phone Number:')
        gift_name = st.text_input('Gift Name:')
        gift_price = st.number_input('Price:', step=0.01)
        quantity = st.number_input('Quantity:', min_value=1, step=1)

    with col2:
        total_price = gift_price * quantity if gift_price > 0 and quantity > 0 else 0
        order_date = datetime.datetime.utcnow()
        payment_method = st.selectbox('Payment Method:', ['Card', 'Cash', 'Other'])
        transaction_id = st.text_input('Transaction ID:')
        payment_status = st.radio('Payment Status:', ['Pending', 'Completed'])

    if st.button('Submit'):
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
        st.success('Inserted successfully!')

elif operation == "View Orders":
    # View Orders Operation
    st.subheader("View Orders")
    orders = orders_collection.find()
    for order in orders:
        st.write(f"**Order ID:** {order['_id']}")
        for key, value in order.items():
            st.write(f"**{key.capitalize()}:** {value}")

        # Update Order Button
        if st.button(f"Update Order {order['_id']}"):
            new_payment_status = st.radio(f'New Payment Status for Order {order["_id"]}:', ['Pending', 'Completed'])
            orders_collection.update_one({'_id': order['_id']}, {'$set': {'payment_status': new_payment_status}})
            st.success(f'Order {order["_id"]} updated successfully!')

        # Delete Order Button
        if st.button(f"Delete Order {order['_id']}"):
            orders_collection.delete_one({'_id': order['_id']})
            st.success(f'Order {order["_id"]} deleted successfully!')

        st.write('---')
