import streamlit as st
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
import io

st.set_page_config(
    page_title="Shree Vari Mart",
    page_icon="🛍️",
    layout="wide"
)

def connect_to_mongodb():
    try:
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://host.docker.internal:27017/')
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Test the connection
        client.server_info()
        db = client["invoice_db"]
        return db.invoices
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {str(e)}")
        st.error("Please ensure MongoDB is running and accessible.")
        return None

# Initialize MongoDB collection
collection = connect_to_mongodb()

def get_next_bill_number():
    last_invoice = collection.find_one(sort=[("bill_no", -1)])
    if last_invoice and 'bill_no' in last_invoice:
        return int(last_invoice['bill_no']) + 1
    return 1000

def preview_invoice(invoice_data):
    st.subheader("Invoice Preview")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**Bill No.:**", invoice_data["bill_no"])
        st.write("**Customer Name:**", invoice_data["customer_name"])
        st.write("**Phone Number:**", invoice_data["phone_number"])
    
    with col2:
        st.write("**Order Date:**", invoice_data["order_date"])
        st.write("**Payment Method:**", invoice_data["payment_method"])
        st.write("**Payment Status:**", invoice_data["payment_status"])
    
    st.write("**Products:**")
    df = pd.DataFrame(invoice_data["products"])
    st.dataframe(df)
    st.write(f"**Total Price:** {invoice_data['total_price']}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Edit"):
            st.session_state.edit_mode = True
            st.session_state.editing_invoice = invoice_data
            st.experimental_rerun()
    with col2:
        if st.button("Confirm & Save"):
            collection.insert_one(invoice_data)
            st.success("Invoice saved successfully!")
            st.session_state.current_bill_no = get_next_bill_number()
            st.session_state.product_details = []
            st.session_state.show_preview = False
            st.session_state.active_tab = "Search Invoices"
            st.experimental_rerun()
    with col3:
        if st.button("Cancel"):
            st.session_state.show_preview = False
            st.experimental_rerun()

def edit_invoice(invoice_data):
    st.subheader("Edit Invoice")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        customer_name = st.text_input("Customer Name", value=invoice_data["customer_name"])
        phone_number = st.text_input("Phone Number", value=invoice_data["phone_number"])
    
    with col2:
        order_date = st.date_input("Order Date", datetime.strptime(invoice_data["order_date"], "%Y-%m-%d"))
        payment_method = st.selectbox("Payment Method", ["Cash", "Card", "UPI"], 
                                    index=["Cash", "Card", "UPI"].index(invoice_data["payment_method"]))
        payment_status = st.selectbox("Payment Status", ["Paid", "Pending"],
                                    index=["Paid", "Pending"].index(invoice_data["payment_status"]))
    
    st.write("Products")
    products = invoice_data["products"]
    num_products = st.number_input("Number of Products", min_value=1, value=len(products))
    
    updated_products = []
    total_price = 0
    
    for i in range(num_products):
        col1, col2, col3 = st.columns(3)
        product = products[i] if i < len(products) else {"gift_name": "", "gift_quantity": 1, "price": 0.0}
        
        with col1:
            gift_name = st.text_input(f"Gift Name #{i+1}", value=product["gift_name"])
        with col2:
            gift_qty = st.number_input(f"Quantity #{i+1}", min_value=1, value=product["gift_quantity"])
        with col3:
            price = st.number_input(f"Price per unit #{i+1}", min_value=0.0, value=product["price"], step=1.0)
        
        updated_product = {
            "gift_name": gift_name,
            "gift_quantity": gift_qty,
            "price": price,
            "total": gift_qty * price
        }
        updated_products.append(updated_product)
        total_price += updated_product["total"]
    
    if updated_products:
        st.write("Updated Invoice Summary:")
        df = pd.DataFrame(updated_products)
        st.dataframe(df)
        st.write(f"Total Price: {total_price}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Changes"):
                updated_invoice = {
                    "bill_no": invoice_data["bill_no"],
                    "customer_name": customer_name,
                    "phone_number": phone_number,
                    "order_date": order_date.strftime("%Y-%m-%d"),
                    "payment_method": payment_method,
                    "payment_status": payment_status,
                    "products": updated_products,
                    "total_price": total_price
                }
                
                collection.update_one({"bill_no": invoice_data["bill_no"]}, {"$set": updated_invoice})
                st.success("Invoice updated successfully!")
                st.session_state.edit_mode = False
                st.session_state.active_tab = "Search Invoices"
                st.experimental_rerun()
        
        with col2:
            if st.button("Cancel"):
                st.session_state.edit_mode = False
                st.experimental_rerun()

def create_invoice():
    if 'current_bill_no' not in st.session_state:
        st.session_state.current_bill_no = get_next_bill_number()
    
    if 'show_preview' not in st.session_state:
        st.session_state.show_preview = False
    
    if st.session_state.show_preview:
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.text_input("Bill No.", str(st.session_state.current_bill_no), disabled=True, key="bill_no")
        customer_name = st.text_input("Customer Name")
        phone_number = st.text_input("Phone Number")
    
    with col2:
        order_date = st.date_input("Order Date")
        payment_method = st.selectbox("Payment Method", ["Cash", "Card", "UPI"])
        payment_status = st.selectbox("Payment Status", ["Paid", "Pending"])
    
    st.write("Products")
    
    if 'products' not in st.session_state:
        st.session_state.products = []
        
    if 'product_details' not in st.session_state:
        st.session_state.product_details = []
    
    num_products = st.number_input("Number of Products", min_value=1, value=1)
    
    while len(st.session_state.product_details) < num_products:
        st.session_state.product_details.append({
            'gift_name': '',
            'gift_quantity': 1,
            'price': 0.0
        })
    
    if len(st.session_state.product_details) > num_products:
        st.session_state.product_details = st.session_state.product_details[:num_products]
    
    products = []
    total_price = 0
    
    for i in range(num_products):
        col1, col2, col3 = st.columns(3)
        with col1:
            gift_name = st.text_input(
                f"Gift Name #{i+1}",
                value=st.session_state.product_details[i]['gift_name'],
                key=f"gift_name_{i}"
            )
            st.session_state.product_details[i]['gift_name'] = gift_name
            
        with col2:
            gift_qty = st.number_input(
                f"Quantity #{i+1}",
                min_value=1,
                value=st.session_state.product_details[i]['gift_quantity'],
                key=f"gift_qty_{i}"
            )
            st.session_state.product_details[i]['gift_quantity'] = gift_qty
            
        with col3:
            price = st.number_input(
                f"Price per unit #{i+1}",
                min_value=0.0,
                value=st.session_state.product_details[i]['price'],
                step=1.0,
                key=f"price_{i}"
            )
            st.session_state.product_details[i]['price'] = price
        
        product = {
            "gift_name": gift_name,
            "gift_quantity": gift_qty,
            "price": price,
            "total": gift_qty * price
        }
        products.append(product)
        total_price += product["total"]
    
    if products:
        st.write("Invoice Summary:")
        df = pd.DataFrame(products)
        st.dataframe(df)
        st.write(f"Total Price: {total_price}")
        
        if st.button("Preview Invoice"):
            invoice_data = {
                "bill_no": str(st.session_state.current_bill_no),
                "customer_name": customer_name,
                "phone_number": phone_number,
                "order_date": order_date.strftime("%Y-%m-%d"),
                "payment_method": payment_method,
                "payment_status": payment_status,
                "products": products,
                "total_price": total_price
            }
            st.session_state.preview_invoice = invoice_data
            st.session_state.show_preview = True
            st.experimental_rerun()

def search_invoices():
    # Add date range filters
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", key="start_date")
    with col2:
        end_date = st.date_input("End Date", key="end_date")
    
    # Search filters
    search_option = st.selectbox("Search By", ["All", "Bill No", "Customer Name", "Phone Number"])
    
    # Only show search term input if not "All"
    search_term = ""
    if search_option != "All":
        search_term = st.text_input("Enter Search Term")
    
    # Build the query
    query = {}
    
    # Add date range to query
    if start_date and end_date:
        query["order_date"] = {
            "$gte": start_date.strftime("%Y-%m-%d"),
            "$lte": end_date.strftime("%Y-%m-%d")
        }
    
    # Add search term to query if provided
    if search_term:
        if search_option == "Bill No":
            query["bill_no"] = search_term
        elif search_option == "Customer Name":
            query["customer_name"] = {"$regex": search_term, "$options": "i"}
        elif search_option == "Phone Number":
            query["phone_number"] = {"$regex": search_term, "$options": "i"}
    
    # Fetch invoices based on query
    invoices = list(collection.find(query).sort("order_date", -1))  # Sort by date, newest first
    
    if invoices:
        # Process invoices and create DataFrame only with valid data
        processed_invoices = []
        for invoice in invoices:
            # Only process invoice if it has all required fields with non-empty values
            if (invoice.get('bill_no') and 
                invoice.get('customer_name') and 
                invoice.get('phone_number') and 
                invoice.get('order_date') and 
                invoice.get('products')):  # Check if products exist
                
                products_str = ', '.join(
                    [f"{p.get('gift_name', '')}({p.get('gift_quantity', '')})" 
                     for p in invoice.get('products', []) 
                     if p.get('gift_name') and p.get('gift_quantity')]  # Only include products with valid data
                )
                
                if products_str:  # Only include invoice if it has valid products
                    invoice_data = {
                        'bill_no': invoice['bill_no'],
                        'customer_name': invoice['customer_name'],
                        'phone_number': invoice['phone_number'],
                        'order_date': invoice['order_date'],
                        'payment_method': invoice.get('payment_method', ''),
                        'payment_status': invoice.get('payment_status', ''),
                        'total_price': invoice.get('total_price', 0),
                        'products': products_str
                    }
                    processed_invoices.append(invoice_data)
        
        if processed_invoices:
            df = pd.DataFrame(processed_invoices)
            
            # Ensure all required columns exist and have valid data
            required_columns = ['bill_no', 'customer_name', 'phone_number', 'order_date', 
                              'payment_method', 'payment_status', 'total_price', 'products']
            
            # Initialize any missing columns with empty strings
            for col in required_columns:
                if col not in df.columns:
                    df[col] = ''
            
            # Reorder columns
            df = df[required_columns]
            
            # Remove any remaining rows with empty essential fields
            df = df[
                df['bill_no'].notna() & 
                df['customer_name'].notna() & 
                df['phone_number'].notna() & 
                df['order_date'].notna() & 
                (df['products'] != '')
            ]
            
            if not df.empty:
                # Display summary statistics
                total_invoices = len(df)
                total_amount = df['total_price'].sum()
                
                # Show summary in columns
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Invoices", total_invoices)
                with col2:
                    st.metric("Total Amount", f"₹{total_amount:,.2f}")
                with col3:
                    st.metric("Date Range", f"{start_date} to {end_date}")
                
                # Display the dataframe
                st.dataframe(df, use_container_width=True, height=400)
                
                # Export buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Export as CSV"):
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f'invoices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                            mime='text/csv'
                        )
                with col2:
                    if st.button("Export as Excel"):
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        st.download_button(
                            label="Download Excel",
                            data=buffer.getvalue(),
                            file_name=f'invoices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        )
                
                # Add summary for filtered results if search is applied
                if search_term or (start_date and end_date):
                    st.info(f"Showing {total_invoices} filtered results with total amount: ₹{total_amount:,.2f}")
            else:
                st.warning("No valid invoice data found.")
        else:
            st.warning("No valid invoice data found.")
    else:
        st.info("No invoices found for the selected criteria.")

def search_invoices():
    # Add date range filters
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", key="start_date")
    with col2:
        end_date = st.date_input("End Date", key="end_date")
    
    # Search filters
    search_option = st.selectbox("Search By", ["All", "Bill No", "Customer Name", "Phone Number"])
    
    # Only show search term input if not "All"
    search_term = ""
    if search_option != "All":
        search_term = st.text_input("Enter Search Term")
    
    # Build the query
    query = {}
    
    # Add date range to query
    if start_date and end_date:
        query["order_date"] = {
            "$gte": start_date.strftime("%Y-%m-%d"),
            "$lte": end_date.strftime("%Y-%m-%d")
        }
    
    # Add search term to query if provided
    if search_term:
        if search_option == "Bill No":
            query["bill_no"] = search_term
        elif search_option == "Customer Name":
            query["customer_name"] = {"$regex": search_term, "$options": "i"}
        elif search_option == "Phone Number":
            query["phone_number"] = {"$regex": search_term, "$options": "i"}
    
    # Fetch invoices based on query
    invoices = list(collection.find(query).sort("order_date", -1))  # Sort by date, newest first
    
    if invoices:
        for invoice in invoices:
            invoice['_id'] = str(invoice['_id'])
            if 'products' in invoice:
                invoice['products'] = ', '.join([f"{p['gift_name']}({p['gift_quantity']})" for p in invoice['products']])
        
        df = pd.DataFrame(invoices)
        columns_order = ['bill_no', 'customer_name', 'phone_number', 'order_date', 
                       'payment_method', 'payment_status', 'total_price', 'products']
        df = df[columns_order]
        
        # Display summary statistics
        total_invoices = len(df)
        total_amount = df['total_price'].sum()
        
        # Show summary in columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Invoices", total_invoices)
        with col2:
            st.metric("Total Amount", f"₹{total_amount:,.2f}")
        with col3:
            st.metric("Date Range", f"{start_date} to {end_date}")
        
        # Display the dataframe
        st.dataframe(df, use_container_width=True, height=400)
        
        # Export buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Export as CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f'invoices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                    mime='text/csv'
                )
        with col2:
            if st.button("Export as Excel"):
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button(
                    label="Download Excel",
                    data=buffer.getvalue(),
                    file_name=f'invoices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
        
        # Add summary for filtered results if search is applied
        if search_term or (start_date and end_date):
            st.info(f"Showing {total_invoices} filtered results with total amount: ₹{total_amount:,.2f}")
    else:
        st.info("No invoices found for the selected criteria.")

def main():
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Create Invoice"
    
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    
    tab1, tab2 = st.tabs(["Create Invoice", "Search Invoices"])
    
    with tab1:
        if st.session_state.edit_mode and 'editing_invoice' in st.session_state:
            edit_invoice(st.session_state.editing_invoice)
        elif 'show_preview' in st.session_state and st.session_state.show_preview:
            preview_invoice(st.session_state.preview_invoice)
        else:
            create_invoice()
    
    with tab2:
        search_invoices()

if __name__ == "__main__":
    main()  