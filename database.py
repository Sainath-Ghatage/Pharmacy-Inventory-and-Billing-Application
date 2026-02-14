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

    # --- MEDICINE (Added batch_no, mfg_date) ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Medicine (
        Med_id INTEGER PRIMARY KEY AUTOINCREMENT,
        Med_name TEXT,
        Manufacturer TEXT,
        Type TEXT,
        Purchase_Price REAL,
        Sale_Price REAL,
        tabs_per_strip INTEGER,
        rate_per_tab REAL,
        Quantity REAL,
        MFG_Date TEXT,
        EXP_Date TEXT,
        batch_no TEXT DEFAULT '',
        hsn_code TEXT DEFAULT '',
        rack_no TEXT DEFAULT '',
        gst_rate REAL DEFAULT 0,
        discount REAL DEFAULT 0,
        barcode TEXT DEFAULT ''
    )
    """)

    # --- BILLS ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Bill (
        Bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT,
        doctor_name TEXT,
        payment_method TEXT,
        discount REAL,
        total_sum REAL,
        bill_date TEXT,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Bill_Item (
        Item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        Bill_id INTEGER,
        Med_id INTEGER,
        quantity REAL,
        unit_price REAL,
        total_price REAL,
        FOREIGN KEY (Med_id) REFERENCES Medicine(Med_id),
        FOREIGN KEY (Bill_id) REFERENCES Bill(Bill_id)
    )
    """)

    # --- PARTNERS ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Supplier (
        Supp_id INTEGER PRIMARY KEY AUTOINCREMENT,
        Sup_name TEXT,
        contact TEXT,
        email TEXT,
        gstin TEXT,
        address TEXT,
        supplier_type TEXT
    )
    """)

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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Customer (
        Cust_id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT,
        Phone TEXT,
        Email TEXT,
        Address TEXT,
        Notes TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Pharmacy (
        p_name TEXT,
        phone TEXT,
        email TEXT,
        GSTIN TEXT,
        location TEXT
    )
    """)

    # --- PURCHASE INVOICE (Added paid_amount, balance) ---
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
        Med_id INTEGER,
        batch_no TEXT,
        expiry_date TEXT,
        quantity REAL,
        free_qty REAL,
        purchase_rate_incl REAL, 
        tax_rate REAL,
        tax_amount REAL,
        mrp REAL,
        total_amount REAL,
        FOREIGN KEY (invoice_id) REFERENCES Purchase_Invoice(invoice_id),
        FOREIGN KEY (Med_id) REFERENCES Medicine(Med_id)
    )
    """)

    conn.commit()
    conn.close()
    
    migrate_db()

def migrate_db():
    """Adds missing columns to existing tables safely."""
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()
    
    # 1. Medicine Columns
    cursor.execute("PRAGMA table_info(Medicine)")
    cols = [row[1] for row in cursor.fetchall()]
    
    updates = {
        "batch_no": "TEXT DEFAULT ''",
        "hsn_code": "TEXT DEFAULT ''", 
        "rack_no": "TEXT DEFAULT ''",
        "gst_rate": "REAL DEFAULT 0", 
        "discount": "REAL DEFAULT 0",
        "barcode": "TEXT DEFAULT ''"
    }
    for col, definition in updates.items():
        if col not in cols:
            try: cursor.execute(f"ALTER TABLE Medicine ADD COLUMN {col} {definition}")
            except: pass

    # 2. Purchase Invoice Columns
    cursor.execute("PRAGMA table_info(Purchase_Invoice)")
    pi_cols = [row[1] for row in cursor.fetchall()]
    pi_updates = {
        "payment_mode": "TEXT",
        "paid_amount": "REAL DEFAULT 0",
        "balance": "REAL DEFAULT 0"
    }
    for col, definition in pi_updates.items():
        if col not in pi_cols:
            try: cursor.execute(f"ALTER TABLE Purchase_Invoice ADD COLUMN {col} {definition}")
            except: pass

    # 3. Supplier Columns
    cursor.execute("PRAGMA table_info(Supplier)")
    sup_cols = [row[1] for row in cursor.fetchall()]
    if "supplier_type" not in sup_cols:
        try: cursor.execute("ALTER TABLE Supplier ADD COLUMN supplier_type TEXT")
        except: pass

    conn.commit()
    conn.close()

# --- HELPER FUNCTIONS ---
def get_all_medicines():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Med_id, Med_name, tabs_per_strip, rate_per_tab, Quantity, Type,
               Purchase_Price, Sale_Price, MFG_Date, EXP_Date,
               hsn_code, rack_no, gst_rate, discount, barcode
        FROM Medicine ORDER BY Med_name ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
    print("Database initialized and migrated.")