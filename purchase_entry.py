import sys
import datetime
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDateEdit, QMessageBox, QDialog, QFormLayout,
    QFrame, QAbstractItemView, QCompleter, QSpinBox, QDoubleSpinBox,
    QGridLayout, QTabWidget, QSplitter
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont, QIcon

import database

# --- COLORS ---
COLOR_BG = "#f8f9fa"            
COLOR_PANEL = "#ffffff"
COLOR_BORDER = "#dee2e6"        
COLOR_TEXT = "#212529"          
COLOR_NAVBAR = "#0d47a1"        
COLOR_GREEN = "#198754"         
COLOR_DELETE = "#dc3545"        
COLOR_ACCENT_LIGHT = "#e7f1ff"     

# --- STYLESHEET ---
STYLE_SHEET = f"""
    QWidget {{
        background-color: {COLOR_BG};
        color: {COLOR_TEXT};
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 13px;
    }}
    
    /* Inputs */
    QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {{
        background-color: {COLOR_PANEL};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        border-radius: 6px;
        padding: 8px 10px;
        font-size: 14px;
        min-height: 25px;
    }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
        border: 2px solid {COLOR_NAVBAR};
    }}

    /* Table */
    QTableWidget {{
        background-color: {COLOR_PANEL};
        color: {COLOR_TEXT};
        gridline-color: {COLOR_BORDER};
        border: 1px solid {COLOR_BORDER};
        border-radius: 6px;
        outline: none;
    }}
    QTableWidget::item {{
        padding-left: 5px;
    }}
    QTableWidget::item:selected {{
        background-color: {COLOR_ACCENT_LIGHT};
        color: {COLOR_NAVBAR};
        border-bottom: 2px solid {COLOR_NAVBAR};
    }}
    QHeaderView::section {{
        background-color: #e9ecef;
        color: #495057;
        padding: 10px;
        border: none;
        border-bottom: 2px solid {COLOR_BORDER};
        border-right: 1px solid {COLOR_BORDER};
        font-weight: bold;
        font-size: 13px;
    }}

    /* Buttons */
    QPushButton {{
        background-color: {COLOR_PANEL};
        border: 1px solid {COLOR_BORDER};
        color: {COLOR_TEXT};
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
        min-height: 20px;
    }}
    QPushButton:hover {{ background-color: #e2e6ea; }}
"""

class PurchaseEntryInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Purchase Entry")
        self.setStyleSheet(STYLE_SHEET)
        
        self.med_names = [] 
        self.load_medicine_names()
        
        self.init_ui()
        self.load_suppliers()

    def load_medicine_names(self):
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT med_name FROM Medicine_Details")
            self.med_names = [row[0] for row in cur.fetchall()]
        except: pass
        finally: conn.close()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        lbl_title = QLabel("Purchase Management")
        lbl_title.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {COLOR_NAVBAR};")
        main_layout.addWidget(lbl_title)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {COLOR_BORDER}; background: {COLOR_PANEL}; border-radius: 6px; }}
            QTabBar::tab {{
                background: #e9ecef;
                color: #495057;
                padding: 12px 25px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {COLOR_PANEL};
                color: {COLOR_NAVBAR};
                border-top: 3px solid {COLOR_NAVBAR};
            }}
        """)
        
        self.tab_entry = QWidget()
        self.tab_history = QWidget()
        
        self.tabs.addTab(self.tab_entry, "New Invoice Entry")
        self.tabs.addTab(self.tab_history, "Invoice History")
        
        self.create_entry_tab()
        self.create_history_tab()
        
        self.tabs.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tabs)

    # -----------------------------------------------------------
    # TAB 1: NEW ENTRY
    # -----------------------------------------------------------
    def create_entry_tab(self):
        layout = QVBoxLayout(self.tab_entry)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. HEADER INPUTS (Styled Card)
        input_container = QFrame()
        input_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_PANEL}; 
                border: 1px solid {COLOR_BORDER}; 
                border-radius: 8px;
            }}
        """)
        grid_layout = QGridLayout(input_container)
        grid_layout.setContentsMargins(20, 20, 20, 20)
        grid_layout.setSpacing(20)

        def add_field(label_text, widget, row, col, colspan=1):
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #6c757d; text-transform: uppercase;")
            container = QWidget()
            vbox = QVBoxLayout(container)
            vbox.setContentsMargins(0,0,0,0)
            vbox.setSpacing(5)
            vbox.addWidget(lbl)
            vbox.addWidget(widget)
            grid_layout.addWidget(container, row, col, 1, colspan)

        self.inp_inv_no = QLineEdit()
        self.inp_inv_no.setPlaceholderText("e.g. INV-2026-001")
        add_field("Invoice No *", self.inp_inv_no, 0, 0)

        self.cmb_supplier = QComboBox()
        self.cmb_supplier.setEditable(True)
        add_field("Supplier *", self.cmb_supplier, 0, 1)

        self.date_inv = QDateEdit(QDate.currentDate())
        self.date_inv.setCalendarPopup(True)
        add_field("Invoice Date *", self.date_inv, 0, 2)

        layout.addWidget(input_container)

        # 2. TABLE
        self.table = QTableWidget()
        self.table.setColumnCount(9) 
        
        # Updated Headers to be Explicit
        headers = [
            "Medicine Name", "Batch No", "Mfg Date\n(MM/YY)", "Exp Date\n(MM/YY)", 
            "Qty (Strips)", "Buy Rate\n(Per Strip)", "MRP\n(Per Strip)", "Line Total", "Action"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        
        # --- ENABLE SCROLLING ---
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False) 
        
        # Set Specific Widths
        self.table.setColumnWidth(0, 300) # Medicine Name
        self.table.setColumnWidth(1, 150) # Batch
        self.table.setColumnWidth(2, 110) # Mfg
        self.table.setColumnWidth(3, 110) # Exp
        self.table.setColumnWidth(4, 100) # Qty
        self.table.setColumnWidth(5, 120) # Buy Rate
        self.table.setColumnWidth(6, 120) # MRP
        self.table.setColumnWidth(7, 120) # Total
        self.table.setColumnWidth(8, 80)  # Action
        
        # Row Height
        self.table.verticalHeader().setDefaultSectionSize(50) 

        self.table.setRowCount(0)
        self.add_row()
        self.table.cellChanged.connect(self.on_cell_changed)
        layout.addWidget(self.table)

        # 3. ROW ACTIONS
        row_btns = QHBoxLayout()
        btn_add = QPushButton("+ Add New Row")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self.add_row)
        btn_add.setStyleSheet(f"""
            color: {COLOR_NAVBAR}; 
            border: 1px dashed {COLOR_NAVBAR}; 
            background: #f0f8ff; 
            font-weight: bold;
        """)
        row_btns.addWidget(btn_add)
        row_btns.addStretch()
        layout.addLayout(row_btns)

        # 4. FOOTER
        footer = QFrame()
        footer.setStyleSheet(f"background-color: {COLOR_PANEL}; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")
        foot_lay = QHBoxLayout(footer)
        foot_lay.setContentsMargins(20, 15, 20, 15)
        foot_lay.setSpacing(20)

        btn_clear = QPushButton("Clear Form")
        btn_clear.clicked.connect(self.clear_form)
        btn_clear.setStyleSheet("color: #dc3545; border-color: #dc3545;")
        foot_lay.addWidget(btn_clear)
        foot_lay.addStretch()

        lbl_pay_mode = QLabel("Payment:")
        lbl_pay_mode.setStyleSheet("font-weight: bold;")
        self.cmb_pay_mode = QComboBox()
        self.cmb_pay_mode.addItems(["Credit", "Cash", "UPI", "Cheque"])
        self.cmb_pay_mode.setFixedWidth(120)

        lbl_paid = QLabel("Paid Amount:")
        lbl_paid.setStyleSheet("font-weight: bold;")
        self.inp_paid = QDoubleSpinBox()
        self.inp_paid.setRange(0, 9999999)
        self.inp_paid.setPrefix("₹ ")
        self.inp_paid.setFixedWidth(140)
        self.inp_paid.valueChanged.connect(self.calculate_balance)

        lbl_bal = QLabel("Balance:")
        lbl_bal.setStyleSheet("font-weight: bold;")
        self.inp_balance = QLineEdit("₹ 0.00")
        self.inp_balance.setReadOnly(True)
        self.inp_balance.setFixedWidth(140)
        self.inp_balance.setStyleSheet(f"background-color: #f1f3f4; color: {COLOR_DELETE}; font-weight: bold; border: 1px solid {COLOR_DELETE};")

        foot_lay.addWidget(lbl_pay_mode)
        foot_lay.addWidget(self.cmb_pay_mode)
        foot_lay.addWidget(lbl_paid)
        foot_lay.addWidget(self.inp_paid)
        foot_lay.addWidget(lbl_bal)
        foot_lay.addWidget(self.inp_balance)

        self.lbl_grand_total = QLabel("Total: ₹0.00")
        self.lbl_grand_total.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLOR_NAVBAR}; margin-left: 20px;")
        foot_lay.addWidget(self.lbl_grand_total)

        btn_save = QPushButton("SAVE INVOICE")
        btn_save.setFixedSize(160, 45)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet(f"background-color: {COLOR_GREEN}; color: white; border: none; font-size: 14px; border-radius: 6px; font-weight: bold;")
        btn_save.clicked.connect(self.save_invoice)
        foot_lay.addWidget(btn_save)

        layout.addWidget(footer)

    # -----------------------------------------------------------
    # TAB 2: HISTORY
    # -----------------------------------------------------------
    def create_history_tab(self):
        layout = QVBoxLayout(self.tab_history)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Search Bar
        h_bar = QHBoxLayout()
        self.hist_search = QLineEdit()
        self.hist_search.setPlaceholderText("Search Invoice No or Supplier...")
        self.hist_search.textChanged.connect(self.load_history)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.load_history)
        h_bar.addWidget(self.hist_search)
        h_bar.addWidget(btn_refresh)
        layout.addLayout(h_bar)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)

        # LEFT: Invoice List
        self.hist_table = QTableWidget()
        self.hist_table.setColumnCount(6)
        self.hist_table.setHorizontalHeaderLabels(["ID", "Invoice No", "Supplier", "Date", "Total Amt", "Paid"])
        self.hist_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.hist_table.verticalHeader().setDefaultSectionSize(40) 
        self.hist_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.hist_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.hist_table.cellClicked.connect(self.on_history_row_clicked)
        splitter.addWidget(self.hist_table)

        # RIGHT: Details Panel
        self.details_panel = QFrame()
        self.details_panel.setStyleSheet("background: white; border-left: 1px solid #ccc;")
        self.details_panel.setVisible(False)
        det_layout = QVBoxLayout(self.details_panel)
        det_layout.setContentsMargins(15, 15, 15, 15)
        
        self.lbl_det_title = QLabel("Invoice Items")
        self.lbl_det_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_NAVBAR}; margin-bottom: 10px;")
        det_layout.addWidget(self.lbl_det_title)

        self.det_table = QTableWidget()
        self.det_table.setColumnCount(4)
        self.det_table.setHorizontalHeaderLabels(["Medicine", "Batch", "Qty", "Total"])
        self.det_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.det_table.verticalHeader().setDefaultSectionSize(35)
        det_layout.addWidget(self.det_table)
        
        btn_close_det = QPushButton("Close Details")
        btn_close_det.clicked.connect(lambda: self.details_panel.hide())
        det_layout.addWidget(btn_close_det)

        splitter.addWidget(self.details_panel)
        splitter.setSizes([700, 300])
        
        layout.addWidget(splitter)

    def on_tab_changed(self, index):
        if index == 1: self.load_history()

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
        self.details_panel.hide()
        for i, row in enumerate(rows):
            self.hist_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.hist_table.setItem(i, 1, QTableWidgetItem(str(row[1])))
            self.hist_table.setItem(i, 2, QTableWidgetItem(str(row[2])))
            self.hist_table.setItem(i, 3, QTableWidgetItem(str(row[3])))
            self.hist_table.setItem(i, 4, QTableWidgetItem(f"₹{row[4]:.2f}"))
            self.hist_table.setItem(i, 5, QTableWidgetItem(f"₹{row[5]:.2f}"))

    def on_history_row_clicked(self, row, col):
        inv_id = self.hist_table.item(row, 0).text()
        inv_no = self.hist_table.item(row, 1).text()
        
        self.lbl_det_title.setText(f"Items for Invoice: {inv_no}")
        self.details_panel.show()
        
        conn = database.get_connection()
        cur = conn.cursor()
        # Fetching qty and rate from Invoice Table
        # Note: These values might be stored as Unit-based depending on saving logic
        # We display them as is.
        cur.execute("""
            SELECT d.med_name, i.batch_no, i.quantity, i.total_amount
            FROM Purchase_Invoice_Item i
            JOIN Medicine_Details d ON i.Med_id = d.med_id
            WHERE i.invoice_id = ?
        """, (inv_id,))
        items = cur.fetchall()
        conn.close()
        
        self.det_table.setRowCount(len(items))
        for i, item in enumerate(items):
            self.det_table.setItem(i, 0, QTableWidgetItem(str(item[0])))
            self.det_table.setItem(i, 1, QTableWidgetItem(str(item[1])))
            self.det_table.setItem(i, 2, QTableWidgetItem(str(item[2]))) # Qty (Is it strips or tabs? Depends on saving logic)
            self.det_table.setItem(i, 3, QTableWidgetItem(f"₹{item[3]:.2f}"))

    # -----------------------------------------------------------
    # ENTRY LOGIC
    # -----------------------------------------------------------
    def add_row(self):
        rc = self.table.rowCount()
        self.table.insertRow(rc)
        
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Type Medicine Name...")
        completer = QCompleter(self.med_names)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        name_edit.setCompleter(completer)
        name_edit.editingFinished.connect(lambda: self.on_name_entered(rc, name_edit))
        self.table.setCellWidget(rc, 0, name_edit)
        
        btn_del = QPushButton("✕")
        btn_del.setFixedSize(30, 30)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet(f"color: white; background-color: {COLOR_DELETE}; border: none; border-radius: 4px; font-weight: bold;")
        btn_del.clicked.connect(lambda: self.remove_specific_row(btn_del))
        
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0,0,0,0)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(btn_del)
        self.table.setCellWidget(rc, 8, w)

    def on_name_entered(self, row, widget):
        name = widget.text().strip()
        if not name: return
        
        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT med_id FROM Medicine_Details WHERE med_name = ?", (name,))
        res = cur.fetchone()
        conn.close()
        
        if res:
            dummy_item = QTableWidgetItem()
            dummy_item.setData(Qt.ItemDataRole.UserRole, res[0]) 
            self.table.setItem(row, 0, dummy_item)
        else:
            QMessageBox.warning(self, "Unknown Product", f"'{name}' not found. Please add it in Masters first.")
            widget.clear()

    def remove_specific_row(self, btn):
        for r in range(self.table.rowCount()):
            widget = self.table.cellWidget(r, 8)
            if widget and widget.layout().itemAt(0).widget() == btn:
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
        if col in [4, 5]: # Qty (Strips), Buy Rate (Per Strip)
            try:
                qty_item = self.table.item(row, 4)
                rate_item = self.table.item(row, 5)
                
                qty = float(qty_item.text()) if qty_item and qty_item.text() else 0
                rate = float(rate_item.text()) if rate_item and rate_item.text() else 0
                
                total = qty * rate # Total Cost for line (Matches Invoice Total)
                
                self.table.blockSignals(True)
                self.table.setItem(row, 7, QTableWidgetItem(f"{total:.2f}"))
                self.table.blockSignals(False)
                
                self.update_grand_total()
            except: pass

    def update_grand_total(self):
        g_total = 0
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 7)
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
        if self.cmb_supplier.currentIndex() <= 0:
            QMessageBox.warning(self, "Error", "Select a Supplier.")
            return
        if not self.inp_inv_no.text().strip():
            QMessageBox.warning(self, "Error", "Invoice Number required.")
            return

        inv_no = self.inp_inv_no.text().strip()
        supp_id = self.cmb_supplier.currentData()
        date = self.date_inv.date().toString("yyyy-MM-dd")
        pay_mode = self.cmb_pay_mode.currentText()
        paid_amt = self.inp_paid.value()
        
        try: total_val = float(self.lbl_grand_total.text().replace("Total: ₹", ""))
        except: total_val = 0
        
        balance_amt = total_val - paid_amt
        rows_to_save = []
        
        conn = database.get_connection()
        cur = conn.cursor()

        try:
            for r in range(self.table.rowCount()):
                name_widget = self.table.cellWidget(r, 0)
                if not name_widget or not name_widget.text(): continue
                
                dummy = self.table.item(r, 0)
                med_id = dummy.data(Qt.ItemDataRole.UserRole) if dummy else None
                
                if not med_id:
                    QMessageBox.warning(self, "Error", f"Row {r+1}: Product not valid.")
                    return

                try:
                    batch = self.table.item(r, 1).text().strip() if self.table.item(r, 1) else ""
                    mfg = self.table.item(r, 2).text().strip() if self.table.item(r, 2) else ""
                    exp = self.table.item(r, 3).text().strip() if self.table.item(r, 3) else ""
                    
                    # User Input (Strips)
                    qty_strips = float(self.table.item(r, 4).text() or 0)
                    rate_per_strip = float(self.table.item(r, 5).text() or 0)
                    mrp_per_strip = float(self.table.item(r, 6).text() or 0)
                    line_total = float(self.table.item(r, 7).text() or 0)
                    
                    if not batch or not exp:
                        QMessageBox.warning(self, "Error", f"Row {r+1}: Batch and Expiry are required.")
                        return

                    # --- KEY CHANGE: CONVERT TO TABLETS ---
                    cur.execute("SELECT tabs_per_strip FROM Medicine_Details WHERE med_id = ?", (med_id,))
                    res = cur.fetchone()
                    tabs_per_strip = int(res[0]) if res and res[0] else 1
                    
                    if tabs_per_strip > 1:
                        final_qty_units = qty_strips * tabs_per_strip
                        final_rate_unit = rate_per_strip / tabs_per_strip
                        final_mrp_unit = mrp_per_strip / tabs_per_strip
                    else:
                        final_qty_units = qty_strips
                        final_rate_unit = rate_per_strip
                        final_mrp_unit = mrp_per_strip

                    rows_to_save.append({
                        "med_id": med_id, 
                        "batch": batch, "mfg": mfg, "exp": exp,
                        "qty_units": final_qty_units, 
                        "rate_unit": final_rate_unit, 
                        "mrp_unit": final_mrp_unit, 
                        "total": line_total
                    })
                except ValueError:
                    QMessageBox.warning(self, "Error", f"Row {r+1}: Invalid numbers.")
                    return

            if not rows_to_save:
                QMessageBox.warning(self, "Error", "No items to save.")
                return

            # 1. Invoice Header
            cur.execute("""
                INSERT INTO Purchase_Invoice (invoice_number, supp_id, invoice_date, payment_mode, total_amount, paid_amount, balance, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (inv_no, supp_id, date, pay_mode, total_val, paid_amt, balance_amt))
            inv_id = cur.lastrowid
            
            # 2. Items & Stock (Storing Units/Tablets now)
            for row in rows_to_save:
                # Saving Units into Invoice Item table too, to maintain consistency with Stock table.
                # If we saved Strips here, later joins with Stock (Units) would be complex.
                cur.execute("""
                    INSERT INTO Purchase_Invoice_Item 
                    (invoice_id, Med_id, batch_no, expiry_date, quantity, purchase_rate_incl, mrp, total_amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (inv_id, row['med_id'], row['batch'], row['exp'], row['qty_units'], row['rate_unit'], row['mrp_unit'], row['total']))
                
                # Check for existing batch in Stock
                cur.execute("SELECT stock_id FROM Medicine_Stock WHERE med_id = ? AND batch_no = ?", (row['med_id'], row['batch']))
                existing = cur.fetchone()
                
                if existing:
                    # Update existing batch quantity and rates (Unit based)
                    cur.execute("""
                        UPDATE Medicine_Stock 
                        SET quantity = quantity + ?, purchase_rate = ?, sale_rate = ? 
                        WHERE stock_id = ?
                    """, (row['qty_units'], row['rate_unit'], row['mrp_unit'], existing[0]))
                else:
                    # Create new batch (Unit based)
                    cur.execute("""
                        INSERT INTO Medicine_Stock (med_id, batch_no, mfg_date, exp_date, quantity, purchase_rate, sale_rate) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (row['med_id'], row['batch'], row['mfg'], row['exp'], row['qty_units'], row['rate_unit'], row['mrp_unit']))

            # 3. UPDATE SUPPLIER BALANCE LOGIC
            if balance_amt != 0:
                cur.execute("UPDATE Supplier SET balance = balance + ? WHERE Supp_id = ?", (balance_amt, supp_id))

            conn.commit()
            QMessageBox.information(self, "Success", "Invoice Saved! Stock updated in Units (Tablets).")
            self.clear_form()
            
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Database Error", str(e))
        finally:
            conn.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PurchaseEntryInterface()
    window.resize(1100, 700)
    window.show()
    sys.exit(app.exec())