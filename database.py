import sqlite3
from sqlite3 import Error

DB_NAME = "pharmacy.db"

def get_connection():
    try:
        conn = sqlite3.connect(DB_NAME)
        return conn
    except Error as e:
        print("Database connection error:", e)
        return None

def init_db():
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()

    # --- 1. PRODUCT DETAILS ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Product_Details (
        prod_id INTEGER PRIMARY KEY AUTOINCREMENT,
        prod_name TEXT NOT NULL,
        manufacturer TEXT,
        hsn_code TEXT,
        gst REAL DEFAULT 0,
        rack_no TEXT,
        type TEXT,
        tabs_per_strip INTEGER DEFAULT 0,
        uses TEXT
    )
    """)

    # --- 2. PRODUCT STOCK ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Product_Stock (
        stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
        prod_id INTEGER,
        purchase_rate REAL,
        sale_rate REAL,
        rate_per_tab REAL,
        quantity REAL,
        mfg_date TEXT, 
        exp_date TEXT, 
        batch_no TEXT,
        discount REAL DEFAULT 0,
        FOREIGN KEY (prod_id) REFERENCES Product_Details(prod_id)
    )
    """)

    # --- 3. DOCTOR TABLE ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Doctor (
        Doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT,
        Phone TEXT,
        Specialization TEXT,
        Hospital TEXT,
        Email TEXT
    )
    """)

    # --- 4. BILLS & ITEMS (Sales) ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Bill (
        Bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT,
        doctor_name TEXT,
        payment_method TEXT,
        discount REAL,
        total_sum REAL,
        paid_amount REAL DEFAULT 0,
        balance REAL DEFAULT 0,
        bill_date TEXT,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Bill_Item (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        Bill_id INTEGER,
        Prod_id INTEGER,
        quantity INTEGER,
        unit_price REAL,
        total_price REAL,
        FOREIGN KEY (Bill_id) REFERENCES Bill(Bill_id)
    )
    """)

    # --- 5. CUSTOMERS ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Customer (
        Cust_id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT,
        Phone TEXT,
        Email TEXT,
        Address TEXT,
        Notes TEXT,
        balance REAL DEFAULT 0
    )
    """)

    # --- 6. SUPPLIERS ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Supplier (
        Supp_id INTEGER PRIMARY KEY AUTOINCREMENT,
        Sup_name TEXT,
        contact TEXT,
        email TEXT,
        gstin TEXT,
        address TEXT,
        supplier_type TEXT,
        balance REAL DEFAULT 0
    )
    """)

    # --- 7. PURCHASE ORDERS ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Purchase_order (
        po_id INTEGER PRIMARY KEY AUTOINCREMENT,
        supp_id INTEGER,
        order_date TEXT,
        status TEXT,
        FOREIGN KEY (supp_id) REFERENCES Supplier(Supp_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS PO_item (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_id INTEGER,
        Prod_id INTEGER,
        Quantity INTEGER,
        FOREIGN KEY (po_id) REFERENCES Purchase_order(po_id),
        FOREIGN KEY (Prod_id) REFERENCES Product_Details(prod_id)
    )
    """)

    # --- 8. PURCHASE INVOICE ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Purchase_Invoice (
        invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT,
        supp_id INTEGER,
        invoice_date TEXT,
        payment_mode TEXT,
        total_amount REAL,
        paid_amount REAL DEFAULT 0,
        balance REAL DEFAULT 0,
        created_at TEXT,
        FOREIGN KEY (supp_id) REFERENCES Supplier(Supp_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Purchase_Invoice_Item (
        pi_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        Prod_id INTEGER,
        batch_no TEXT,
        expiry_date TEXT,
        quantity REAL,
        free_qty REAL DEFAULT 0,
        purchase_rate_incl REAL, 
        tax_rate REAL,
        tax_amount REAL,
        mrp REAL,
        total_amount REAL,
        FOREIGN KEY (invoice_id) REFERENCES Purchase_Invoice(invoice_id),
        FOREIGN KEY (Prod_id) REFERENCES Product_Details(prod_id)
    )
    """)

    # --- 9. PHARMACY PROFILE ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Pharmacy (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        p_name TEXT,
        location TEXT,
        phone TEXT,
        email TEXT,
        license_no TEXT,
        GSTIN TEXT,
        smtp_email TEXT,
        smtp_password TEXT
    )
    """)

    # --- 10. EXPENSES ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Expenses (
        expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
        expense_type TEXT NOT NULL,
        description TEXT,
        amount REAL NOT NULL,
        expense_date TEXT NOT NULL,
        payment_mode TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # --- 11. PURCHASE RETURN (NEW TABLES) ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Purchase_Return (
        return_id INTEGER PRIMARY KEY AUTOINCREMENT,
        return_number TEXT,
        supp_id INTEGER,
        return_date TEXT,
        total_amount REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (supp_id) REFERENCES Supplier(Supp_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Purchase_Return_Item (
        pr_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        return_id INTEGER,
        Prod_id INTEGER,
        batch_no TEXT,
        expiry_date TEXT,
        return_qty REAL,
        return_amount REAL,
        FOREIGN KEY (return_id) REFERENCES Purchase_Return(return_id),
        FOREIGN KEY (Prod_id) REFERENCES Product_Details(prod_id)
    )
    """)

    conn.commit()
    conn.close()

# --- HELPER FUNCTIONS ---

def get_all_products():
    """
    Returns a joined view of Product Details and Stock for the UI.
    """
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor()
    
    query = """
        SELECT 
            d.prod_id, 
            d.prod_name, 
            d.tabs_per_strip, 
            s.rate_per_tab, 
            s.quantity, 
            d.type,
            s.purchase_rate, 
            s.sale_rate, 
            s.mfg_date, 
            s.exp_date,
            d.hsn_code, 
            d.rack_no, 
            d.gst, 
            s.discount, 
            '' as barcode
        FROM Product_Details d
        LEFT JOIN Product_Stock s ON d.prod_id = s.prod_id
        ORDER BY d.prod_name ASC
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")