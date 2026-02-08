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
    if not conn:
        return

    cursor = conn.cursor()

    # --- MEDICINE TABLE ---
    # Renamed 'Form' to 'Type'
    # Added 'tabs_per_strip' and 'rate_per_tab' for loose billing
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
        EXP_Date TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Bill (
        Bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient TEXT,
        doctor TEXT,
        payment_method TEXT,
        discount REAL,
        total_sum REAL,
        bill_date TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Bill_Item (
        Med_id INTEGER,
        Bill_id INTEGER,
        quantity INTEGER,
        FOREIGN KEY (Med_id) REFERENCES Medicine(Med_id),
        FOREIGN KEY (Bill_id) REFERENCES Bill(Bill_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Supplier (
        Supp_id INTEGER PRIMARY KEY AUTOINCREMENT,
        Sup_name TEXT,
        contact TEXT,
        email TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Purchase_order (
        po_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_date TEXT,
        supp_id INTEGER,
        status TEXT,
        FOREIGN KEY (supp_id) REFERENCES Supplier(Supp_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS PO_item (
        PO_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_id INTEGER,
        Med_id INTEGER,
        Quantity INTEGER,
        FOREIGN KEY (po_id) REFERENCES Purchase_order(po_id),
        FOREIGN KEY (Med_id) REFERENCES Medicine(Med_id)
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

    conn.commit()
    conn.close()


# -------------------------
# COMMON DATA FUNCTIONS
# -------------------------

def get_all_medicines():
    """
    Returns a list of all medicines with specific columns needed for Billing.
    Order: ID, Name, TabsPerStrip, RatePerTab, Qty, Type, PurchasePrice, SalePrice, Mfg, Exp
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Med_id, Med_name, tabs_per_strip, rate_per_tab, Quantity, Type,
               Purchase_Price, Sale_Price, MFG_Date, EXP_Date
        FROM Medicine
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

# Run initialization immediately when this module is run directly
if __name__ == "__main__":
    init_db()
    print("Database initialized.")