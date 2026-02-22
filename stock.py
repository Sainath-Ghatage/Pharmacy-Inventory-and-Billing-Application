import sqlite3
import random
import time
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

DB_NAME = "pharmacy.db"

# ==========================================
# DATA POOLS FOR REALISTIC INDIAN CONTEXT
# ==========================================
MANUFACTURERS = ["Sun Pharma", "Cipla", "Abbott", "Mankind", "Alkem", "Torrent", "Lupin", "Dr. Reddy's", "Zydus", "Intas", "Macleods", "Aristo", "Glenmark", "GSK", "P&G", "Himalaya"]
RACKS = ["A-1", "A-2", "A-3", "B-1", "B-2", "C-1", "C-2", "D-1", "Fridge", "Floor Display", "Gondola"]

TABLETS = [
    ("Dolo", "Fever/Pain"), ("Pan", "Acidity"), ("Pantocid", "Acidity"), ("Augmentin", "Antibiotic"), 
    ("Azee", "Antibiotic"), ("Calpol", "Fever"), ("Cetirizine", "Allergy"), ("Allegra", "Allergy"), 
    ("Telma", "Blood Pressure"), ("Amlokind", "Blood Pressure"), ("Glycomet", "Diabetes"), 
    ("Thyronorm", "Thyroid"), ("Shelcal", "Calcium"), ("Zincovit", "Multivitamin"), 
    ("Montair", "Asthma/Allergy"), ("Zerodol", "Pain Relief"), ("Atorva", "Cholesterol"),
    ("Clavam", "Antibiotic"), ("Ecosprin", "Heart/Blood Thinning"), ("Omez", "Acidity")
]
TAB_SUFFIXES = ["250mg", "500mg", "650mg", "SR", "D", "Plus", "CV", "40", "20", "M", "AM", "Forte"]

SYRUPS = [
    ("Benadryl", "Cough"), ("Corex", "Cough"), ("Ascoril", "Cough"), ("Digene", "Acidity"), 
    ("Gelusil", "Acidity"), ("Dexorange", "Blood Builder"), ("Bro-Zedex", "Cough"), 
    ("Honitus", "Cough"), ("Grilinctus", "Cough"), ("Ondem", "Anti-Vomiting")
]
SYR_SUFFIXES = ["Syrup 100ml", "Syrup 60ml", "LS Syrup", "Junior 60ml", "Suspension"]

CREAMS = [
    ("Volini", "Pain Relief"), ("Moov", "Pain Relief"), ("Betadine", "Antiseptic"), 
    ("Soframycin", "Antiseptic"), ("Candid", "Antibacterial"), ("Fourderm", "Skin Infection"), 
    ("Quadriderm", "Skin Infection"), ("Itch Guard", "Anti-Fungal"), ("Boroline", "Antiseptic")
]
CRM_SUFFIXES = ["Gel 30g", "Cream 15g", "Ointment 20g", "Powder 50g"]

INJECTIONS = [
    ("Monocef", "Antibiotic"), ("Pantop I.V.", "Acidity"), ("Tetvac", "Tetanus"), 
    ("Eldervit", "Vitamin Supplement"), ("Tramazac", "Severe Pain"), ("Decdan", "Steroid")
]

DROPS = [
    ("Refresh Tears", "Dry Eyes"), ("Ciplox Eye", "Eye Infection"), ("Otrivin", "Blocked Nose"), 
    ("Nasivion", "Blocked Nose"), ("Clearwax", "Ear Wax"), ("Moxicip", "Eye/Ear Antibiotic")
]

POWDERS = [("Eno", "Acidity"), ("ORSL", "Rehydration"), ("Candid Dusting", "Anti-Fungal"), ("ProteinX", "Energy")]

PERSONAL_CARE = [("Dettol Handwash", "Hygiene"), ("Sensodyne Paste", "Dental"), ("Himalaya Sanitizer", "Hygiene"), ("Oral-B Brush", "Dental"), ("Pampers", "Baby Care")]

DEVICES = [
    ("Digital Thermometer", "Fever Check", "Omron"), ("BP Monitor", "BP Check", "Dr. Morepen"), 
    ("Glucometer", "Sugar Check", "Accu-Chek"), ("Pulse Oximeter", "Oxygen Check", "BPL"), 
    ("Vaporizer", "Steam", "Dr. Trust"), ("Hot Water Bag", "Pain Relief", "Polo"), 
    ("Crepe Bandage", "Support", "Flamingo"), ("Pregnancy Kit", "Test Kit", "Prega News")
]

DOCTORS = [
    ("Dr. Amit Sharma", "Cardiologist", "Apollo Hospital", "9876543210"),
    ("Dr. Priya Singh", "General Physician", "City Care Clinic", "9876543211"),
    ("Dr. Rajesh Gupta", "Pediatrician", "KIMS Hospital", "9876543212"),
    ("Dr. Sneha Reddy", "Dermatologist", "Skin & Hair Clinic", "9876543213"),
    ("Dr. Vikram Patel", "Orthopedic", "Sunshine Hospital", "9876543214")
]

CUSTOMERS = [
    ("Rahul Verma", "9988776655", "rahul@email.com", "HSR Layout, Hyderabad"),
    ("Anjali Desai", "9988776656", "anjali@email.com", "Koramangala, Bangalore"),
    ("Mohit Agarwal", "9988776657", "mohit@email.com", "Andheri West, Mumbai"),
    ("Sunita Rao", "9988776658", "sunita@email.com", "Anna Nagar, Chennai"),
    ("Karan Kapoor", "9988776659", "karan@email.com", "Vasant Kunj, Delhi"),
    ("Pooja Joshi", "9988776650", "pooja@email.com", "Salt Lake, Chennai"),
    ("Sandeep Nair", "9988776651", "sandeep@email.com", "Banjara Hills, Hyderabad"),
    ("Neha Menon", "9988776652", "neha@email.com", "Indiranagar, Bangalore")
]

SUPPLIERS = [
    ("Apollo Distributors", "9123456780", "sales@apollodist.com", "27AADCA1234E1Z1", "Mumbai, MH", "Wholesaler"),
    ("MedLife Suppliers", "9123456781", "info@medlifesup.com", "29BBDCM5678G1Z2", "Bangalore, KA", "Distributor"),
    ("Balaji Pharma Agency", "9123456782", "contact@balajipharma.com", "36CCDCB9012H1Z3", "Hyderabad, TG", "Wholesaler"),
    ("Sanjeevani Medicals", "9123456783", "orders@sanjeevani.com", "33DDFCR3456K1Z4", "Chennai, TN", "Distributor")
]

EXPENSE_TYPES = ["Electricity Bill", "Water Bill", "Shop Rent", "Employee Salary", "Maintenance", "Stationery"]
PAYMENT_MODES = ["Cash", "UPI", "Bank Transfer", "Credit", "Card"]

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def generate_dates(status):
    today = date.today()
    if status == "expired":
        exp_dt = today - relativedelta(months=random.randint(1, 12))
    elif status == "expiring_soon":
        exp_dt = today + relativedelta(months=random.randint(1, 3))
    else:
        exp_dt = today + relativedelta(months=random.randint(8, 36))
    mfg_dt = exp_dt - relativedelta(months=24)
    return mfg_dt.strftime("%m/%y"), exp_dt.strftime("%m/%y")

def random_past_date(days_back=90):
    start_date = datetime.now() - timedelta(days=days_back)
    random_days = random.randrange(days_back)
    random_seconds = random.randrange(86400)
    return (start_date + timedelta(days=random_days, seconds=random_seconds)).strftime("%Y-%m-%d %H:%M:%S")

def random_past_date_only(days_back=90):
    return random_past_date(days_back).split()[0]

def ensure_schema_update(cursor):
    """Ensures dynamic columns created by the application exist to prevent crashing."""
    cursor.execute("PRAGMA table_info(Product_Stock)")
    columns = [info[1] for info in cursor.fetchall()]
    if "min_qty" not in columns: cursor.execute("ALTER TABLE Product_Stock ADD COLUMN min_qty INTEGER DEFAULT 10")
    
    cursor.execute("PRAGMA table_info(Purchase_Return)")
    pr_cols = [info[1] for info in cursor.fetchall()]
    if "payment_mode" not in pr_cols: cursor.execute("ALTER TABLE Purchase_Return ADD COLUMN payment_mode TEXT DEFAULT 'Credit'")
    if "amount_received" not in pr_cols: cursor.execute("ALTER TABLE Purchase_Return ADD COLUMN amount_received REAL DEFAULT 0")
    if "balance" not in pr_cols: cursor.execute("ALTER TABLE Purchase_Return ADD COLUMN balance REAL DEFAULT 0")
        
    cursor.execute("PRAGMA table_info(Bill)")
    b_cols = [info[1] for info in cursor.fetchall()]
    if "paid_amount" not in b_cols: cursor.execute("ALTER TABLE Bill ADD COLUMN paid_amount REAL DEFAULT 0")
    if "balance" not in b_cols: cursor.execute("ALTER TABLE Bill ADD COLUMN balance REAL DEFAULT 0")

# ==========================================
# MAIN SEED FUNCTION
# ==========================================
def seed_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    ensure_schema_update(cursor)
    
    print("⏳ Seeding Pharmacy Profile...")
    cursor.execute("SELECT COUNT(*) FROM Pharmacy")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO Pharmacy (p_name, location, phone, email, license_no, GSTIN, smtp_email, smtp_password, printer_type)
            VALUES ('LifeCare Pharmacy', 'Shop No 14, Main Road, City Center', '9876543210', 'contact@lifecare.com', 'DL-MH-2026-101', '27AADCA1234E1Z1', 'bot@lifecare.com', 'dummy_app_pass', 'Thermal Printer (80mm/58mm)')
        """)

    print("⏳ Seeding Partners (Doctors, Customers, Suppliers)...")
    doc_ids = []
    for d in DOCTORS:
        cursor.execute("INSERT INTO Doctor (Name, Specialization, Hospital, Phone) VALUES (?, ?, ?, ?)", d)
        doc_ids.append((cursor.lastrowid, d[0]))

    cust_ids = []
    for c in CUSTOMERS:
        cursor.execute("INSERT INTO Customer (Name, Phone, Email, Address, balance) VALUES (?, ?, ?, ?, ?)", (c[0], c[1], c[2], c[3], random.randint(0, 1500)))
        cust_ids.append((cursor.lastrowid, c[0]))

    supp_ids = []
    for s in SUPPLIERS:
        cursor.execute("INSERT INTO Supplier (Sup_name, contact, email, gstin, address, supplier_type, balance) VALUES (?, ?, ?, ?, ?, ?, ?)", (s[0], s[1], s[2], s[3], s[4], s[5], random.randint(0, 50000)))
        supp_ids.append((cursor.lastrowid, s[0]))

    print("⏳ Generating 200 Products (Tablets, Syrups, Injections, Drops, Devices)...")
    products = []
    for _ in range(95): # Tablets
        b = random.choice(TABLETS)
        products.append({"name": f"{b[0]} {random.choice(TAB_SUFFIXES)}", "type": "Tablet", "uses": b[1], "mfg": random.choice(MANUFACTURERS), "hsn": f"300490{random.randint(10,99)}", "gst": 12.0, "tps": random.choice([10, 15, 20])})
    for _ in range(35): # Syrups
        b = random.choice(SYRUPS)
        products.append({"name": f"{b[0]} {random.choice(SYR_SUFFIXES)}", "type": "Syrup", "uses": b[1], "mfg": random.choice(MANUFACTURERS), "hsn": f"300490{random.randint(10,99)}", "gst": 12.0, "tps": 1})
    for _ in range(25): # Creams
        b = random.choice(CREAMS)
        products.append({"name": f"{b[0]} {random.choice(CRM_SUFFIXES)}", "type": "Cream", "uses": b[1], "mfg": random.choice(MANUFACTURERS), "hsn": f"300490{random.randint(10,99)}", "gst": 12.0, "tps": 1})
    for _ in range(15): # Injections
        b = random.choice(INJECTIONS)
        products.append({"name": f"{b[0]} Vial/Ampoule", "type": "Injection", "uses": b[1], "mfg": random.choice(MANUFACTURERS), "hsn": f"300490{random.randint(10,99)}", "gst": 12.0, "tps": 1})
    for _ in range(10): # Drops
        b = random.choice(DROPS)
        products.append({"name": f"{b[0]} 10ml", "type": "Drops", "uses": b[1], "mfg": random.choice(MANUFACTURERS), "hsn": f"300490{random.randint(10,99)}", "gst": 12.0, "tps": 1})
    for _ in range(10): # Powders
        b = random.choice(POWDERS)
        products.append({"name": f"{b[0]} 100g", "type": "Powder", "uses": b[1], "mfg": random.choice(MANUFACTURERS), "hsn": f"300490{random.randint(10,99)}", "gst": 18.0, "tps": 1})
    for _ in range(10): # Devices & Personal
        b = random.choice(DEVICES + PERSONAL_CARE)
        products.append({"name": b[0], "type": "Medical Devices" if len(b)==3 else "Personal Care & Wellness", "uses": b[1], "mfg": b[2] if len(b)==3 else random.choice(MANUFACTURERS), "hsn": f"901890{random.randint(10,99)}", "gst": 18.0, "tps": 1})

    random.shuffle(products)
    products = products[:200]

    db_products = [] # To hold id, name, price etc for billing
    for prod in products:
        cursor.execute("INSERT INTO Product_Details (prod_name, manufacturer, hsn_code, gst, rack_no, type, tabs_per_strip, uses) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                       (prod["name"], prod["mfg"], prod["hsn"], prod["gst"], random.choice(RACKS), prod["type"], prod["tps"], prod["uses"]))
        prod_id = cursor.lastrowid
        
        # Stock Status Distribution
        rand_status = random.random()
        if rand_status < 0.70: status = "normal"
        elif rand_status < 0.80: status = "low_stock"
        elif rand_status < 0.90: status = "expiring_soon"
        else: status = "expired"

        min_qty = random.randint(10, 30) * prod["tps"]
        qty = random.randint(1, min_qty - 1) if status == "low_stock" else random.randint(min_qty + 10, min_qty + 300)
        mfg_date, exp_date = generate_dates(status)
        batch_no = f"BTH-{random.randint(10000, 99999)}"

        mrp_per_strip = random.randint(30, 800)
        purchase_per_strip = mrp_per_strip * random.uniform(0.60, 0.85)
        
        sale_rate_unit = round(mrp_per_strip / prod["tps"], 2)
        purchase_rate_unit = round(purchase_per_strip / prod["tps"], 2)

        cursor.execute("""
            INSERT INTO Product_Stock (prod_id, purchase_rate, sale_rate, rate_per_tab, quantity, mfg_date, exp_date, batch_no, discount, min_qty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (prod_id, purchase_rate_unit, sale_rate_unit, sale_rate_unit, qty, mfg_date, exp_date, batch_no, 0, min_qty))
        
        stock_id = cursor.lastrowid
        db_products.append({
            "prod_id": prod_id, "stock_id": stock_id, "name": prod["name"], "batch": batch_no, "exp": exp_date,
            "sale_rate_unit": sale_rate_unit, "purchase_rate_unit": purchase_rate_unit, "gst": prod["gst"], "tps": prod["tps"]
        })

    print("⏳ Simulating 60 Sales Bills (History)...")
    for _ in range(60):
        pat_id, pat_name = random.choice(cust_ids) if random.random() > 0.3 else (None, "Walk-in")
        doc_id, doc_name = random.choice(doc_ids) if random.random() > 0.5 else (None, "")
        
        bill_date = random_past_date(60)
        pay_mode = random.choice(PAYMENT_MODES)
        
        # Insert empty bill first
        cursor.execute("INSERT INTO Bill (patient_name, doctor_name, payment_method, discount, total_sum, paid_amount, balance, bill_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (pat_name, doc_name, pay_mode, 0, 0, 0, 0, bill_date))
        bill_id = cursor.lastrowid
        
        items_count = random.randint(1, 5)
        bill_total = 0.0
        
        for _ in range(items_count):
            p = random.choice(db_products)
            qty_units = random.randint(1, 3) * p["tps"]
            item_total = qty_units * p["sale_rate_unit"]
            bill_total += item_total
            
            cursor.execute("INSERT INTO Bill_Item (Bill_id, Prod_id, quantity, unit_price, total_price) VALUES (?, ?, ?, ?, ?)",
                           (bill_id, p["prod_id"], qty_units, p["sale_rate_unit"], item_total))
        
        paid = bill_total if pay_mode != "Credit" else random.choice([0, bill_total * 0.5])
        bal = bill_total - paid
        cursor.execute("UPDATE Bill SET total_sum=?, paid_amount=?, balance=? WHERE Bill_id=?", (bill_total, paid, bal, bill_id))

    print("⏳ Simulating 15 Purchase Invoices & 10 Purchase Orders...")
    for _ in range(15):
        s_id, s_name = random.choice(supp_ids)
        inv_date = random_past_date_only(120)
        inv_no = f"INV-{random.randint(1000,9999)}"
        pay_mode = random.choice(["Cash", "Bank Transfer", "Credit"])
        
        cursor.execute("INSERT INTO Purchase_Invoice (invoice_number, supp_id, invoice_date, payment_mode, total_amount, paid_amount, balance, created_at) VALUES (?, ?, ?, ?, 0, 0, 0, ?)",
                       (inv_no, s_id, inv_date, pay_mode, inv_date))
        inv_id = cursor.lastrowid
        
        inv_total = 0.0
        for _ in range(random.randint(3, 8)):
            p = random.choice(db_products)
            qty_units = random.randint(50, 200)
            item_total = qty_units * p["purchase_rate_unit"]
            inv_total += item_total
            
            cursor.execute("INSERT INTO Purchase_Invoice_Item (invoice_id, Prod_id, batch_no, expiry_date, quantity, purchase_rate_incl, mrp, total_amount) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (inv_id, p["prod_id"], p["batch"], p["exp"], qty_units, p["purchase_rate_unit"], p["sale_rate_unit"] * p["tps"], item_total))
        
        cursor.execute("UPDATE Purchase_Invoice SET total_amount=?, paid_amount=? WHERE invoice_id=?", (inv_total, inv_total if pay_mode != "Credit" else 0, inv_id))

    for _ in range(10):
        s_id, _ = random.choice(supp_ids)
        o_date = random_past_date_only(30)
        status = random.choice(["Created", "Sent", "Received"])
        cursor.execute("INSERT INTO Purchase_order (supp_id, order_date, status) VALUES (?, ?, ?)", (s_id, o_date, status))
        po_id = cursor.lastrowid
        for _ in range(random.randint(2, 6)):
            p = random.choice(db_products)
            cursor.execute("INSERT INTO PO_item (po_id, Prod_id, Quantity) VALUES (?, ?, ?)", (po_id, p["prod_id"], random.randint(20, 100)))

    print("⏳ Simulating 5 Purchase Returns...")
    for _ in range(5):
        s_id, _ = random.choice(supp_ids)
        r_date = random_past_date_only(60)
        r_no = f"PR-{random.randint(100,999)}"
        
        cursor.execute("INSERT INTO Purchase_Return (return_number, supp_id, return_date, total_amount, payment_mode) VALUES (?, ?, ?, 0, 'Credit')", (r_no, s_id, r_date))
        ret_id = cursor.lastrowid
        
        ret_total = 0.0
        for _ in range(random.randint(1, 3)):
            p = random.choice(db_products)
            qty = random.randint(5, 20)
            amt = qty * p["purchase_rate_unit"]
            ret_total += amt
            cursor.execute("INSERT INTO Purchase_Return_Item (return_id, Prod_id, batch_no, expiry_date, return_qty, return_amount) VALUES (?, ?, ?, ?, ?, ?)",
                           (ret_id, p["prod_id"], p["batch"], p["exp"], qty, amt))
            
        cursor.execute("UPDATE Purchase_Return SET total_amount=?, balance=? WHERE return_id=?", (ret_total, ret_total, ret_id))

    print("⏳ Simulating 45 Business Expenses...")
    for _ in range(45):
        e_type = random.choice(EXPENSE_TYPES)
        amt = random.randint(500, 15000)
        e_date = random_past_date_only(90)
        mode = random.choice(PAYMENT_MODES)
        cursor.execute("INSERT INTO Expenses (expense_type, description, amount, expense_date, payment_mode) VALUES (?, ?, ?, ?, ?)",
                       (e_type, f"Monthly {e_type}", amt, e_date, mode))

    conn.commit()
    conn.close()
    
    print("\n✅ SEEDING COMPLETE! Your Pharmacy System is fully loaded with realistic Indian data.")

if __name__ == "__main__":
    seed_database()