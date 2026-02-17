import sys
import datetime
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QSpinBox, QComboBox, QFrame, QSizePolicy, QMessageBox,
    QGridLayout, QAbstractItemView, QDoubleSpinBox, QCompleter, QTabWidget
)
from PyQt6.QtGui import QFont, QTextDocument, QColor, QBrush, QPalette, QIcon
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

import database 

# --- COLORS ---
COLOR_NAVBAR = "#0d47a1"
COLOR_BG = "#f4f7f6"
COLOR_WHITE = "#ffffff"
COLOR_GREEN_BTN = "#198754"
COLOR_RED_BTN = "#dc3545"
COLOR_BLACK = "#000000"

# --- GLOBAL STYLES ---
GLOBAL_STYLE = """
    QWidget { font-family: 'Segoe UI', sans-serif; background-color: #f4f7f6; color: black; }
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { 
        background-color: white; color: black; border: 1px solid #ccc; padding: 5px; 
    }
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
        border: 2px solid #0d47a1;
    }
    QTableWidget { background-color: white; color: black; gridline-color: #ccc; selection-background-color: #e3f2fd; selection-color: black; }
    QHeaderView::section { background-color: #e0e0e0; color: black; padding: 5px; border: 1px solid #ccc; font-weight: bold; }
    QListWidget { background-color: white; color: black; }
    QPushButton { color: white; }
    
    /* POPUP FIXES */
    QMessageBox { background-color: white; color: black; }
    QMessageBox QLabel { color: black; }
    QMessageBox QPushButton { background-color: #0d47a1; color: white; padding: 5px 15px; border-radius: 3px; }
"""

class SingleBillTab(QWidget):
    """
    A single billing session tab.
    """
    def __init__(self):
        super().__init__()
        self.cart_items = []
        self.current_selected_stock = None
        self.customer_names = []
        self.doctor_names = []
        self.editing_bill_id = None  # Track if we are editing an existing bill
        
        self.init_ui()
        self.refresh_cache()
        self.search_medicine("")

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # --- LEFT PANEL ---
        left_panel = QFrame()
        left_panel.setStyleSheet(f"background-color: {COLOR_WHITE}; border-radius: 10px; border: 1px solid #ccc;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)

        lbl_search = QLabel("Find Medicine")
        lbl_search.setStyleSheet(f"color: {COLOR_NAVBAR}; font-size: 16px; font-weight: bold;")
        left_layout.addWidget(lbl_search)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Type Name, ID or Batch...")
        self.search_input.setFixedHeight(40)
        self.search_input.textChanged.connect(self.search_medicine)
        left_layout.addWidget(self.search_input)

        self.match_list = QListWidget()
        self.match_list.setStyleSheet("border: 1px solid #ccc; color: black; background-color: white;")
        self.match_list.itemClicked.connect(self.select_medicine_from_list)
        left_layout.addWidget(self.match_list)

        self.detail_frame = QFrame()
        self.detail_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 10px; border: 1px solid #ddd;")
        det_layout = QVBoxLayout(self.detail_frame)
        self.lbl_sel_name = QLabel("No Medicine Selected")
        self.lbl_sel_name.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLOR_NAVBAR}; border: none;")
        self.lbl_sel_info = QLabel("Batch: - | Stock: - | Rack: -")
        self.lbl_sel_info.setStyleSheet("font-size: 12px; border: none; color: black;")
        self.lbl_sel_info.setWordWrap(True)
        self.lbl_conversion = QLabel("Conversion: -")
        self.lbl_conversion.setStyleSheet("color: #0d47a1; font-weight: bold; font-size: 11px; border: none;")
        self.lbl_sel_uses = QLabel("Uses: -")
        self.lbl_sel_uses.setStyleSheet("color: #555555; font-style: italic; font-size: 12px; border: none;")
        self.lbl_sel_uses.setWordWrap(True)
        det_layout.addWidget(self.lbl_sel_name); det_layout.addWidget(self.lbl_sel_info)
        det_layout.addWidget(self.lbl_conversion); det_layout.addWidget(self.lbl_sel_uses)
        left_layout.addWidget(self.detail_frame)

        action_layout = QGridLayout()
        action_layout.setVerticalSpacing(10)
        self.spin_strips = QSpinBox(); self.spin_strips.setRange(0, 9999); self.spin_strips.setFixedHeight(40)
        self.spin_loose = QSpinBox(); self.spin_loose.setRange(0, 9999); self.spin_loose.setFixedHeight(40)
        self.spin_disc = QDoubleSpinBox(); self.spin_disc.setRange(0, 100); self.spin_disc.setFixedHeight(40); self.spin_disc.setSuffix("%")
        self.btn_add = QPushButton("ADD TO BILL ➔")
        self.btn_add.setFixedHeight(45)
        self.btn_add.clicked.connect(self.add_to_cart)
        self.btn_add.setStyleSheet(f"background-color: {COLOR_NAVBAR}; color: white; font-weight: bold; border-radius: 5px;")
        
        l1=QLabel("Strips:"); l1.setStyleSheet("color:black;"); action_layout.addWidget(l1, 0, 0); action_layout.addWidget(self.spin_strips, 0, 1)
        l2=QLabel("Tablets:"); l2.setStyleSheet("color:black;"); action_layout.addWidget(l2, 0, 2); action_layout.addWidget(self.spin_loose, 0, 3)
        l3=QLabel("Disc %:"); l3.setStyleSheet("color:black;"); action_layout.addWidget(l3, 1, 0); action_layout.addWidget(self.spin_disc, 1, 1)
        action_layout.addWidget(self.btn_add, 2, 0, 1, 4)
        left_layout.addLayout(action_layout)

        # --- RIGHT PANEL ---
        right_panel = QFrame()
        right_panel.setStyleSheet(f"background-color: {COLOR_WHITE}; border-radius: 10px; border: 1px solid #ccc;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)

        cust_layout = QHBoxLayout()
        self.inp_patient = QLineEdit(); self.inp_patient.setPlaceholderText("Patient Name"); self.inp_patient.setFixedHeight(35)
        self.pat_completer = QCompleter(self.customer_names); self.pat_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive); self.inp_patient.setCompleter(self.pat_completer)
        self.inp_doctor = QLineEdit(); self.inp_doctor.setPlaceholderText("Doctor Name"); self.inp_doctor.setFixedHeight(35)
        self.doc_completer = QCompleter(self.doctor_names); self.doc_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive); self.inp_doctor.setCompleter(self.doc_completer)
        cust_layout.addWidget(QLabel("Patient:")); cust_layout.addWidget(self.inp_patient, 1)
        cust_layout.addWidget(QLabel("Doctor:")); cust_layout.addWidget(self.inp_doctor, 1)
        right_layout.addLayout(cust_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["Medicine", "Batch", "Exp", "Qty", "Rate", "GST", "Disc", "Total", "Del"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(8, 40)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.cellClicked.connect(self.load_item_from_cart)
        right_layout.addWidget(self.table)

        footer_layout = QGridLayout()
        self.cmb_payment = QComboBox(); self.cmb_payment.addItems(["Cash", "UPI", "Card", "Credit"]); self.cmb_payment.setFixedHeight(35)
        self.lbl_grand_total = QLabel("Total: ₹0.00"); self.lbl_grand_total.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_NAVBAR}; border: none;")
        self.lbl_balance = QLabel("Balance: ₹0.00"); self.lbl_balance.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLOR_RED_BTN}; border: none;")
        self.spin_paid = QDoubleSpinBox(); self.spin_paid.setRange(0, 999999); self.spin_paid.setPrefix("Paid: ₹ "); self.spin_paid.setFixedHeight(35); self.spin_paid.valueChanged.connect(self.calculate_balance)
        self.btn_checkout = QPushButton("CHECKOUT & PRINT")
        self.btn_checkout.setFixedHeight(50); self.btn_checkout.clicked.connect(self.process_checkout)
        self.btn_checkout.setStyleSheet(f"background-color: {COLOR_GREEN_BTN}; color: white; font-weight: bold; border-radius: 5px; font-size: 15px;")
        
        footer_layout.addWidget(QLabel("Payment Mode:"), 0, 0); footer_layout.addWidget(self.cmb_payment, 0, 1); footer_layout.addWidget(self.lbl_grand_total, 0, 2, Qt.AlignmentFlag.AlignRight)
        footer_layout.addWidget(QLabel("Amount Paid:"), 1, 0); footer_layout.addWidget(self.spin_paid, 1, 1); footer_layout.addWidget(self.lbl_balance, 1, 2, Qt.AlignmentFlag.AlignRight)
        footer_layout.addWidget(self.btn_checkout, 2, 0, 1, 3)
        right_layout.addLayout(footer_layout)

        main_layout.addWidget(left_panel, 35)
        main_layout.addWidget(right_panel, 65)

    def refresh_cache(self):
        conn = database.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT Name FROM Customer")
            self.customer_names = [r[0] for r in cursor.fetchall() if r[0]]
            cursor.execute("SELECT Name FROM Doctor")
            self.doctor_names = [r[0] for r in cursor.fetchall() if r[0]]
            self.pat_completer.model().setStringList(self.customer_names)
            self.doc_completer.model().setStringList(self.doctor_names)
        finally: conn.close()

    def search_medicine(self, text):
        self.match_list.clear()
        conn = database.get_connection()
        cursor = conn.cursor()
        query = """SELECT d.med_name, s.batch_no, s.quantity, s.sale_rate, s.exp_date, 
                   d.rack_no, d.type, s.stock_id, d.med_id, d.gst, d.uses, d.tabs_per_strip
                   FROM Medicine_Details d JOIN Medicine_Stock s ON d.med_id = s.med_id
                   WHERE (d.med_name LIKE ? OR s.batch_no LIKE ?) AND s.quantity > 0 ORDER BY s.exp_date ASC"""
        st = f"%{text}%"; cursor.execute(query, (st, st)); rows = cursor.fetchall(); conn.close()
        
        today = datetime.date.today()
        for r in rows:
            name, batch, qty, rate, exp, rack, mtype, sid, mid, gst, uses, tps = r
            tps = int(tps) if tps else 1
            rate = float(rate or 0)
            
            # Expired check
            is_expired = False
            try:
                if "/" in exp: m, y = map(int, exp.split('/')); exp_dt = datetime.date(2000+y, m, 1)
                else: exp_dt = datetime.datetime.strptime(exp, "%Y-%m-%d").date()
                if (exp_dt - today).days < 0: is_expired = True
            except: pass

            disp_qty = f"{int(qty)//tps}s + {int(qty)%tps}l" if tps > 1 else str(qty)
            text_label = f"{name} | Batch: {batch} | Stock: {disp_qty}"
            
            item = QListWidgetItem(text_label)
            item.setData(Qt.ItemDataRole.UserRole, {
                "name": name, "batch": batch, "qty": qty, "unit_price": rate, 
                "exp": exp, "rack": rack, "stock_id": sid, "med_id": mid, 
                "gst": gst, "uses": uses, "tabs_per_strip": tps
            })
            
            if is_expired:
                item.setForeground(QBrush(QColor(COLOR_RED_BTN))); item.setText(text_label + " [EXPIRED]")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            else:
                item.setForeground(QBrush(QColor("black")))
            self.match_list.addItem(item)

    def select_medicine_from_list(self, item):
        self.load_preview(item.data(Qt.ItemDataRole.UserRole))

    def load_preview(self, data):
        self.current_selected_stock = data
        tps = data['tabs_per_strip']; up = data['unit_price']
        self.lbl_sel_name.setText(data['name'])
        
        if tps > 1:
            self.lbl_sel_info.setText(f"Batch: {data['batch']} | Rack: {data['rack']}\nPrice: ₹{up*tps:.2f}/Strip (₹{up:.2f}/Tab)")
            self.lbl_conversion.setText(f"1 Strip = {tps} Tablets"); self.spin_loose.setEnabled(True)
        else:
            self.lbl_sel_info.setText(f"Batch: {data['batch']} | Rack: {data['rack']}\nPrice: ₹{up:.2f}/Unit")
            self.lbl_conversion.setText("Unit Item"); self.spin_loose.setEnabled(False); self.spin_loose.setValue(0)
        
        self.lbl_sel_uses.setText(f"Uses: {data.get('uses', '-')}")
        self.spin_strips.setValue(0); self.spin_loose.setValue(0); self.spin_strips.setFocus(); self.spin_strips.selectAll()

    def add_to_cart(self):
        if not self.current_selected_stock: return
        data = self.current_selected_stock
        tps = data['tabs_per_strip']
        total_units = (self.spin_strips.value() * tps) + self.spin_loose.value()
        
        if total_units <= 0: QMessageBox.warning(self, "Invalid", "Enter quantity."); return
        if total_units > data['qty']: QMessageBox.warning(self, "Stock", f"Available: {data['qty']}"); return

        price = total_units * data['unit_price']
        disc = price * (self.spin_disc.value() / 100)
        
        qty_str = f"{self.spin_strips.value()}s + {self.spin_loose.value()}l" if tps > 1 else str(total_units)
        
        item = {
            "stock_id": data['stock_id'], "med_id": data['med_id'], "name": data['name'],
            "batch": data['batch'], "exp": data['exp'], "qty_total": total_units, "qty_disp": qty_str,
            "unit_rate": data['unit_price'], "strip_rate": data['unit_price'] * tps,
            "gst": data.get('gst', 0), "disc": disc, "total": price - disc, 
            "raw_data": data, "is_strip": tps > 1
        }
        
        # Check duplicate
        found = False
        for i, it in enumerate(self.cart_items):
            if it['stock_id'] == data['stock_id']: self.cart_items[i] = item; found = True; break
        if not found: self.cart_items.append(item)
        
        self.refresh_table()
        self.spin_strips.setValue(0); self.spin_loose.setValue(0); self.spin_strips.setFocus()

    def load_item_from_cart(self, r, c):
        if c != 8 and r < len(self.cart_items): self.load_preview(self.cart_items[r]['raw_data'])

    def delete_item(self, r):
        self.cart_items.pop(r); self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(0); total = 0
        for r, it in enumerate(self.cart_items):
            self.table.insertRow(r)
            rate = it['strip_rate'] if it['is_strip'] else it['unit_rate']
            
            def item(t): i = QTableWidgetItem(str(t)); i.setForeground(QBrush(QColor("black"))); return i
            
            self.table.setItem(r, 0, item(it['name'])); self.table.setItem(r, 1, item(it['batch']))
            self.table.setItem(r, 2, item(it['exp'])); self.table.setItem(r, 3, item(it['qty_disp']))
            self.table.setItem(r, 4, item(f"{rate:.2f}")); self.table.setItem(r, 5, item(f"{it['gst']}%"))
            self.table.setItem(r, 6, item(f"{it['disc']:.2f}")); self.table.setItem(r, 7, item(f"{it['total']:.2f}"))
            
            btn = QPushButton("X"); btn.setFixedSize(30, 25); btn.setStyleSheet(f"background:{COLOR_RED_BTN}; border:none; color:white;")
            btn.clicked.connect(lambda _, x=r: self.delete_item(x))
            self.table.setCellWidget(r, 8, btn)
            total += it['total']
            
        self.lbl_grand_total.setText(f"Total: ₹{total:.2f}")
        if self.spin_paid.value() == 0: self.spin_paid.setValue(total)
        else: self.calculate_balance()

    def calculate_balance(self):
        try: total = float(self.lbl_grand_total.text().replace("Total: ₹", ""))
        except: total = 0.0
        bal = total - self.spin_paid.value()
        if bal > 0.01: self.lbl_balance.setText(f"Balance: ₹{bal:.2f}")
        else: self.lbl_balance.setText(f"Change: ₹{abs(bal):.2f}")

    # --- EDIT MODE: Load Data ---
    def load_bill_data(self, bill_id):
        self.editing_bill_id = bill_id
        conn = database.get_connection(); cursor = conn.cursor()
        try:
            cursor.execute("SELECT patient_name, doctor_name, payment_method, paid_amount FROM Bill WHERE Bill_id=?", (bill_id,))
            head = cursor.fetchone()
            if not head: return
            
            self.inp_patient.setText(head[0]); self.inp_doctor.setText(head[1]); self.cmb_payment.setCurrentText(head[2])
            self.spin_paid.setValue(head[3] if head[3] else 0)
            
            cursor.execute("""SELECT bi.Med_id, bi.quantity, bi.total_price, m.med_name, m.gst, m.tabs_per_strip, m.rack_no
                              FROM Bill_Item bi JOIN Medicine_Details m ON bi.Med_id = m.med_id WHERE bi.Bill_id = ?""", (bill_id,))
            items = cursor.fetchall()
            
            self.cart_items = []
            for mid, qty, total, name, gst, tps, rack in items:
                cursor.execute("SELECT stock_id, batch_no, exp_date, quantity, sale_rate FROM Medicine_Stock WHERE med_id=? LIMIT 1", (mid,))
                stock = cursor.fetchone()
                if not stock: continue # Skip if stock definition gone
                
                sid, batch, exp, curr_qty, unit_rate = stock
                tps = int(tps) if tps else 1
                qty_disp = f"{int(qty)//tps}s + {int(qty)%tps}l" if tps > 1 else str(qty)
                
                # Reconstruct Item
                self.cart_items.append({
                    "stock_id": sid, "med_id": mid, "name": name, "batch": batch, "exp": exp,
                    "qty_total": qty, "qty_disp": qty_disp, "unit_rate": unit_rate,
                    "strip_rate": unit_rate * tps, "gst": gst, "disc": 0, "total": total,
                    "raw_data": {"stock_id": sid, "med_id": mid, "name": name, "batch": batch, "qty": curr_qty, 
                                 "unit_price": unit_rate, "exp": exp, "rack": rack, "tabs_per_strip": tps, "gst": gst},
                    "is_strip": tps > 1
                })
            self.refresh_table()
        finally: conn.close()

    def process_checkout(self):
        if not self.cart_items: return
        try: total = float(self.lbl_grand_total.text().replace("Total: ₹", ""))
        except: return
        
        paid = self.spin_paid.value(); credit = total - paid
        pat = self.inp_patient.text().strip() or "Walk-in"; doc = self.inp_doctor.text().strip()
        
        conn = database.get_connection(); cursor = conn.cursor()
        try:
            # --- RESTORE STOCK IF EDITING ---
            if self.editing_bill_id:
                # 1. Restore old quantities
                cursor.execute("SELECT Med_id, quantity FROM Bill_Item WHERE Bill_id=?", (self.editing_bill_id,))
                old_items = cursor.fetchall()
                for mid, qty in old_items:
                    cursor.execute("UPDATE Medicine_Stock SET quantity = quantity + ? WHERE med_id=?", (qty, mid)) # Simplified restoration
                
                # 2. Adjust Customer Balance (Reverse old credit)
                cursor.execute("SELECT balance, total_sum, paid_amount FROM Bill WHERE Bill_id=?", (self.editing_bill_id,))
                old_bill = cursor.fetchone()
                if old_bill:
                    old_credit = (old_bill[1] or 0) - (old_bill[2] or 0)
                    if old_credit > 0:
                        cursor.execute("UPDATE Customer SET balance = balance - ? WHERE Name = ?", (old_credit, pat))

                # 3. Delete Old Bill
                cursor.execute("DELETE FROM Bill_Item WHERE Bill_id=?", (self.editing_bill_id,))
                cursor.execute("DELETE FROM Bill WHERE Bill_id=?", (self.editing_bill_id,))

            # --- SAVE NEW BILL ---
            cursor.execute("INSERT INTO Bill (patient_name, doctor_name, payment_method, total_sum, paid_amount, balance, bill_date) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))", 
                           (pat, doc, self.cmb_payment.currentText(), total, paid, credit))
            bid = cursor.lastrowid
            
            for it in self.cart_items:
                cursor.execute("INSERT INTO Bill_Item (Bill_id, Med_id, quantity, unit_price, total_price) VALUES (?, ?, ?, ?, ?)", 
                               (bid, it['med_id'], it['qty_total'], it['unit_rate'], it['total']))
                cursor.execute("UPDATE Medicine_Stock SET quantity = quantity - ? WHERE stock_id=?", (it['qty_total'], it['stock_id']))
            
            if credit > 0.01 and pat != "Walk-in":
                cursor.execute("SELECT Cust_id FROM Customer WHERE Name=?", (pat,))
                cid = cursor.fetchone()
                if cid: cursor.execute("UPDATE Customer SET balance = balance + ? WHERE Cust_id=?", (credit, cid[0]))
                else: cursor.execute("INSERT INTO Customer (Name, balance) VALUES (?, ?)", (pat, credit))
            
            conn.commit()
            
            if QMessageBox.question(self, "Saved", f"Bill #{bid} Saved! Print Receipt?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                self.print_receipt(bid, pat, doc, total, paid, credit)
            
            self.cart_items = []; self.refresh_table(); self.inp_patient.clear(); self.inp_doctor.clear()
            self.spin_paid.setValue(0); self.editing_bill_id = None # Reset edit mode

        except Exception as e: conn.rollback(); QMessageBox.critical(self, "Error", str(e))
        finally: conn.close()

    def print_receipt(self, bid, pat, doc, total, paid, bal):
        conn = database.get_connection(); cur = conn.cursor()
        cur.execute("SELECT p_name, phone, email, location, GSTIN FROM Pharmacy LIMIT 1")
        ph = cur.fetchone(); conn.close()
        
        shop = ph[0] if ph else "PHARMACY"; addr = ph[3] if ph else ""; contact = f"Ph: {ph[1]}" if ph else ""
        gstin = f"<br>GSTIN: {ph[4]}" if ph and ph[4] else ""
        
        html = f"""<div style='font-family: Arial; font-size: 12px; color:black;'>
        <center><h2>{shop}</h2><p>{addr}<br>{contact}{gstin}</p></center><hr>
        <table width='100%'><tr><td>Bill: {bid}</td><td align='right'>Date: {datetime.datetime.now().strftime('%d/%m/%y')}</td></tr>
        <tr><td>Pat: {pat}</td><td align='right'>Doc: {doc}</td></tr></table><hr>
        <table width='100%' cellspacing='0' cellpadding='3'>
        <tr style='border-bottom:1px solid black;'><td><b>Item</b></td><td><b>Exp</b></td><td><b>Qty</b></td><td><b>GST</b></td><td align='right'><b>Total</b></td></tr>"""
        
        for i in self.cart_items:
            html += f"<tr><td>{i['name']}</td><td>{i['exp']}</td><td>{i['qty_disp']}</td><td>{i['gst']}%</td><td align='right'>{i['total']:.2f}</td></tr>"
        
        html += f"</table><hr><table width='100%'><tr><td align='right'><b>Total: ₹{total:.2f}</b></td></tr>"
        html += f"<tr><td align='right'>Paid: ₹{paid:.2f}</td></tr>"
        if bal > 0: html += f"<tr><td align='right'><b>Due: ₹{bal:.2f}</b></td></tr>"
        html += "</table><br><center>Thank You!</center></div>"
        
        printer = QPrinter(); doc = QTextDocument(); doc.setHtml(html)
        if QPrintDialog(printer, self).exec(): doc.print(printer)

class BillingInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Billing & POS")
        self.setStyleSheet(GLOBAL_STYLE)
        
        self.layout = QVBoxLayout(self); self.layout.setContentsMargins(0,0,0,0)
        self.top_bar = QHBoxLayout()
        self.btn_new = QPushButton("+ New Bill Tab"); self.btn_new.setFixedSize(120, 35)
        self.btn_new.clicked.connect(self.add_new_tab)
        self.btn_new.setStyleSheet(f"background-color: {COLOR_NAVBAR}; border-radius: 5px; font-weight: bold;")
        self.top_bar.addStretch(); self.top_bar.addWidget(self.btn_new); self.top_bar.setContentsMargins(10,5,10,0)
        
        self.tabs = QTabWidget(); self.tabs.setTabsClosable(True); self.tabs.tabCloseRequested.connect(self.close_tab)
        self.layout.addLayout(self.top_bar); self.layout.addWidget(self.tabs)
        self.add_new_tab()

    def add_new_tab(self):
        t = SingleBillTab(); self.tabs.addTab(t, f"Bill {self.tabs.count()+1}"); self.tabs.setCurrentWidget(t)
    
    def close_tab(self, i): 
        if self.tabs.count() > 1: self.tabs.removeTab(i)
    
    def refresh_cache(self):
        if self.tabs.currentWidget(): self.tabs.currentWidget().refresh_cache()

    def load_bill_for_editing(self, bid):
        self.add_new_tab()
        self.tabs.currentWidget().load_bill_data(bid)
        self.tabs.setTabText(self.tabs.currentIndex(), f"Edit #{bid}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BillingInterface()
    window.showMaximized()
    sys.exit(app.exec())