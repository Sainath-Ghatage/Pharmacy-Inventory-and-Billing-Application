import sys
import datetime
import sqlite3
import pandas as pd 
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDateEdit, QMessageBox, QDialog, QFormLayout,
    QFrame, QAbstractItemView, QCompleter, QSpinBox, QDoubleSpinBox,
    QGridLayout, QTabWidget, QSplitter, QFileDialog, QSizePolicy, QSpacerItem
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
    QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {{
        background-color: {COLOR_PANEL};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 14px;
        min-height: 25px;
    }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
        border: 2px solid {COLOR_NAVBAR};
    }}
    QTableWidget {{
        background-color: {COLOR_PANEL};
        color: {COLOR_TEXT};
        gridline-color: {COLOR_BORDER};
        border: 1px solid {COLOR_BORDER};
        border-radius: 6px;
        outline: none;
    }}
    QTableWidget::item {{ padding-left: 5px; }}
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

# --- POPUP DIALOG FOR ORDER SELECTION ---
class OrderSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Purchase Order")
        self.resize(600, 400)
        self.selected_po_id = None
        
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["PO ID", "Supplier", "Date", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.select_and_close)
        
        layout.addWidget(QLabel("Double click an order to load items:"))
        layout.addWidget(self.table)
        
        self.load_orders()
        
    def load_orders(self):
        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT po.po_id, s.Sup_name, po.order_date, po.status 
            FROM Purchase_order po
            JOIN Supplier s ON po.supp_id = s.Supp_id
            WHERE po.status IN ('Created', 'Sent', 'Updated')
            ORDER BY po.po_id DESC
        """)
        rows = cur.fetchall()
        conn.close()
        
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.table.setItem(i, 1, QTableWidgetItem(row[1]))
            self.table.setItem(i, 2, QTableWidgetItem(row[2]))
            self.table.setItem(i, 3, QTableWidgetItem(row[3]))
            
    def select_and_close(self):
        row = self.table.currentRow()
        if row >= 0:
            self.selected_po_id = self.table.item(row, 0).text()
            self.accept()

class PurchaseEntryInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Purchase Entry")
        self.setStyleSheet(STYLE_SHEET)
        self.setMinimumSize(1000, 700)
        
        self.editing_invoice_id = None # Tracker for Edit Mode
        self.prod_names = [] 
        self.load_product_names()
        
        self.init_ui()
        self.load_suppliers()

    def load_product_names(self):
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT prod_name FROM Product_Details")
            self.prod_names = [row[0] for row in cur.fetchall()]
        except: pass
        finally: conn.close()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Title
        lbl_title = QLabel("Purchase Management")
        lbl_title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLOR_NAVBAR};")
        main_layout.addWidget(lbl_title)

        # Tabs
        self.tabs = QTabWidget()
        self.tab_entry = QWidget()
        self.tab_history = QWidget()
        
        self.tabs.addTab(self.tab_entry, "New Invoice Entry")
        self.tabs.addTab(self.tab_history, "Invoice History")
        
        self.create_entry_tab()
        self.create_history_tab()
        
        self.tabs.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tabs)

    # -----------------------------------------------------------
    # TAB 1: ENTRY (FIXED LAYOUT)
    # -----------------------------------------------------------
    def create_entry_tab(self):
        layout = QVBoxLayout(self.tab_entry)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # 1. HEADER INPUTS
        input_container = QFrame()
        input_container.setStyleSheet(f"background-color: {COLOR_PANEL}; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")
        
        header_layout = QHBoxLayout(input_container)
        header_layout.setContentsMargins(15, 15, 15, 15)
        header_layout.setSpacing(15)

        def create_field_box(label_text, widget):
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #6c757d; text-transform: uppercase;")
            container = QWidget()
            vbox = QVBoxLayout(container)
            vbox.setContentsMargins(0,0,0,0)
            vbox.setSpacing(2)
            vbox.addWidget(lbl)
            vbox.addWidget(widget)
            return container

        self.inp_inv_no = QLineEdit()
        self.inp_inv_no.setPlaceholderText("e.g. INV-2026-001")
        
        self.cmb_supplier = QComboBox()
        self.cmb_supplier.setEditable(True)
        
        self.date_inv = QDateEdit(QDate.currentDate())
        self.date_inv.setCalendarPopup(True)

        header_layout.addWidget(create_field_box("Invoice No *", self.inp_inv_no), 1)
        header_layout.addWidget(create_field_box("Supplier *", self.cmb_supplier), 2)
        header_layout.addWidget(create_field_box("Invoice Date *", self.date_inv), 1)

        layout.addWidget(input_container)

        # 2. IMPORT TOOLBAR
        tool_bar = QHBoxLayout()
        
        btn_import_file = QPushButton("Import CSV/Excel")
        btn_import_file.clicked.connect(self.import_from_file)
        btn_import_file.setStyleSheet("background-color: #ffc107; color: #000; border: none;")
        
        btn_load_po = QPushButton("Load from Order")
        btn_load_po.clicked.connect(self.load_from_order)
        btn_load_po.setStyleSheet(f"background-color: {COLOR_NAVBAR}; color: white; border: none;")
        
        tool_bar.addWidget(btn_import_file)
        tool_bar.addWidget(btn_load_po)
        tool_bar.addStretch()
        layout.addLayout(tool_bar)

        # 3. TABLE
        self.table = QTableWidget()
        self.table.setColumnCount(9) 
        headers = [
            "Product Name", "Batch", "Mfg", "Exp", 
            "Qty", "Buy Rate", "MRP", "Total", "Action"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) 
        self.table.setColumnWidth(1, 100) 
        self.table.setColumnWidth(2, 90)  
        self.table.setColumnWidth(3, 90)  
        self.table.setColumnWidth(4, 70)  
        self.table.setColumnWidth(5, 100) 
        self.table.setColumnWidth(6, 100) 
        self.table.setColumnWidth(7, 100) 
        self.table.setColumnWidth(8, 60)  

        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.verticalHeader().setDefaultSectionSize(45) 

        self.table.setRowCount(0)
        self.add_row()
        self.table.cellChanged.connect(self.on_cell_changed)
        layout.addWidget(self.table)

        # 4. ROW ACTIONS
        row_btns = QHBoxLayout()
        btn_add = QPushButton("+ Add New Row")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self.add_row)
        btn_add.setStyleSheet(f"color: {COLOR_NAVBAR}; border: 1px dashed {COLOR_NAVBAR}; background: #f0f8ff;")
        row_btns.addWidget(btn_add)
        row_btns.addStretch()
        layout.addLayout(row_btns)

        # 5. FOOTER
        footer = QFrame()
        footer.setStyleSheet(f"background-color: {COLOR_PANEL}; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")
        foot_main = QVBoxLayout(footer)
        foot_main.setContentsMargins(15, 10, 15, 10)
        foot_main.setSpacing(10)

        pay_row = QHBoxLayout()
        lbl_pay_mode = QLabel("Payment:"); lbl_pay_mode.setStyleSheet("font-weight: bold;")
        self.cmb_pay_mode = QComboBox()
        self.cmb_pay_mode.addItems(["Credit", "Cash", "UPI", "Cheque"])
        self.cmb_pay_mode.setFixedWidth(140)
        
        lbl_paid = QLabel("Paid:"); lbl_paid.setStyleSheet("font-weight: bold;")
        self.inp_paid = QDoubleSpinBox()
        self.inp_paid.setRange(0, 9999999); self.inp_paid.setPrefix("₹ "); self.inp_paid.setFixedWidth(140)
        self.inp_paid.valueChanged.connect(self.calculate_balance)

        lbl_bal = QLabel("Balance:"); lbl_bal.setStyleSheet("font-weight: bold;")
        self.inp_balance = QLineEdit("₹ 0.00")
        self.inp_balance.setReadOnly(True); self.inp_balance.setFixedWidth(150) 
        self.inp_balance.setStyleSheet(f"background-color: #f1f3f4; color: {COLOR_DELETE}; font-weight: bold; border: 1px solid {COLOR_DELETE};")

        pay_row.addWidget(lbl_pay_mode); pay_row.addWidget(self.cmb_pay_mode); pay_row.addSpacing(20)
        pay_row.addWidget(lbl_paid); pay_row.addWidget(self.inp_paid); pay_row.addSpacing(20)
        pay_row.addWidget(lbl_bal); pay_row.addWidget(self.inp_balance); pay_row.addStretch() 
        foot_main.addLayout(pay_row)

        btn_row = QHBoxLayout()
        self.btn_clear = QPushButton("Cancel Edit / Clear Form")
        self.btn_clear.clicked.connect(self.clear_form)
        self.btn_clear.setFixedWidth(180)
        self.btn_clear.setStyleSheet("color: #dc3545; border-color: #dc3545;")
        
        self.lbl_grand_total = QLabel("Total: ₹0.00")
        self.lbl_grand_total.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLOR_NAVBAR};")
        self.lbl_grand_total.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.btn_save = QPushButton("SAVE INVOICE")
        self.btn_save.setFixedSize(160, 45)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setStyleSheet(f"background-color: {COLOR_GREEN}; color: white; border: none; font-size: 14px; border-radius: 6px; font-weight: bold;")
        self.btn_save.clicked.connect(self.save_invoice)

        btn_row.addWidget(self.btn_clear); btn_row.addStretch()
        btn_row.addWidget(self.lbl_grand_total); btn_row.addSpacing(20); btn_row.addWidget(self.btn_save)

        foot_main.addLayout(btn_row)
        layout.addWidget(footer)

    # -----------------------------------------------------------
    # TAB 2: HISTORY
    # -----------------------------------------------------------
    def create_history_tab(self):
        layout = QVBoxLayout(self.tab_history)
        layout.setContentsMargins(15, 15, 15, 15)
        
        h_bar = QHBoxLayout()
        self.hist_search = QLineEdit()
        self.hist_search.setPlaceholderText("Search Invoice No or Supplier...")
        self.hist_search.textChanged.connect(self.load_history)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.load_history)
        h_bar.addWidget(self.hist_search)
        h_bar.addWidget(btn_refresh)
        layout.addLayout(h_bar)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.hist_table = QTableWidget()
        self.hist_table.setColumnCount(7) # Added Actions Column
        self.hist_table.setHorizontalHeaderLabels(["ID", "Invoice No", "Supplier", "Date", "Total Amt", "Paid", "Actions"])
        self.hist_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.hist_table.verticalHeader().setDefaultSectionSize(40) 
        self.hist_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.hist_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.hist_table.cellClicked.connect(self.on_history_row_clicked)
        splitter.addWidget(self.hist_table)
        
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
        self.det_table.setHorizontalHeaderLabels(["Product", "Batch", "Qty", "Total"])
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
            inv_id = str(row[0])
            self.hist_table.setItem(i, 0, QTableWidgetItem(inv_id))
            self.hist_table.setItem(i, 1, QTableWidgetItem(str(row[1])))
            self.hist_table.setItem(i, 2, QTableWidgetItem(str(row[2])))
            self.hist_table.setItem(i, 3, QTableWidgetItem(str(row[3])))
            self.hist_table.setItem(i, 4, QTableWidgetItem(f"₹{row[4]:.2f}"))
            self.hist_table.setItem(i, 5, QTableWidgetItem(f"₹{row[5]:.2f}"))
            
            # --- EDIT BUTTON ---
            btn_edit = QPushButton("Edit")
            btn_edit.setStyleSheet("background-color: #ffc107; color: black; border-radius: 4px; padding: 5px;")
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.clicked.connect(lambda _, x=inv_id: self.load_invoice_for_editing(x))
            
            container = QWidget()
            btn_layout = QHBoxLayout(container)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.addWidget(btn_edit)
            self.hist_table.setCellWidget(i, 6, container)

    def on_history_row_clicked(self, row, col):
        if col == 6: return # Ignore click if clicking the Edit button column
        inv_id = self.hist_table.item(row, 0).text()
        inv_no = self.hist_table.item(row, 1).text()
        self.lbl_det_title.setText(f"Items for Invoice: {inv_no}")
        self.details_panel.show()
        
        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT d.prod_name, i.batch_no, i.quantity, i.total_amount
            FROM Purchase_Invoice_Item i
            JOIN Product_Details d ON i.Prod_id = d.prod_id
            WHERE i.invoice_id = ?
        """, (inv_id,))
        items = cur.fetchall()
        conn.close()
        
        self.det_table.setRowCount(len(items))
        for i, item in enumerate(items):
            self.det_table.setItem(i, 0, QTableWidgetItem(str(item[0])))
            self.det_table.setItem(i, 1, QTableWidgetItem(str(item[1])))
            self.det_table.setItem(i, 2, QTableWidgetItem(str(item[2])))
            self.det_table.setItem(i, 3, QTableWidgetItem(f"₹{item[3]:.2f}"))

    # -----------------------------------------------------------
    # EDIT INVOICE LOGIC (NEW)
    # -----------------------------------------------------------
    def load_invoice_for_editing(self, inv_id):
        conn = database.get_connection()
        cur = conn.cursor()
        
        # 1. Fetch Header
        cur.execute("SELECT invoice_number, supp_id, invoice_date, payment_mode, paid_amount FROM Purchase_Invoice WHERE invoice_id=?", (inv_id,))
        header = cur.fetchone()
        if not header:
            conn.close()
            return
            
        inv_no, supp_id, inv_date, pay_mode, paid_amt = header
        
        # 2. Fetch Items
        cur.execute("""
            SELECT i.Prod_id, d.prod_name, i.batch_no, i.expiry_date, i.quantity, i.purchase_rate_incl, i.mrp, i.total_amount, d.tabs_per_strip 
            FROM Purchase_Invoice_Item i
            JOIN Product_Details d ON i.Prod_id = d.prod_id
            WHERE i.invoice_id=?
        """, (inv_id,))
        items = cur.fetchall()
        
        self.editing_invoice_id = inv_id
        self.tabs.setCurrentIndex(0)
        
        # Populate Header
        self.inp_inv_no.setText(inv_no)
        idx = self.cmb_supplier.findData(supp_id)
        if idx >= 0: self.cmb_supplier.setCurrentIndex(idx)
        self.date_inv.setDate(QDate.fromString(inv_date, "yyyy-MM-dd"))
        self.cmb_pay_mode.setCurrentText(pay_mode if pay_mode else "Credit")
        
        # Populate Items
        self.table.setRowCount(0)
        for pid, pname, batch, exp, qty_units, rate_unit, mrp_unit, total, tps in items:
            tps = int(tps) if tps else 1
            
            # Re-fetch mfg_date from stock (as it wasn't saved in invoice_item table directly)
            cur.execute("SELECT mfg_date FROM Product_Stock WHERE prod_id=? AND batch_no=?", (pid, batch))
            mfg_row = cur.fetchone()
            mfg = mfg_row[0] if mfg_row else ""
            
            r = self.table.rowCount()
            self.add_row()
            
            # Product Name Widget
            name_widget = self.table.cellWidget(r, 0)
            name_widget.setText(pname)
            
            # Store ID in hidden Data 
            dummy = QTableWidgetItem()
            dummy.setData(Qt.ItemDataRole.UserRole, pid)
            self.table.setItem(r, 0, dummy)
            
            # Mathematical reconversion (Units to Strips for UI)
            qty_strips = qty_units / tps
            rate_strip = rate_unit * tps
            mrp_strip = mrp_unit * tps
            
            self.table.setItem(r, 1, QTableWidgetItem(str(batch)))
            self.table.setItem(r, 2, QTableWidgetItem(str(mfg)))
            self.table.setItem(r, 3, QTableWidgetItem(str(exp)))
            self.table.setItem(r, 4, QTableWidgetItem(f"{qty_strips:g}"))
            self.table.setItem(r, 5, QTableWidgetItem(f"{rate_strip:.2f}"))
            self.table.setItem(r, 6, QTableWidgetItem(f"{mrp_strip:.2f}"))
            self.table.setItem(r, 7, QTableWidgetItem(f"{total:.2f}"))
            
        self.update_grand_total()
        self.inp_paid.setValue(paid_amt if paid_amt else 0.0)
        
        self.btn_save.setText("UPDATE INVOICE")
        self.btn_save.setStyleSheet(f"background-color: #ffc107; color: black; border: none; font-size: 14px; border-radius: 6px; font-weight: bold;")
        self.btn_clear.setText("Cancel Edit")
        
        conn.close()

    # -----------------------------------------------------------
    # ENTRY LOGIC
    # -----------------------------------------------------------
    def add_row(self):
        rc = self.table.rowCount()
        self.table.insertRow(rc)
        
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Search...")
        completer = QCompleter(self.prod_names)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        name_edit.setCompleter(completer)
        name_edit.editingFinished.connect(lambda: self.on_name_entered(rc, name_edit))
        self.table.setCellWidget(rc, 0, name_edit)
        
        btn_del = QPushButton("✕")
        btn_del.setFixedSize(25, 25)
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
        cur.execute("SELECT prod_id FROM Product_Details WHERE prod_name = ?", (name,))
        res = cur.fetchone()
        conn.close()
        
        if res:
            dummy_item = QTableWidgetItem()
            dummy_item.setData(Qt.ItemDataRole.UserRole, res[0]) 
            self.table.setItem(row, 0, dummy_item)

    def remove_specific_row(self, btn):
        for r in range(self.table.rowCount()):
            widget = self.table.cellWidget(r, 8)
            if widget and widget.layout().itemAt(0).widget() == btn:
                self.table.removeRow(r)
                self.update_grand_total()
                return

    # -----------------------------------------------------------
    # IMPORT LOGIC
    # -----------------------------------------------------------
    def import_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Excel/CSV Files (*.xlsx *.xls *.csv)")
        if not file_path: return
        try:
            if file_path.endswith('.csv'): df = pd.read_csv(file_path)
            else: df = pd.read_excel(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not read file:\n{str(e)}")
            return

        df.columns = df.columns.astype(str).str.lower().str.strip()
        map_name = ['product', 'product name', 'name', 'item', 'description', 'medicine']
        map_qty = ['qty', 'quantity', 'count', 'units', 'pieces']
        map_price = ['price', 'rate', 'cost', 'buy rate', 'p.price', 'purchase price']
        map_mrp = ['mrp', 'sale price', 'selling price']

        col_name = next((c for c in map_name if c in df.columns), None)
        col_qty = next((c for c in map_qty if c in df.columns), None)
        col_price = next((c for c in map_price if c in df.columns), None)
        col_mrp = next((c for c in map_mrp if c in df.columns), None)

        if not col_name:
            QMessageBox.warning(self, "Error", "Could not find a 'Product Name' column.")
            return

        conn = database.get_connection()
        cur = conn.cursor()

        for index, row in df.iterrows():
            prod_name = str(row[col_name]).strip()
            qty = str(row[col_qty]) if col_qty else "0"
            price = str(row[col_price]) if col_price else "0"
            mrp = str(row[col_mrp]) if col_mrp else "0"

            r = self.table.rowCount()
            self.add_row()

            widget_name = self.table.cellWidget(r, 0)
            widget_name.setText(prod_name)

            cur.execute("SELECT prod_id FROM Product_Details WHERE prod_name = ?", (prod_name,))
            res = cur.fetchone()
            if res:
                dummy_item = QTableWidgetItem()
                dummy_item.setData(Qt.ItemDataRole.UserRole, res[0])
                self.table.setItem(r, 0, dummy_item)

            self.table.setItem(r, 4, QTableWidgetItem(str(qty)))
            self.table.setItem(r, 5, QTableWidgetItem(str(price)))
            self.table.setItem(r, 6, QTableWidgetItem(str(mrp)))
            self.on_cell_changed(r, 4)

        conn.close()
        QMessageBox.information(self, "Success", "Data Imported Successfully. Please fill Batch/Expiry manually.")

    def load_from_order(self):
        dlg = OrderSelectionDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            po_id = dlg.selected_po_id
            self.load_order_items(po_id)

    def load_order_items(self, po_id):
        conn = database.get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT s.Sup_name, s.Supp_id FROM Purchase_order po JOIN Supplier s ON po.supp_id = s.Supp_id WHERE po.po_id = ?", (po_id,))
        supp_row = cur.fetchone()
        if supp_row:
            index = self.cmb_supplier.findData(supp_row[1])
            if index >= 0: self.cmb_supplier.setCurrentIndex(index)
            else: self.cmb_supplier.setEditText(supp_row[0])

        cur.execute("SELECT d.prod_name, pi.Quantity FROM PO_item pi JOIN Product_Details d ON pi.Prod_id = d.prod_id WHERE pi.po_id = ?", (po_id,))
        items = cur.fetchall()
        conn.close()

        self.table.setRowCount(0)
        for prod_name, qty in items:
            r = self.table.rowCount()
            self.add_row()
            widget_name = self.table.cellWidget(r, 0)
            widget_name.setText(prod_name)
            self.on_name_entered(r, widget_name)
            self.table.setItem(r, 4, QTableWidgetItem(str(qty)))
            self.on_cell_changed(r, 4)

        QMessageBox.information(self, "Loaded", f"Loaded items from Order #{po_id}.")

    # -----------------------------------------------------------
    # STANDARD LOGIC
    # -----------------------------------------------------------
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
        if col in [4, 5]: # Qty, Rate
            try:
                qty_item = self.table.item(row, 4)
                rate_item = self.table.item(row, 5)
                
                qty = float(qty_item.text()) if qty_item and qty_item.text() else 0
                rate = float(rate_item.text()) if rate_item and rate_item.text() else 0
                
                total = qty * rate
                
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
        self.editing_invoice_id = None
        self.btn_save.setText("SAVE INVOICE")
        self.btn_save.setStyleSheet(f"background-color: {COLOR_GREEN}; color: white; border: none; font-size: 14px; border-radius: 6px; font-weight: bold;")
        self.btn_clear.setText("Cancel Edit / Clear Form")
        
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
                prod_id = dummy.data(Qt.ItemDataRole.UserRole) if dummy else None
                
                if not prod_id:
                    cur.execute("SELECT prod_id FROM Product_Details WHERE prod_name=?", (name_widget.text().strip(),))
                    res = cur.fetchone()
                    if res: prod_id = res[0]
                    else:
                        QMessageBox.warning(self, "Error", f"Row {r+1}: Product '{name_widget.text()}' not found in DB.")
                        return

                try:
                    batch = self.table.item(r, 1).text().strip() if self.table.item(r, 1) else ""
                    mfg = self.table.item(r, 2).text().strip() if self.table.item(r, 2) else ""
                    exp = self.table.item(r, 3).text().strip() if self.table.item(r, 3) else ""
                    
                    qty_strips = float(self.table.item(r, 4).text() or 0)
                    rate_per_strip = float(self.table.item(r, 5).text() or 0)
                    mrp_per_strip = float(self.table.item(r, 6).text() or 0)
                    line_total = float(self.table.item(r, 7).text() or 0)
                    
                    if not batch or not exp:
                        QMessageBox.warning(self, "Error", f"Row {r+1}: Batch and Expiry are required.")
                        return

                    cur.execute("SELECT tabs_per_strip FROM Product_Details WHERE prod_id = ?", (prod_id,))
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
                        "prod_id": prod_id, 
                        "batch": batch, "mfg": mfg, "exp": exp,
                        "qty_units": final_qty_units, 
                        "rate_unit": final_rate_unit, 
                        "mrp_unit": final_mrp_unit, 
                        "mrp_strip": mrp_per_strip, 
                        "total": line_total
                    })
                except ValueError:
                    QMessageBox.warning(self, "Error", f"Row {r+1}: Invalid numbers.")
                    return

            if not rows_to_save:
                QMessageBox.warning(self, "Error", "No items to save.")
                return

            # --- EDIT MODE: REVERT PREVIOUS DATA ---
            if self.editing_invoice_id:
                # 1. Reverse Supplier Balance
                cur.execute("SELECT balance, supp_id FROM Purchase_Invoice WHERE invoice_id=?", (self.editing_invoice_id,))
                old_bal_row = cur.fetchone()
                if old_bal_row:
                    cur.execute("UPDATE Supplier SET balance = balance - ? WHERE Supp_id = ?", (old_bal_row[0], old_bal_row[1]))
                
                # 2. Reverse Stock Quantities
                cur.execute("SELECT Prod_id, batch_no, quantity FROM Purchase_Invoice_Item WHERE invoice_id=?", (self.editing_invoice_id,))
                for pid, bno, old_qty in cur.fetchall():
                    cur.execute("UPDATE Product_Stock SET quantity = quantity - ? WHERE prod_id=? AND batch_no=?", (old_qty, pid, bno))
                
                # 3. Clear old items
                cur.execute("DELETE FROM Purchase_Invoice_Item WHERE invoice_id=?", (self.editing_invoice_id,))
                
                # 4. Update Header
                cur.execute("""
                    UPDATE Purchase_Invoice 
                    SET invoice_number=?, supp_id=?, invoice_date=?, payment_mode=?, total_amount=?, paid_amount=?, balance=? 
                    WHERE invoice_id=?
                """, (inv_no, supp_id, date, pay_mode, total_val, paid_amt, balance_amt, self.editing_invoice_id))
                inv_id = self.editing_invoice_id

            # --- NORMAL INSERT MODE ---
            else:
                cur.execute("""
                    INSERT INTO Purchase_Invoice (invoice_number, supp_id, invoice_date, payment_mode, total_amount, paid_amount, balance, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (inv_no, supp_id, date, pay_mode, total_val, paid_amt, balance_amt))
                inv_id = cur.lastrowid
            
            # --- APPLY ITEMS & STOCK ---
            for row in rows_to_save:
                cur.execute("""
                    INSERT INTO Purchase_Invoice_Item 
                    (invoice_id, Prod_id, batch_no, expiry_date, quantity, purchase_rate_incl, mrp, total_amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (inv_id, row['prod_id'], row['batch'], row['exp'], row['qty_units'], row['rate_unit'], row['mrp_unit'], row['total']))
                
                cur.execute("SELECT stock_id FROM Product_Stock WHERE prod_id = ? AND batch_no = ?", (row['prod_id'], row['batch']))
                existing = cur.fetchone()
                
                if existing:
                    # Update existing batch stock
                    cur.execute("""
                        UPDATE Product_Stock 
                        SET quantity = quantity + ?, purchase_rate = ?, sale_rate = ?, rate_per_tab = ? 
                        WHERE stock_id = ?
                    """, (row['qty_units'], row['rate_unit'], row['mrp_strip'], row['mrp_unit'], existing[0]))
                else:
                    # Insert new batch
                    cur.execute("""
                        INSERT INTO Product_Stock (prod_id, batch_no, mfg_date, exp_date, quantity, purchase_rate, sale_rate, rate_per_tab) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (row['prod_id'], row['batch'], row['mfg'], row['exp'], row['qty_units'], row['rate_unit'], row['mrp_strip'], row['mrp_unit']))

            if balance_amt != 0:
                cur.execute("UPDATE Supplier SET balance = balance + ? WHERE Supp_id = ?", (balance_amt, supp_id))

            conn.commit()
            msg = "Invoice Updated! Stock updated." if self.editing_invoice_id else "Invoice Saved! Stock updated."
            QMessageBox.information(self, "Success", msg)
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