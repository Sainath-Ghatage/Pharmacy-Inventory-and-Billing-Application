import sys
import datetime
import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDateEdit, QMessageBox, QDialog, QFormLayout,
    QFrame, QAbstractItemView, QCompleter, QSpinBox, QDoubleSpinBox,
    QGridLayout, QTabWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont, QIcon

import database

# --- COLORS ---
COLOR_BG = "#ffffff"            
COLOR_INPUT_BG = "#ffffff"      
COLOR_HEADER_BG = "#f1f3f4"     
COLOR_BORDER = "#dadce0"        
COLOR_TEXT = "#202124"          
COLOR_NAVBAR = "#1a73e8"        
COLOR_GREEN = "#1e8e3e"         
COLOR_DELETE = "#d93025"        
COLOR_SELECTION = "#e8f0fe"     

# --- STYLESHEET ---
STYLE_SHEET = f"""
    QWidget {{
        background-color: {COLOR_BG};
        color: {COLOR_TEXT};
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        font-size: 13px;
    }}

    /* Inputs */
    QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {{
        background-color: {COLOR_INPUT_BG};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        padding: 8px;
        min-height: 20px;
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus {{
        border: 2px solid {COLOR_NAVBAR};
        background-color: #fff;
    }}

    /* Table */
    QTableWidget {{
        background-color: #ffffff;
        color: {COLOR_TEXT};
        gridline-color: {COLOR_BORDER};
        border: 1px solid {COLOR_BORDER};
        selection-background-color: {COLOR_SELECTION};
        selection-color: {COLOR_NAVBAR};
        outline: none;
    }}
    
    QHeaderView::section {{
        background-color: {COLOR_HEADER_BG};
        color: #5f6368;
        padding: 8px;
        border: 1px solid {COLOR_BORDER};
        font-weight: 700;
        font-size: 12px;
        text-transform: uppercase;
    }}

    /* Tabs */
    QTabWidget::pane {{ border: 1px solid {COLOR_BORDER}; }}
    QTabBar::tab {{
        background: #f1f3f4;
        color: #5f6368;
        padding: 10px 20px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    QTabBar::tab:selected {{
        background: {COLOR_NAVBAR};
        color: white;
        font-weight: bold;
    }}

    /* Buttons */
    QPushButton {{
        background-color: #f8f9fa;
        border: 1px solid {COLOR_BORDER};
        color: {COLOR_TEXT};
        border-radius: 4px;
        padding: 6px 16px;
        font-weight: 600;
    }}
    QPushButton:hover {{ background-color: #f1f3f4; }}
"""

# --- QUICK ADD DIALOG ---
class QuickAddMedicineDialog(QDialog):
    def __init__(self, partial_name="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Add Product")
        self.setFixedSize(450, 400)
        self.setStyleSheet(STYLE_SHEET)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.inp_name = QLineEdit(partial_name)
        self.inp_type = QComboBox()
        # Updated Categories
        types = [
            "Tablet", "Capsule", "Syrup", "Injection", "Cream", 
            "Ointment", "Drops", "Personal Care & Wellness", 
            "Spray", "Powder", "Medical Devices"
        ]
        self.inp_type.addItems(types)
        
        self.inp_rack = QLineEdit()
        self.inp_hsn = QLineEdit()
        
        self.inp_gst = QDoubleSpinBox()
        self.inp_gst.setRange(0, 100)
        self.inp_gst.setValue(12.0)
        
        self.inp_tabs = QSpinBox()
        self.inp_tabs.setRange(1, 1000)
        self.inp_tabs.setValue(1) 
        self.inp_tabs.setSuffix(" units")
        
        form.addRow("Product Name:", self.inp_name)
        form.addRow("Category:", self.inp_type)
        form.addRow("Rack/Shelf:", self.inp_rack)
        form.addRow("HSN Code:", self.inp_hsn)
        form.addRow("GST %:", self.inp_gst)
        form.addRow("Pack Size (Tabs/Qty):", self.inp_tabs)
        
        layout.addLayout(form)
        
        btn_box = QHBoxLayout()
        btn_save = QPushButton("Save & Use")
        btn_save.clicked.connect(self.save_medicine)
        btn_save.setStyleSheet(f"background-color: {COLOR_GREEN}; color: white; border: none;")
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)
        
        self.new_med_id = None
        self.new_med_data = None

    def save_medicine(self):
        name = self.inp_name.text().strip()
        if not name: return
        
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO Medicine (Med_name, Type, rack_no, hsn_code, gst_rate, tabs_per_strip, Quantity, Purchase_Price, Sale_Price)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0)
            """, (name, self.inp_type.currentText(), self.inp_rack.text(), self.inp_hsn.text(), self.inp_gst.value(), self.inp_tabs.value()))
            self.new_med_id = cur.lastrowid
            conn.commit()
            
            self.new_med_data = {
                "id": self.new_med_id, "name": name, "type": self.inp_type.currentText(),
                "rack": self.inp_rack.text(), "hsn": self.inp_hsn.text(),
                "gst": self.inp_gst.value()
            }
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()

class PurchaseEntryInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Purchase Entry")
        self.setStyleSheet(STYLE_SHEET)
        
        self.init_ui()
        self.load_suppliers()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Title
        lbl_title = QLabel("Purchase Management")
        lbl_title.setStyleSheet(f"font-size: 24px; font-weight: 600; color: {COLOR_NAVBAR}; margin-bottom: 15px;")
        main_layout.addWidget(lbl_title)

        # TABS
        self.tabs = QTabWidget()
        self.tab_entry = QWidget()
        self.tab_history = QWidget()
        
        self.tabs.addTab(self.tab_entry, "New Invoice Entry")
        self.tabs.addTab(self.tab_history, "Invoice History")
        
        # Setup Tabs
        self.create_entry_tab()
        self.create_history_tab()
        
        # Refresh history when tab clicked
        self.tabs.currentChanged.connect(self.on_tab_changed)

        main_layout.addWidget(self.tabs)

    # -----------------------------------------------------------
    # TAB 1: NEW ENTRY
    # -----------------------------------------------------------
    def create_entry_tab(self):
        layout = QVBoxLayout(self.tab_entry)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # 1. HEADER INPUTS
        input_container = QFrame()
        input_container.setStyleSheet(f"background-color: #fff; border: 1px solid {COLOR_BORDER}; border-radius: 6px;")
        grid_layout = QGridLayout(input_container)
        grid_layout.setContentsMargins(15, 15, 15, 15)
        grid_layout.setSpacing(15)

        def add_field(label_text, widget, row, col, colspan=1):
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #5f6368;")
            container = QWidget()
            vbox = QVBoxLayout(container)
            vbox.setContentsMargins(0,0,0,0)
            vbox.setSpacing(4)
            vbox.addWidget(lbl)
            vbox.addWidget(widget)
            grid_layout.addWidget(container, row, col, 1, colspan)

        self.inp_inv_no = QLineEdit()
        self.inp_inv_no.setPlaceholderText("Invoice No")
        add_field("Invoice No *", self.inp_inv_no, 0, 0)

        self.cmb_supplier = QComboBox()
        self.cmb_supplier.setEditable(True)
        add_field("Supplier *", self.cmb_supplier, 0, 1)

        self.date_inv = QDateEdit(QDate.currentDate())
        self.date_inv.setCalendarPopup(True)
        add_field("Invoice Date *", self.date_inv, 0, 2)

        self.inp_remarks = QLineEdit()
        self.inp_remarks.setPlaceholderText("Optional notes...")
        add_field("Remarks", self.inp_remarks, 0, 3)

        layout.addWidget(input_container)

        # 2. TABLE
        self.table = QTableWidget()
        self.table.setColumnCount(11) 
        
        headers = [
            "Medicine Name", "Batch No", "Mfg Date\n(MM/YY)", "Exp Date\n(MM/YY)", 
            "Bill Qty", "Free Qty", "Buy Rate\n(Incl Tax)", "MRP", "GST %", "Line Total", "Action"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("alternate-background-color: #fafafa;")
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setDefaultSectionSize(90)
        header.setFixedHeight(40)
        
        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setDefaultSectionSize(40)
        
        # Add 1 initial row
        self.table.setRowCount(0)
        self.add_row()
        
        self.table.cellChanged.connect(self.on_cell_changed)
        layout.addWidget(self.table)

        # 3. ROW ACTIONS
        row_btns = QHBoxLayout()
        btn_add = QPushButton("+ Add Item")
        btn_add.clicked.connect(self.add_row)
        btn_add.setStyleSheet(f"color: {COLOR_NAVBAR}; border: 1px dashed {COLOR_NAVBAR}; background: #f0f8ff;")
        row_btns.addWidget(btn_add)
        row_btns.addStretch()
        layout.addLayout(row_btns)

        # 4. FOOTER (Payment & Save)
        footer = QFrame()
        footer.setStyleSheet(f"background-color: #fff; border: 1px solid {COLOR_BORDER}; border-radius: 6px;")
        foot_lay = QHBoxLayout(footer)
        foot_lay.setContentsMargins(15, 10, 15, 10)
        foot_lay.setSpacing(20)

        # Clear
        btn_clear = QPushButton("Reset")
        btn_clear.clicked.connect(self.clear_form)
        btn_clear.setStyleSheet(f"color: #666; border: 1px solid #ccc;")
        foot_lay.addWidget(btn_clear)

        foot_lay.addStretch()

        # Payment Logic
        lbl_pay_mode = QLabel("Payment:")
        self.cmb_pay_mode = QComboBox()
        self.cmb_pay_mode.addItems(["Credit", "Cash", "UPI", "Cheque", "Net Banking"])
        self.cmb_pay_mode.setFixedWidth(100)

        lbl_paid = QLabel("Paid Amount:")
        self.inp_paid = QDoubleSpinBox()
        self.inp_paid.setRange(0, 9999999)
        self.inp_paid.setPrefix("₹ ")
        self.inp_paid.setFixedWidth(120)
        self.inp_paid.valueChanged.connect(self.calculate_balance)

        lbl_bal = QLabel("Balance:")
        self.inp_balance = QLineEdit("₹ 0.00")
        self.inp_balance.setReadOnly(True)
        self.inp_balance.setFixedWidth(120)
        self.inp_balance.setStyleSheet(f"background-color: #f1f3f4; color: {COLOR_DELETE}; font-weight: bold;")

        foot_lay.addWidget(lbl_pay_mode)
        foot_lay.addWidget(self.cmb_pay_mode)
        foot_lay.addWidget(lbl_paid)
        foot_lay.addWidget(self.inp_paid)
        foot_lay.addWidget(lbl_bal)
        foot_lay.addWidget(self.inp_balance)

        # Grand Total
        self.lbl_grand_total = QLabel("Total: ₹0.00")
        self.lbl_grand_total.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_NAVBAR}; margin-left: 10px; margin-right: 10px;")
        foot_lay.addWidget(self.lbl_grand_total)

        # Save
        btn_save = QPushButton("Save Entry")
        btn_save.setFixedSize(140, 40)
        btn_save.setStyleSheet(f"background-color: {COLOR_GREEN}; color: white; border: none; font-size: 14px; border-radius: 4px;")
        btn_save.clicked.connect(self.save_invoice)
        foot_lay.addWidget(btn_save)

        layout.addWidget(footer)

    # -----------------------------------------------------------
    # TAB 2: HISTORY
    # -----------------------------------------------------------
    def create_history_tab(self):
        layout = QVBoxLayout(self.tab_history)
        
        # Search Bar for history
        h_bar = QHBoxLayout()
        self.hist_search = QLineEdit()
        self.hist_search.setPlaceholderText("Search Invoice No or Supplier...")
        self.hist_search.textChanged.connect(self.load_history)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.load_history)
        
        h_bar.addWidget(self.hist_search)
        h_bar.addWidget(btn_refresh)
        layout.addLayout(h_bar)

        # Table
        self.hist_table = QTableWidget()
        self.hist_table.setColumnCount(7)
        self.hist_table.setHorizontalHeaderLabels(["ID", "Invoice No", "Supplier", "Date", "Total Amt", "Paid", "Actions"])
        self.hist_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.hist_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.hist_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.hist_table)

    def on_tab_changed(self, index):
        if index == 1: # History tab
            self.load_history()

    def load_history(self):
        conn = database.get_connection()
        cur = conn.cursor()
        query_txt = self.hist_search.text().strip()
        
        sql = """
            SELECT p.invoice_id, p.invoice_number, s.Sup_name, p.invoice_date, p.total_amount, p.paid_amount
            FROM Purchase_Invoice p
            LEFT JOIN Supplier s ON p.supp_id = s.Supp_id
        """
        if query_txt:
            sql += f" WHERE p.invoice_number LIKE '%{query_txt}%' OR s.Sup_name LIKE '%{query_txt}%'"
        
        sql += " ORDER BY p.invoice_id DESC"
        
        cur.execute(sql)
        rows = cur.fetchall()
        conn.close()
        
        self.hist_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.hist_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.hist_table.setItem(i, 1, QTableWidgetItem(str(row[1])))
            self.hist_table.setItem(i, 2, QTableWidgetItem(str(row[2])))
            self.hist_table.setItem(i, 3, QTableWidgetItem(str(row[3])))
            self.hist_table.setItem(i, 4, QTableWidgetItem(f"₹{row[4]:.2f}"))
            self.hist_table.setItem(i, 5, QTableWidgetItem(f"₹{row[5]:.2f}"))
            
            # Action (View Details placeholder)
            btn_view = QPushButton("View")
            btn_view.setFixedSize(60, 25)
            # You can connect this to a detail dialog later
            self.hist_table.setCellWidget(i, 6, btn_view)

    # -----------------------------------------------------------
    # LOGIC
    # -----------------------------------------------------------
    def add_row(self):
        rc = self.table.rowCount()
        self.table.insertRow(rc)
        
        # Add Delete Button in last column
        btn_del = QPushButton("X")
        btn_del.setFixedSize(30, 25)
        btn_del.setStyleSheet(f"color: white; background-color: {COLOR_DELETE}; border: none; border-radius: 3px;")
        btn_del.clicked.connect(lambda: self.remove_specific_row(btn_del))
        
        # Center the button
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0,0,0,0)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(btn_del)
        self.table.setCellWidget(rc, 10, w)

    def remove_specific_row(self, btn):
        # Find the row containing this button
        for r in range(self.table.rowCount()):
            widget = self.table.cellWidget(r, 10)
            if widget:
                # Get the button inside the layout
                layout = widget.layout()
                if layout.itemAt(0).widget() == btn:
                    self.table.removeRow(r)
                    self.update_grand_total()
                    return

    def load_suppliers(self):
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT Sup_name, Supp_id FROM Supplier")
            self.suppliers = cur.fetchall()
            self.cmb_supplier.clear()
            self.cmb_supplier.addItem("-- Select Supplier --", None)
            for name, sid in self.suppliers:
                self.cmb_supplier.addItem(name, sid)
        except: pass
        finally: conn.close()

    def on_cell_changed(self, row, col):
        self.table.blockSignals(True)
        try:
            # 1. Name Entry (Col 0)
            if col == 0:
                item = self.table.item(row, 0)
                if item and item.text():
                    name = item.text()
                    data = self.fetch_med_data(name)
                    if data:
                        # Auto-fill GST (Col 8)
                        if not self.table.item(row, 8):
                            self.table.setItem(row, 8, QTableWidgetItem(str(data['gst'])))
                        item.setData(Qt.ItemDataRole.UserRole, data['id'])
                    else:
                        ret = QMessageBox.question(self, "New Product", f"'{name}' not found.\nAdd it to database?", 
                                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                        if ret == QMessageBox.StandardButton.Yes:
                            dlg = QuickAddMedicineDialog(name, self)
                            if dlg.exec():
                                self.table.setItem(row, 8, QTableWidgetItem(str(dlg.new_med_data['gst'])))
                                item.setData(Qt.ItemDataRole.UserRole, dlg.new_med_data['id'])
            
            # 2. Calculation (Qty=4, Rate=6) -> Total=9
            if col in [4, 6]:
                try:
                    qty = float(self.table.item(row, 4).text()) if self.table.item(row, 4) else 0
                    rate = float(self.table.item(row, 6).text()) if self.table.item(row, 6) else 0
                    total = qty * rate
                    self.table.setItem(row, 9, QTableWidgetItem(f"{total:.2f}"))
                    self.update_grand_total()
                except: pass

        except Exception as e:
            print(f"Grid Error: {e}")
        finally:
            self.table.blockSignals(False)

    def fetch_med_data(self, name):
        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT Med_id, gst_rate FROM Medicine WHERE Med_name = ? LIMIT 1", (name,))
        row = cur.fetchone()
        conn.close()
        if row: return {"id": row[0], "gst": row[1]}
        return None

    def update_grand_total(self):
        g_total = 0
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 9)
            if item:
                try: g_total += float(item.text())
                except: pass
        
        self.lbl_grand_total.setText(f"Total: ₹{g_total:.2f}")
        self.calculate_balance()

    def calculate_balance(self):
        try:
            total_text = self.lbl_grand_total.text().replace("Total: ₹", "")
            total = float(total_text) if total_text else 0.0
            paid = self.inp_paid.value()
            balance = total - paid
            self.inp_balance.setText(f"₹ {balance:.2f}")
        except:
            self.inp_balance.setText("₹ 0.00")

    def clear_form(self):
        self.inp_inv_no.clear()
        self.cmb_supplier.setCurrentIndex(0)
        self.table.setRowCount(0)
        self.add_row()
        self.lbl_grand_total.setText("Total: ₹0.00")
        self.inp_paid.setValue(0)
        self.inp_balance.setText("₹ 0.00")

    def save_invoice(self):
        # Validation
        if self.cmb_supplier.currentIndex() <= 0:
            QMessageBox.warning(self, "Error", "Select a Supplier.")
            return
        if not self.inp_inv_no.text().strip():
            QMessageBox.warning(self, "Error", "Invoice Number required.")
            return

        # Prepare Header Data
        inv_no = self.inp_inv_no.text().strip()
        supp_id = self.cmb_supplier.currentData()
        date = self.date_inv.date().toString("yyyy-MM-dd")
        pay_mode = self.cmb_pay_mode.currentText()
        paid_amt = self.inp_paid.value()
        
        try:
            total_val = float(self.lbl_grand_total.text().replace("Total: ₹", ""))
        except: total_val = 0
        
        balance_amt = total_val - paid_amt

        rows_to_save = []
        
        # Scrape Table
        for r in range(self.table.rowCount()):
            name_item = self.table.item(r, 0)
            if not name_item or not name_item.text(): continue
            
            med_id = name_item.data(Qt.ItemDataRole.UserRole)
            # If creating a new batch, we might treat it as a new stock entry
            # But we need the Med_ID to link general info.
            if not med_id:
                # If user typed a name but didn't trigger the logic, fetch or create now
                # Simplified: fail if not valid
                QMessageBox.warning(self, "Error", f"Row {r+1}: Please press Enter on the Name field to register the product.")
                return

            try:
                # Col Map: 0:Name, 1:Batch, 2:Mfg, 3:Exp, 4:Qty, 5:Free, 6:Rate, 7:MRP, 8:GST, 9:Total
                batch = self.table.item(r, 1).text().strip() if self.table.item(r, 1) else ""
                mfg = self.table.item(r, 2).text().strip() if self.table.item(r, 2) else ""
                exp = self.table.item(r, 3).text().strip() if self.table.item(r, 3) else ""
                qty = float(self.table.item(r, 4).text() or 0)
                free = float(self.table.item(r, 5).text() or 0)
                rate_incl = float(self.table.item(r, 6).text() or 0)
                mrp = float(self.table.item(r, 7).text() or 0)
                gst_pct = float(self.table.item(r, 8).text() or 0)
                
                # Check required fields
                if not batch or not exp:
                    QMessageBox.warning(self, "Error", f"Row {r+1}: Batch and Expiry are required.")
                    return

                # Calculations
                base_rate = rate_incl / (1 + (gst_pct/100))
                tax_amt_unit = rate_incl - base_rate
                total_line = rate_incl * qty
                
                rows_to_save.append({
                    "med_id": med_id, "name": name_item.text(), 
                    "batch": batch, "mfg": mfg, "exp": exp,
                    "qty": qty, "free": free, "rate": rate_incl,
                    "mrp": mrp, "gst": gst_pct, "tax_amt": tax_amt_unit * qty,
                    "total": total_line
                })
            except ValueError:
                QMessageBox.warning(self, "Error", f"Row {r+1}: Invalid numbers.")
                return

        if not rows_to_save:
            QMessageBox.warning(self, "Error", "No items to save.")
            return

        # DATABASE COMMIT
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            # 1. Insert Invoice Header
            cur.execute("""
                INSERT INTO Purchase_Invoice (invoice_number, supp_id, invoice_date, payment_mode, total_amount, paid_amount, balance, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (inv_no, supp_id, date, pay_mode, total_val, paid_amt, balance_amt))
            inv_id = cur.lastrowid
            
            # 2. Insert Items & STOCK LOGIC
            for row in rows_to_save:
                cur.execute("""
                    INSERT INTO Purchase_Invoice_Item 
                    (invoice_id, Med_id, batch_no, expiry_date, quantity, free_qty, purchase_rate_incl, tax_rate, tax_amount, mrp, total_amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (inv_id, row['med_id'], row['batch'], row['exp'], row['qty'], row['free'], row['rate'], row['gst'], row['tax_amt'], row['mrp'], row['total']))
                
                # STOCK LOGIC: Differentiate by Name + Batch + Expiry
                # First, check if this specific batch exists
                cur.execute("""
                    SELECT Med_id FROM Medicine 
                    WHERE Med_name = ? AND batch_no = ? AND EXP_Date = ?
                """, (row['name'], row['batch'], row['exp']))
                
                existing = cur.fetchone()
                total_qty = row['qty'] + row['free']
                
                if existing:
                    # Update existing batch
                    cur.execute("""
                        UPDATE Medicine 
                        SET Quantity = Quantity + ?, Purchase_Price = ?, Sale_Price = ?
                        WHERE Med_id = ?
                    """, (total_qty, row['rate'], row['mrp'], existing[0]))
                else:
                    # Create NEW stock entry for this batch
                    # Get generic details from base ID
                    cur.execute("SELECT Type, hsn_code, rack_no, tabs_per_strip, gst_rate FROM Medicine WHERE Med_id = ?", (row['med_id'],))
                    base_info = cur.fetchone()
                    
                    cur.execute("""
                        INSERT INTO Medicine (Med_name, batch_no, MFG_Date, EXP_Date, Quantity, Purchase_Price, Sale_Price, 
                                              Type, hsn_code, rack_no, tabs_per_strip, gst_rate)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (row['name'], row['batch'], row['mfg'], row['exp'], total_qty, row['rate'], row['mrp'],
                          base_info[0], base_info[1], base_info[2], base_info[3], row['gst']))

            conn.commit()
            QMessageBox.information(self, "Success", "Invoice Saved & Stock Updated!")
            self.clear_form()
            
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Database Error", str(e))
        finally:
            conn.close()