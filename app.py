
#*****************************************
#  Maintainer : SHIVAM 
#*****************************************

#Imports

from flask import Flask, render_template, request, redirect, url_for , session ,send_file
import hashlib
from datetime import datetime
import sqlite3
import os
from functools import wraps
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle , Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


app = Flask(__name__)
app.secret_key = os.urandom(24) 


class Medicine:
    def __init__(self, name, price, mrp, quantity, expiry,date ):
        self.name = name
        self.price = price
        self.mrp = mrp
        self.quantity = quantity
        self.expiry = datetime.strptime(expiry, '%Y-%m-%d').date()
        self.date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').date()


class Sale:
    def __init__(self, name, quantity_sold, quantity_left, total_amount, datestamp):
        self.name = name
        self.quantity_sold = quantity_sold
        self.quantity_left = quantity_left
        self.total_amount = total_amount
        self.datestamp = datestamp
class Customer:
    def __init__(self, customer_name, phone_no, issued_by):
        self.customer_name = customer_name
        self.phone_no = phone_no
        self.issued_by = issued_by

        
class PharmacyManagementSystem:
    def __init__(self):
        self.initialize_database()

    def initialize_database(self):
        connection = sqlite3.connect('pharmacy.db')
        cursor = connection.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                mrp REAL NOT NULL,
                quantity INTEGER NOT NULL,
                expiry TEXT NOT NULL,
                date TEXT NOT NULL      
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               medicine_name TEXT NOT NULL,
               quantity_sold INTEGER NOT NULL,
               quantity_left INTEGER NOT NULL,
               total_amount REAL NOT NULL,
               datestamp TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               customer_name TEXT NOT NULL,
               phone_no INTEGER NOT NULL,
               issued_by TEXT NOT NULL
            )
        ''')
       

        connection.commit()
        connection.close()


    def register_user(self, username, password):
        connection = sqlite3.connect('pharmacy.db')
        cursor = connection.cursor()

        # Check if the username is already taken
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            connection.close()
            return "Username already taken. Please choose a different username."

        # Hash the password before storing in the database
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        cursor.execute('''
            INSERT INTO users (username, password)
            VALUES (?, ?)
        ''', (username, hashed_password))

        connection.commit()
        connection.close()

        return "Registration successful. You can now login."

    def verify_user(self, username, password):
        connection = sqlite3.connect('pharmacy.db')
        cursor = connection.cursor()

        # Hash the password for comparison with the hashed password in the database
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        cursor.execute('''
            SELECT * FROM users WHERE username = ? AND password = ?
        ''', (username, hashed_password))

        user_data = cursor.fetchone()
        connection.close()

        if user_data:
            return True
        else:
            return False


    def add_medicine(self, name, price, mrp, quantity, expiry):
        connection = sqlite3.connect('pharmacy.db')
        cursor = connection.cursor()
        date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO medicines (name, price, mrp, quantity, expiry , date)
            VALUES (?, ?, ?, ?, ? , ?)
        ''', (name, price, mrp, quantity, expiry , date))

        connection.commit()
        connection.close()

    def find_medicine(self, name):
        connection = sqlite3.connect('pharmacy.db')
        cursor = connection.cursor()

        cursor.execute('''
            SELECT * FROM medicines WHERE name = ?
        ''', (name,))

        medicine_data = cursor.fetchone()
        connection.close()

        if medicine_data:
            return Medicine(*medicine_data[1:])
        else:
            return None

    def update_medicine_quantity(self, name, quantity):
        connection = sqlite3.connect('pharmacy.db')
        cursor = connection.cursor()

        cursor.execute('''
            UPDATE medicines SET quantity = quantity + ? WHERE name = ?
        ''', (quantity, name))

        connection.commit()
        connection.close()

   
    
    def sell_medicine(self, name, quantity):
        connection = sqlite3.connect('pharmacy.db')
        cursor = connection.cursor()

        cursor.execute('SELECT quantity FROM medicines WHERE name = ?', (name,))
        current_quantity_row = cursor.fetchone()

        if current_quantity_row is None:
            connection.close()
            print(f"Medicine '{name}' does not exist in the inventory.")
            return

        current_quantity = int(current_quantity_row[0])

        cursor.execute('SELECT * FROM medicines WHERE name = ?', (name,))
        medicine_data = cursor.fetchone()

        if medicine_data is None:
            connection.close()
            print(f"Medicine '{name}' does not exist in the inventory.")
            return

        if current_quantity and current_quantity >= int(quantity):
            total_amount = medicine_data[3] * int(quantity)

            quantity_left = current_quantity - int(quantity)

            datestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute('UPDATE medicines SET quantity = ? WHERE name = ?', (quantity_left, name))

            cursor.execute('INSERT INTO sales (medicine_name, quantity_sold, quantity_left, total_amount, datestamp) VALUES (?, ?, ?, ?, ?)',
                           (name, quantity, quantity_left, total_amount, datestamp))

            connection.commit()
            connection.close()

            print(f"Sold {quantity} units of '{name}' for ${total_amount:.2f} :")
        else:
            connection.close()
            print(f"Not enough stock for '{name}'. Available: {current_quantity[0] if current_quantity else 0}")
   
    def customer_info(self,customer_name, phone_no ,issued_by):
        connection = sqlite3.connect('pharmacy.db')
        cursor = connection.cursor()
        
        if not customer_name:
            customer_name = "Default Customer"
        if not phone_no :
            customer_name = 0000000000
        if not issued_by:
             issued_by = "pharmaCO"
        
        cursor.execute('INSERT INTO customer (customer_name, phone_no ,issued_by) VALUES (?, ?, ?)',
                           (customer_name, phone_no ,issued_by))
        connection.commit()
        connection.close()

    def get_customer(self):
        connection = sqlite3.connect('pharmacy.db')
        cursor = connection.cursor()

        cursor.execute('''
        SELECT * FROM customer
        ''')

        customer_data = cursor.fetchall()
        connection.close()

        customers = []  # List to store customer objects

        if not customer_data:
            return customers
        else:
            for custo_info in customer_data:
                customer = Customer(*custo_info[1:])  # Create a Customer object from the data
                customers.append(customer)

            return customers


    def get_customer_recent(self):
        connection = sqlite3.connect('pharmacy.db')
        cursor = connection.cursor()

        cursor.execute('''
            SELECT * FROM customer
            ORDER BY id DESC LIMIT 1
        ''')

        customer_data = cursor.fetchone()
        connection.close()

        if not customer_data:
            return None
        else:
            customer = Customer(*customer_data[1:])
            return customer


    def display_inventory(self):
        connection = sqlite3.connect('pharmacy.db')
        cursor = connection.cursor()

        cursor.execute('''
        SELECT * FROM medicines
        ''')

        medicines_data = cursor.fetchall()
        connection.close()

        if not medicines_data:
            return []
        else:
            medicines = []
            for medicine_data in medicines_data:
                medicine = Medicine(*medicine_data[1:])
                medicines.append(medicine)
            return medicines

            
    def generate_pdf_report(self, start_date, end_date):
        filename = "inventory_report.pdf"
        doc = SimpleDocTemplate(filename, pagesize=letter)
        elements = []

        # Add title, generated by, and date
        styles = getSampleStyleSheet()
        title = Paragraph("PharmaCO : Inventory Report", styles['Title'])
        generated_by = Paragraph(f"Generated by : {session.get('username', 'Anonymous')}", styles['Normal'])   
        current_date = Paragraph(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
        signed_by = Paragraph(f"Signed by : {session.get('username', 'Anonymous')}", styles['Normal']) 
        elements.extend([title, generated_by, current_date])

        # Generate the table data for the report
        data = [['Medicine Name', 'Price', 'Quantity', 'MRP', 'Expiry', 'Date']]

        all_medicines = self.display_inventory()

        # Filter medicines based on start_date and end_date
        filtered_medicines = [medicine for medicine in all_medicines if start_date <= medicine.date <= end_date]
        
        for medicine in filtered_medicines:
            data.append([medicine.name, medicine.price, medicine.quantity, medicine.mrp, medicine.expiry, medicine.date])

        # Create the table and add it to the elements list
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        
        elements.extend([signed_by])
        # Build the PDF file
        doc.build(elements)

        return filename


        
    def remove_medicine(self, name):
        connection = sqlite3.connect('pharmacy.db')
        cursor = connection.cursor()

        cursor.execute('DELETE FROM medicines WHERE name = ?', (name,))

        connection.commit()
        connection.close()

        print(f"Medicine '{name}' removed from the inventory.")
    
    def remove_sales_history(self, medicine_name):
        connection = sqlite3.connect('pharmacy.db')
        cursor = connection.cursor()

        cursor.execute('DELETE FROM sales WHERE medicine_name = ?', (medicine_name,))

        connection.commit()
        connection.close()

        print(f"Transaction for '{medicine_name}' removed from sales history.")
  

    def recently_updated(self):
        connection = sqlite3.connect('pharmacy.db')
        cursor = connection.cursor()

        cursor.execute('''
        SELECT * FROM medicines
        ORDER BY id DESC LIMIT 12
        ''')

        medicines_data = cursor.fetchall()
        connection.close()

        if not medicines_data:
            return []
        else:
            medicines = []
            for medicine_data in medicines_data:
                medicine = Medicine(*medicine_data[1:])
                medicines.append(medicine)
            return medicines
    

    def get_sales(self):
        connection = sqlite3.connect('pharmacy.db')
        cursor = connection.cursor()

        cursor.execute('''
        SELECT * FROM sales
        ''')

        sales_data = cursor.fetchall()
        connection.close()

        if not sales_data:
            return []
        else:
            sales = []
            for sale_data in sales_data:
                sale = Sale(*sale_data[1:])
                sales.append(sale)
            return sales

  

############################################################################################
   
pharmacy = PharmacyManagementSystem()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function



##############################################################################################

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if pharmacy.verify_user(username, password):
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')


# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        result = pharmacy.register_user(username, password)
        return render_template('register.html', result=result)

    return render_template('register.html')


# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))



#########################################################################

#HOME

@app.route('/')  
@login_required
def home():
    all_medicines = pharmacy.display_inventory()
    recently= pharmacy.recently_updated() 
    current_date = datetime.now().date()  # Convert current_date to datetime.date object

    expired_medicines = [medicine for medicine in all_medicines if medicine.expiry < current_date]
    out_of_stock_medicines = [medicine for medicine in all_medicines if medicine.quantity == 0]

    return render_template('index.html', medicines=all_medicines, expired_medicines=expired_medicines , recently=recently , outstocks=out_of_stock_medicines)


#add_medicine

@app.route('/add_medicine', methods=['GET', 'POST'])
@login_required
def add_medicine():
    message = None
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        mrp = float(request.form['mrp'])
        expiry = request.form['expiry']
        
        try:
            expiry = datetime.strptime(expiry, '%Y-%m-%d').date()

        except ValueError:
            return "Invalid Expiry Date Format. Please use yyyy-mm-dd."

        pharmacy.add_medicine(name, price, mrp, quantity, expiry)
        message = "Medicine added successfully!"
        
        # return redirect(url_for('add_medicine'))

    return render_template('add_medicine.html', message=message , medicines=pharmacy.recently_updated())


#find_medicine

@app.route('/find_medicine', methods=['GET', 'POST'])
@login_required
def find_medicine():
    if request.method == 'POST':
        name = request.form['name']
        medicine = pharmacy.find_medicine(name)
        return render_template('find_medicine.html', medicine=medicine)

    return render_template('find_medicine.html', medicine=None)

#update_medicine_quantity

@app.route('/update_medicine_quantity', methods=['GET', 'POST'])
@login_required
def update_medicine_quantity_route():
    recent_update=None
    message=None
    if request.method == 'POST':
        name = request.form['name']
        quantity = int(request.form['quantity'])
        pharmacy.update_medicine_quantity(name, quantity)
        recent_update=pharmacy.recently_updated()
        message="Updated Successfully!"
        # return redirect(url_for('display_inventory'))
     

    return render_template('update_medicine_quantity.html' ,recently=recent_update,message=message)


@app.route('/remove_medicine', methods=['GET', 'POST'])
@login_required
def remove_medicine():
    message = None
    all_medicines = pharmacy.display_inventory()
    
    if request.method == 'POST':
        selected_medicines = request.form.getlist('medicine_checkbox')

        for medicine_name in selected_medicines:
            pharmacy.remove_medicine(medicine_name)
        message="Medicine's Removed Successfully! "
        
        
    return render_template('remove_medicine.html', medicines=all_medicines ,message=message)


@app.route('/remove_sales_history', methods=['GET', 'POST'])
@login_required
def remove_sales_history():
    message1 = None
    history = None  # Add this line to initialize the history variable
    if request.method == 'POST':
        medicine_name = request.form['medicine_name']
        pharmacy.remove_sales_history(medicine_name)
        message1 = f"Sales history for '{medicine_name}' removed successfully!"
    
    # Fetch updated sales history after removal
    sales_history = pharmacy.get_sales()

    return render_template('remove_sales.html', message1=message1, medicines=sales_history)


@app.route('/sell_medicine', methods=['GET', 'POST'])
@login_required
def sell_medicine_route():
    message = None
    if request.method == 'POST':
        medicine_names = request.form.getlist('medicine_name')
        quantities = request.form.getlist('quantity')
        customer_name = request.form['customer_name']  # Get customer name from the form
        phone_no = request.form['phone_no']  # Get phone number from the form
        issued_by = request.form['issued_by'] 
        pharmacy.customer_info(customer_name, phone_no, issued_by)
        message="Medicine's sold Successfully! , Now Generate Invoice "
        invoice = []  # List to store invoice data

        # Process the data as needed
        for name, quantity in zip(medicine_names, quantities):
            if name and quantity:
                medicine = pharmacy.find_medicine(name)
                if medicine:
                    total_amount = medicine.mrp * int(quantity)
                    invoice.append({
                        'name': medicine.name,
                        'quantity_sold': int(quantity),
                        'price': medicine.mrp,
                        'total_amount': total_amount
                    })
                    # Perform the sell operation using pharmacy.sell_medicine()
                    pharmacy.sell_medicine(name, int(quantity))

        total_amount = sum(item['total_amount'] for item in invoice)

        # Store the invoice data in a session variable
        session['invoice'] = {
            'invoice_items': invoice,
            'total_amount': total_amount
        }
        return render_template('sell_medicine.html', medicines=pharmacy.display_inventory(), invoice=invoice, total_amount=total_amount ,message=message )

    return render_template('sell_medicine.html', medicines=pharmacy.display_inventory())



@app.route('/invoice', methods=['GET', 'POST'])
@login_required
def invoice():
    customers = pharmacy.get_customer_recent()  # Get the list of customers
    customers = [customers] if customers else []

    invoice_data = session.get('invoice')  # Retrieve the invoice data from the session
    date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return render_template('invoice.html', customers=customers, invoice_data=invoice_data , date=date)






@app.route('/display_inventory')
@login_required
def display_inventory():
    return render_template('display_inventory.html', medicines=pharmacy.display_inventory())

@app.route('/generate_report', methods=['GET', 'POST'])
@login_required
def generate_report():
    if request.method == 'POST':
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        report_filename = pharmacy.generate_pdf_report(start_date, end_date)
        return send_file(report_filename, as_attachment=True)

    return render_template('generate_report.html')



if __name__ == '__main__':
    app.run(debug=True)






