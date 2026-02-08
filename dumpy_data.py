import sqlite3
import random
import datetime
from datetime import timedelta

DB_NAME = "pharmacy.db"

# --- SAMPLE DATA LISTS ---

PHARMACY_INFO = {
    "p_name": "Apollo Pharmacy (Indiranagar)",
    "phone": "+91 98765 43210",
    "email": "contact@apollopharmacy.in",
    "gstin": "29ABCDE1234F1Z5",
    "location": "No. 42, 100 Feet Road, Indiranagar, Bengaluru, Karnataka - 560038"
}

SUPPLIERS = [
    ("Mahaveer Medi-Sales", "Rajesh Kumar", "rajesh@mahaveer.com"),
    ("Karnataka Pharma Distributors", "Suresh Gowda", "sales@kpd.com"),
    ("Sun Pharma Supply Chain", "Amit Shah", "supply@sunpharma.com"),
    ("Vardhman Health Agency", "Vikas Jain", "vikas@vardhman.in")
]

# (Name, Manufacturer, Type, Purchase_Price, Sale_Price, Tabs_Per_Strip, Stock_Qty, Expiry_Days_From_Now)
# Stock < 10 triggers Low Stock Alert
# Expiry < 120 triggers Expiry Alert
MEDICINES_DATA = [
    # --- LOW STOCK ITEMS (< 10) ---
    ("Azithral 500", "Alembic", "Tablet", 100.00, 130.00, 5, 5, 400),       # Low Stock (5)
    ("Volini Gel", "Sun Pharma", "Gel", 130.00, 165.00, 1, 8, 500),         # Low Stock (8)

    # --- EXPIRING SOON ITEMS (< 120 Days) ---
    ("Dolo 650mg", "Micro Labs", "Tablet", 24.50, 32.00, 15, 100, 30),      # Expires in 30 days!
    ("Ascoril LS", "Glenmark", "Syrup", 95.00, 118.00, 1, 50, 60),          # Expires in 60 days!

    # --- NORMAL ITEMS ---
    ("Crocin Advance", "GSK", "Tablet", 15.00, 20.00, 15, 80, 600),
    ("Pantocid 40", "Sun Pharma", "Tablet", 120.00, 155.00, 15, 60, 550),
    ("Augmentin 625", "GSK", "Tablet", 180.00, 223.00, 10, 40, 700),
    ("Shelcal 500", "Torrent", "Tablet", 110.00, 135.00, 15, 90, 450),
    ("Becosules Z", "Pfizer", "Capsule", 40.00, 55.00, 20, 120, 300),
    ("Allegra 120mg", "Sanofi", "Tablet", 160.00, 210.00, 10, 45, 365),
    ("Benadryl Cough", "J&J", "Syrup", 110.00, 135.00, 1, 35, 400),
    ("Thyronorm 100mcg", "Abbott", "Tablet", 140.00, 185.00, 120, 15, 500),
    ("Saridon", "Piramal", "Tablet", 35.00, 48.00, 10, 200, 600),
    ("Limcee 500mg", "Abbott", "Tablet", 20.00, 28.00, 15, 150, 550),
    ("Zincovit", "Apex Labs", "Tablet", 90.00, 115.00, 15, 100, 480)
]

PATIENTS = ["Rahul Dravid", "Anjali Sharma", "Vikram Singh", "Priya Menon", "Mohd. Rafiq", "Sneha Gupta", "Arjun Reddy"]
DOCTORS = ["Dr. Devi Shetty", "Dr. Naresh Trehan", "Dr. A. Rao", "Dr. S. Kulkarni", "Self"]

def populate_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print("--- CLEARING OLD DATA ---")
    cursor.execute("DELETE FROM Medicine")
    cursor.execute("DELETE FROM Bill")
    cursor.execute("DELETE FROM Bill_Item")
    cursor.execute("DELETE FROM Supplier")
    cursor.execute("DELETE FROM Pharmacy")
    cursor.execute("DELETE FROM sqlite_sequence") # Reset auto-increment IDs
    
    print("--- INSERTING PHARMACY DETAILS ---")
    cursor.execute("""
        INSERT INTO Pharmacy (p_name, phone, email, GSTIN, location)
        VALUES (?, ?, ?, ?, ?)
    """, (PHARMACY_INFO['p_name'], PHARMACY_INFO['phone'], PHARMACY_INFO['email'], 
          PHARMACY_INFO['gstin'], PHARMACY_INFO['location']))

    print("--- INSERTING SUPPLIERS ---")
    cursor.executemany("INSERT INTO Supplier (Sup_name, contact, email) VALUES (?, ?, ?)", SUPPLIERS)

    print("--- INSERTING MEDICINES ---")
    today = datetime.date.today()
    med_ids = []

    for med in MEDICINES_DATA:
        name, mfg, m_type, p_price, s_price, tabs, qty, expiry_days = med
        
        # Calculate derived values
        rate_per_tab = s_price / tabs
        mfg_date = (today - timedelta(days=365)).strftime("%Y-%m-%d") # Manufactured 1 year ago
        exp_date = (today + timedelta(days=expiry_days)).strftime("%Y-%m-%d") # Custom expiry logic
        
        cursor.execute("""
            INSERT INTO Medicine 
            (Med_name, Manufacturer, Type, Purchase_Price, Sale_Price, tabs_per_strip, rate_per_tab, Quantity, MFG_Date, EXP_Date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, mfg, m_type, p_price, s_price, tabs, rate_per_tab, qty, mfg_date, exp_date))
        med_ids.append(cursor.lastrowid)

    print("--- GENERATING DUMMY SALES (WHOLE NUMBERS ONLY) ---")
    
    # Create 15 random bills
    for _ in range(15):
        # Random Date
        bill_date = (datetime.datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d %H:%M:%S")
        patient = random.choice(PATIENTS)
        doctor = random.choice(DOCTORS)
        pay_method = random.choice(["Cash", "UPI", "Card"])
        
        # Create Bill Header
        cursor.execute("""
            INSERT INTO Bill (patient, doctor, payment_method, discount, total_sum, bill_date)
            VALUES (?, ?, ?, 0, 0, ?)
        """, (patient, doctor, pay_method, bill_date))
        bill_id = cursor.lastrowid
        
        # Add 1 to 3 items
        num_items = random.randint(1, 3)
        selected_meds = random.sample(med_ids, num_items)
        bill_total = 0
        
        for med_id in selected_meds:
            # Fetch details
            cursor.execute("SELECT Sale_Price, Quantity FROM Medicine WHERE Med_id = ?", (med_id,))
            res = cursor.fetchone()
            if not res: continue
            
            s_price, current_stock = res
            
            # NO LOOSE TABS -> WHOLE NUMBER QUANTITY ONLY
            # Buying 1 or 2 Packs/Strips
            qty_bought = random.randint(1, 2) 
            
            # Ensure we don't sell into negative for this dummy data
            if current_stock < qty_bought:
                continue

            item_total = qty_bought * s_price
            bill_total += item_total
            
            # Insert Bill Item (Integer Quantity)
            cursor.execute("""
                INSERT INTO Bill_Item (Med_id, Bill_id, quantity)
                VALUES (?, ?, ?)
            """, (med_id, bill_id, qty_bought))
            
            # Deduct Stock
            cursor.execute("UPDATE Medicine SET Quantity = Quantity - ? WHERE Med_id = ?", (qty_bought, med_id))

        # Update Bill Total
        cursor.execute("UPDATE Bill SET total_sum = ? WHERE Bill_id = ?", (bill_total, bill_id))

    conn.commit()
    conn.close()
    print("--- SUCCESS: DATA INSERTED (No Decimal Qty, Included Alerts) ---")

if __name__ == "__main__":
    populate_data()