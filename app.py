from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from uuid import uuid4

# --- Configuration and Data ---
app = Flask(__name__)
# IMPORTANT: Always change the secret key in a production environment
app.secret_key = 'super-creative-shopping-key-123' 

# SHOP NAME CONFIGURATION
SHOP_NAME = "Giri Shopping Mart" 

# Global financial parameters
TAX_RATE = 0.05       # 5% Sales Tax
DISCOUNT_THRESHOLD = 50000 
DISCOUNT_RATE = 0.10  # 10% off for total >= 50,000

# Enhanced Item List: Nested dictionary for categorization and stock tracking
available_items = {
    "Electronics": {
        "Laptop": {"price": 45000, "stock": 10},
        "Smartphone": {"price": 25000, "stock": 25},
        "Tablet": {"price": 20000, "stock": 15},
        "Smartwatch": {"price": 5500, "stock": 30},
        "LED TV": {"price": 38000, "stock": 5},
    },
    "Accessories": {
        "Mouse": {"price": 500, "stock": 50},
        "Keyboard": {"price": 800, "stock": 40},
        "Headphones": {"price": 1500, "stock": 35},
        "Power Bank": {"price": 1200, "stock": 60},
        "Bluetooth Earbuds": {"price": 1800, "stock": 45},
    },
    "Home Appliances": {
        "Washing Machine": {"price": 32000, "stock": 8},
        "Microwave Oven": {"price": 11000, "stock": 12},
        "Ceiling Fan": {"price": 2600, "stock": 50},
    },
    "Stationery": {
        "Notebook": {"price": 80, "stock": 200},
        "Pen Pack": {"price": 50, "stock": 300},
        "Calculator": {"price": 300, "stock": 75},
    },
}

# Global cart list 
cart = []

# --- Utility Functions ---
def find_item_details(item_name):
    """Finds the price, stock, and category of an item."""
    for category, items in available_items.items():
        if item_name in items:
            return items[item_name]['price'], items[item_name]['stock'], category
    return None, None, None

# --- Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    # Calculate subtotal for display
    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    
    if request.method == 'POST':
        # Customer details submission logic
        session['customer_id'] = request.form['customer_id']
        session['customer_name'] = request.form['customer_name']
        session['customer_phone'] = request.form['customer_phone']
        flash("Customer details updated successfully!", 'success')
        
    return render_template(
        'index.html', 
        cart=cart, 
        subtotal=subtotal, 
        items=available_items, 
        session=session
    )

@app.route('/add_item', methods=['POST'])
def add_item():
    try:
        item_name = request.form['item']
        quantity = int(request.form['quantity'])
    except:
        flash("Invalid item selection or quantity.", 'error')
        return redirect(url_for('index'))

    price, stock, category = find_item_details(item_name)

    if not price:
        flash(f"Item '{item_name}' not found.", 'error')
        return redirect(url_for('index'))
    
    if quantity <= 0:
        flash("Quantity must be a positive number.", 'error')
        return redirect(url_for('index'))
        
    current_cart_quantity = sum(item['quantity'] for item in cart if item['name'] == item_name)
    
    # Stock Check
    if (current_cart_quantity + quantity) > stock:
        flash(f"Sorry, only {stock - current_cart_quantity} of {item_name} remaining in stock.", 'error')
        return redirect(url_for('index'))

    # Add or Update Item in Cart
    for item in cart:
        if item['name'] == item_name:
            item['quantity'] += quantity
            flash(f"Updated {item_name} quantity.", 'info')
            return redirect(url_for('index'))

    item_id = len(cart) + 1
    cart.append({'id': item_id, 'name': item_name, 'price': price, 'quantity': quantity, 'category': category})
    flash(f"Added {quantity} x {item_name} to cart.", 'success')
    return redirect(url_for('index'))

@app.route('/update/<int:item_id>', methods=['POST'])
def update_item(item_id):
    try:
        new_quantity = int(request.form['quantity'])
    except:
        flash("Invalid quantity entered.", 'error')
        return redirect(url_for('index'))
        
    if new_quantity <= 0:
        return delete_item(item_id) # Treat update to 0 as deletion
        
    for item in cart:
        if item['id'] == item_id:
            price, stock, category = find_item_details(item['name'])
            
            # Stock check for update
            if new_quantity > stock:
                flash(f"Cannot set quantity for {item['name']} to {new_quantity}. Only {stock} available.", 'error')
                return redirect(url_for('index'))
                
            item['quantity'] = new_quantity
            flash(f"Updated {item['name']} quantity to {new_quantity}.", 'info')
            break
    return redirect(url_for('index'))

@app.route('/delete/<int:item_id>')
def delete_item(item_id):
    global cart
    item_name = ""
    original_length = len(cart)
    for item in cart:
        if item['id'] == item_id:
            item_name = item['name']
            break
            
    cart = [item for item in cart if item['id'] != item_id]
    
    if len(cart) < original_length:
        flash(f"Removed {item_name} from cart.", 'warning')
    return redirect(url_for('index'))

@app.route('/clear_cart')
def clear_cart():
    """Route to empty the shopping cart and clear customer session data."""
    global cart
    cart = []
    session.pop('customer_id', None)
    session.pop('customer_name', None)
    session.pop('customer_phone', None)
    flash("Cart and customer details cleared successfully!", 'warning')
    return redirect(url_for('index'))


@app.route('/bill')
def print_bill(): # Correct endpoint name: 'print_bill'
    if not session.get('customer_name') or not cart:
        flash("Please enter customer details and add items to the cart before generating a bill.", 'error')
        return redirect(url_for('index'))

    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    
    # Calculate Discount
    discount = 0
    if subtotal >= DISCOUNT_THRESHOLD:
        discount = round(subtotal * DISCOUNT_RATE, 2)
        
    taxable_amount = subtotal - discount
    
    # Calculate Tax
    tax = round(taxable_amount * TAX_RATE, 2)
    
    final_total = round(taxable_amount + tax, 2)
    
    date_time = datetime.now().strftime("%d-%m-%Y %I:%M %p")
    invoice_id = f"INV-{uuid4().hex[:8].upper()}" 

    return render_template(
        'bill.html',
        cart=cart,
        subtotal=subtotal,
        discount=discount,
        tax=tax,
        final_total=final_total,
        customer_id=session.get('customer_id', 'N/A'),
        customer_name=session.get('customer_name', 'N/A'),
        customer_phone=session.get('customer_phone', 'N/A'),
        date_time=date_time,
        invoice_id=invoice_id,
        tax_rate=int(TAX_RATE * 100),
        discount_rate=int(DISCOUNT_RATE * 100),
        shop_name=SHOP_NAME # Pass the shop name
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')