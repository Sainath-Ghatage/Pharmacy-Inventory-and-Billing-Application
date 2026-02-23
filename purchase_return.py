import sys
import sqlite3
import datetime
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDateEdit, QMessageBox, QFrame, QAbstractItemView,
    QCompleter, QDoubleSpinBox, QSpinBox, QTabWidget, QFileDialog, QCheckBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QFont

# PDF Imports
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
except ImportError:
    print("ReportLab is missing. Install with: pip install reportlab")

import database

# --- COLORS ---
COLOR_BG = "#f8f9fa"
COLOR_NAVBAR = "#0d47a1"
COLOR_TEXT = "#000000"
COLOR_RED_BTN = "#dc3545"
COLOR_GREEN_BTN = "#198754"
COLOR_BORDER = "#dee2e6"

# --- GLOBAL STYLESHEET FOR THIS PAGE ---
STYLE_SHEET = f"""
    QWidget {{
        background-color: {COLOR_BG};
        color: {COLOR_TEXT};
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 13px;
    }}
    QTableWidget {{
        background-color: white;
        color: black;
        gridline-color: #ccc;
        selection-background-color: transparent;
        selection-color: black;
    }}
    QHeaderView::section {{
        background-color: {COLOR_NAVBAR};
        color: white;
        padding: 6px;
        font-weight: bold;
        border: 1px solid #0a3d8f;
    }}
    QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox {{
        background-color: white;
        color: black;
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 5px 10px;
    }}
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
        border: 1px solid {COLOR_NAVBAR};
    }}
    QComboBox QAbstractItemView {{
        background-color: white;
        color: black;
        selection-background-color: {COLOR_NAVBAR};
        selection-color: white;
    }}
    QLabel {{
        color: black;
        background: transparent;
    }}
    /* --- CUSTOM CHECKBOX STYLING --- */
    QCheckBox {{
        background: transparent;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid #888;
        border-radius: 4px;
        background-color: white;
    }}
    QCheckBox::indicator:hover {{
        border: 2px solid {COLOR_NAVBAR};
    }}
    QCheckBox::indicator:checked {{
        background-color: {COLOR_GREEN_BTN};
        border: 2px solid {COLOR_GREEN_BTN};
        image: url(check.png); 
    }}
"""

class PurchaseReturnInterface(QWidget):
    
    return_processed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet(STYLE_SHEET)
        
        self.editing_return_id = None
        self.check_schema()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {COLOR_BORDER}; background: white; }}
            QTabBar::tab {{ background: #e9ecef; padding: 12px 25px; border-top-left-radius: 4px; border-top-right-radius: 4px; color: black; }}
            QTabBar::tab:selected {{ background: white; color: {COLOR_NAVBAR}; border-top: 3px solid {COLOR_NAVBAR}; font-weight: bold; }}
        """)
        self.layout.addWidget(self.tabs)

        self.tab_new = QWidget()
        self.setup_new_return_tab()
        self.tabs.addTab(self.tab_new, "New Purchase Return (Debit Note)")

        self.tab_history = QWidget()
        self.setup_history_tab()
        self.tabs.addTab(self.tab_history, "Return History")

        self.tab_expiring = QWidget()
        self.setup_expiring_tab()
        self.tabs.addTab(self.tab_expiring, "Expiring Stock Alerts")

        self.load_initial_data()
        self.tabs.currentChanged.connect(self.on_tab_change)

    def check_schema(self):
        conn = database.get_connection()
        if not conn: return
        cursor = conn.cursor()
        try:
            cursor.execute("PRAGMA table_info(Purchase_Return)")
            columns = [col[1] for col in cursor.fetchall()]
            if "payment_mode" not in columns:
                cursor.execute("ALTER TABLE Purchase_Return ADD COLUMN payment_mode TEXT DEFAULT 'Credit'")
            if "amount_received" not in columns:
                cursor.execute("ALTER TABLE Purchase_Return ADD COLUMN amount_received REAL DEFAULT 0")
            if "balance" not in columns:
                cursor.execute("ALTER TABLE Purchase_Return ADD COLUMN balance REAL DEFAULT 0")
            conn.commit()
        except Exception as e:
            print(f"Schema Check Error: {e}")
        finally:
            conn.close()

    # ==========================================
    # TAB 1: NEW RETURN SETUP
    # ==========================================
    def setup_new_return_tab(self):
        layout = QVBoxLayout(self.tab_new)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        top_frame = QFrame()
        top_frame.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #ddd;")
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(15, 15, 15, 15)
        
        self.cmb_supplier = QComboBox()
        self.cmb_supplier.setPlaceholderText("Select Supplier")
        self.cmb_supplier.setEditable(True)
        self.cmb_supplier.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.cmb_supplier.setMinimumWidth(400)
        self.cmb_supplier.setMinimumHeight(38)
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMinimumWidth(180)
        self.date_edit.setMinimumHeight(38)

        top_layout.addWidget(QLabel("<b>Supplier:</b>"))
        top_layout.addWidget(self.cmb_supplier)
        top_layout.addSpacing(30)
        top_layout.addWidget(QLabel("<b>Return Date:</b>"))
        top_layout.addWidget(self.date_edit)
        top_layout.addStretch()
        
        self.lbl_return_no = QLabel("New Return")
        self.lbl_return_no.setStyleSheet("color: #6c757d; font-style: italic; font-size: 14px; font-weight: bold;")
        top_layout.addWidget(self.lbl_return_no)
        layout.addWidget(top_frame)

        # UPDATED TABLE: 7 Columns for Strips and Loose Tabs
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Product Name", "Batch No", "Expiry", "Strips/Boxes", "Loose Tabs", "Amount (₹)", "Action"])
        
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(2, 90) 
        self.table.setColumnWidth(3, 100) 
        self.table.setColumnWidth(4, 100) 
        self.table.setColumnWidth(5, 120) 
        self.table.setColumnWidth(6, 60)  
        layout.addWidget(self.table)
        
        btn_add = QPushButton(" + Add Item")
        btn_add.setFixedSize(140, 38)
        btn_add.setStyleSheet(f"background-color: {COLOR_NAVBAR}; color: white; border-radius: 4px; font-weight: bold; font-size: 13px;")
        btn_add.clicked.connect(self.add_row)
        layout.addWidget(btn_add)

        bot_frame = QFrame()
        bot_frame.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #ddd;")
        bot_layout = QVBoxLayout(bot_frame)
        bot_layout.setContentsMargins(15, 10, 15, 10)
        bot_layout.setSpacing(10)

        pay_row = QHBoxLayout()
        self.cmb_pay_mode = QComboBox(); self.cmb_pay_mode.addItems(["Credit", "Cash", "UPI", "Bank Transfer"]); self.cmb_pay_mode.setFixedWidth(140)
        self.inp_received = QDoubleSpinBox(); self.inp_received.setRange(0, 9999999); self.inp_received.setPrefix("₹ "); self.inp_received.setFixedWidth(140)
        self.inp_received.valueChanged.connect(self.calculate_balance)
        self.inp_balance = QLineEdit("₹ 0.00"); self.inp_balance.setReadOnly(True); self.inp_balance.setFixedWidth(150)
        self.inp_balance.setStyleSheet(f"background-color: #f1f3f4; color: {COLOR_RED_BTN}; font-weight: bold; border: 1px solid {COLOR_RED_BTN};")

        pay_row.addWidget(QLabel("<b>Payment Mode:</b>")); pay_row.addWidget(self.cmb_pay_mode); pay_row.addSpacing(20)
        pay_row.addWidget(QLabel("<b>Amount Received:</b>")); pay_row.addWidget(self.inp_received); pay_row.addSpacing(20)
        pay_row.addWidget(QLabel("<b>Balance (Owed by Supp):</b>")); pay_row.addWidget(self.inp_balance); pay_row.addStretch()
        bot_layout.addLayout(pay_row)

        action_row = QHBoxLayout()
        self.btn_clear = QPushButton("Cancel Edit / Clear Form"); self.btn_clear.setFixedSize(180, 40)
        self.btn_clear.setStyleSheet("color: #dc3545; border: 1px solid #dc3545; background-color: white; font-weight: bold;"); self.btn_clear.clicked.connect(self.clear_form)
        
        self.lbl_total_amount = QLabel("Total Return Value: ₹0.00"); self.lbl_total_amount.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold)); self.lbl_total_amount.setStyleSheet("color: #dc3545;")

        self.btn_save = QPushButton("Process Return"); self.btn_save.setFixedSize(220, 45)
        self.btn_save.setStyleSheet(f"background-color: {COLOR_GREEN_BTN}; color: white; font-weight: bold; border-radius: 5px; font-size: 14px;"); self.btn_save.clicked.connect(self.save_return)

        action_row.addWidget(self.btn_clear); action_row.addStretch()
        action_row.addWidget(self.lbl_total_amount); action_row.addSpacing(30); action_row.addWidget(self.btn_save)

        bot_layout.addLayout(action_row)
        layout.addWidget(bot_frame)

    # ==========================================
    # TAB 2: HISTORY SETUP
    # ==========================================
    def setup_history_tab(self):
        layout = QVBoxLayout(self.tab_history)
        layout.setContentsMargins(20, 20, 20, 20)

        filter_layout = QHBoxLayout()
        self.search_history = QLineEdit()
        self.search_history.setPlaceholderText("Search by Supplier or Return #...")
        self.search_history.setMinimumWidth(500); self.search_history.setMinimumHeight(40); self.search_history.setFont(QFont("Segoe UI", 11))
        self.search_history.textChanged.connect(self.load_history)
        
        btn_refresh = QPushButton("Refresh"); btn_refresh.setFixedSize(120, 40)
        btn_refresh.setStyleSheet(f"background-color: {COLOR_NAVBAR}; color: white; font-weight: bold; border-radius: 4px;")
        btn_refresh.clicked.connect(self.load_history)
        
        filter_layout.addWidget(self.search_history); filter_layout.addWidget(btn_refresh); filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self.hist_table = QTableWidget()
        self.hist_table.setColumnCount(8)
        self.hist_table.setHorizontalHeaderLabels(["Return #", "Supplier", "Date", "Items", "Total Amt", "Received", "Balance", "Actions"])
        self.hist_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.hist_table.setColumnWidth(0, 140); self.hist_table.setColumnWidth(2, 110); self.hist_table.setColumnWidth(3, 80) 
        self.hist_table.setColumnWidth(4, 110); self.hist_table.setColumnWidth(5, 110); self.hist_table.setColumnWidth(6, 110); self.hist_table.setColumnWidth(7, 180) 
        self.hist_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.hist_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.hist_table)

    # ==========================================
    # TAB 3: EXPIRING STOCK SETUP
    # ==========================================
    def setup_expiring_tab(self):
        layout = QVBoxLayout(self.tab_expiring)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        filter_layout = QHBoxLayout()
        self.exp_search = QLineEdit()
        self.exp_search.setPlaceholderText("🔍 Search Product or Batch...")
        self.exp_search.setMinimumHeight(35)
        self.exp_search.textChanged.connect(self.load_expiring_data)
        
        self.exp_type_filter = QComboBox()
        self.exp_type_filter.setMinimumHeight(35)
        self.exp_type_filter.addItem("All Types")
        self.exp_type_filter.addItems(["Tablet", "Capsule", "Syrup", "Injection", "Cream", "Ointment", "Drops", "Spray", "Powder", "Medical Devices", "Personal Care & Wellness"])
        self.exp_type_filter.currentIndexChanged.connect(self.load_expiring_data)
        
        self.exp_sort = QComboBox()
        self.exp_sort.setMinimumHeight(35)
        self.exp_sort.addItems(["Days Left (Low to High)", "Days Left (High to Low)", "Product Name (A-Z)"])
        self.exp_sort.currentIndexChanged.connect(self.load_expiring_data)

        filter_layout.addWidget(self.exp_search, stretch=2)
        filter_layout.addWidget(QLabel("<b>Type:</b>"))
        filter_layout.addWidget(self.exp_type_filter, stretch=1)
        filter_layout.addWidget(QLabel("<b>Sort:</b>"))
        filter_layout.addWidget(self.exp_sort, stretch=1)
        layout.addLayout(filter_layout)

        action_layout = QHBoxLayout()
        lbl_info = QLabel("<b>Products expiring within 6 months or already expired:</b>")
        lbl_info.setFont(QFont("Segoe UI", 11))
        
        btn_refresh_exp = QPushButton("⟳ Refresh List")
        btn_refresh_exp.setStyleSheet(f"background-color: #6c757d; color: white; padding: 8px 15px; font-weight: bold; border-radius: 4px;")
        btn_refresh_exp.clicked.connect(self.load_expiring_data)
        
        btn_add_selected = QPushButton("➡ Add Selected to Return Form")
        btn_add_selected.setStyleSheet(f"background-color: {COLOR_NAVBAR}; color: white; padding: 8px 15px; font-weight: bold; border-radius: 4px;")
        btn_add_selected.clicked.connect(self.add_expiring_to_return)

        action_layout.addWidget(lbl_info)
        action_layout.addStretch()
        action_layout.addWidget(btn_refresh_exp)
        action_layout.addWidget(btn_add_selected)
        layout.addLayout(action_layout)

        self.exp_table = QTableWidget()
        self.exp_table.setColumnCount(8)
        self.exp_table.setHorizontalHeaderLabels(["Select", "Product Name", "Type", "Batch", "Stock Qty", "Expiry Date", "Days Left", "Status"])
        self.exp_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.exp_table.setColumnWidth(0, 60)
        self.exp_table.setColumnWidth(2, 120)
        self.exp_table.setColumnWidth(3, 100)
        self.exp_table.setColumnWidth(4, 100)
        self.exp_table.setColumnWidth(5, 100)
        self.exp_table.setColumnWidth(6, 100)
        self.exp_table.setColumnWidth(7, 130)
        
        self.exp_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.exp_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.exp_table)

    # ==========================================
    # CORE LOGIC & DATA LOADING
    # ==========================================
    def load_initial_data(self):
        self.suppliers = []
        self.products_cache = []

        conn = database.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        cursor.execute("SELECT Supp_id, Sup_name FROM Supplier ORDER BY Sup_name")
        self.suppliers = cursor.fetchall()
        
        self.cmb_supplier.clear()
        self.cmb_supplier.addItem("Select Supplier", None)
        for supp_id, name in self.suppliers:
            self.cmb_supplier.addItem(name, supp_id)

        cursor.execute("SELECT prod_id, prod_name FROM Product_Details ORDER BY prod_name")
        self.products_cache = cursor.fetchall()
        conn.close()
        
        self.load_history()
        self.load_expiring_data()

    def on_tab_change(self, index):
        if index == 1:
            self.load_history()
        elif index == 2:
            self.load_expiring_data()

    # --- Expiring Data Logic ---
    def load_expiring_data(self):
        search_txt = self.exp_search.text().lower()
        type_filter = self.exp_type_filter.currentText()
        sort_opt = self.exp_sort.currentText()

        self.exp_table.setRowCount(0)
        conn = database.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.prod_id, d.prod_name, s.batch_no, s.quantity, s.exp_date, d.tabs_per_strip, d.type
            FROM Product_Stock s
            JOIN Product_Details d ON s.prod_id = d.prod_id
            WHERE s.quantity > 0
        """)
        rows = cursor.fetchall()
        conn.close()

        filtered_items = []
        today = datetime.date.today()

        for prod_id, prod_name, batch, qty, exp_date_str, tps, p_type in rows:
            if not exp_date_str: continue
            try:
                if "/" in exp_date_str:
                    m, y = map(int, exp_date_str.split('/'))
                    y = 2000 + y if y < 100 else y
                    exp_date = datetime.date(y, m, 1)
                else:
                    exp_date = datetime.datetime.strptime(exp_date_str, "%Y-%m-%d").date()
            except:
                continue

            days_left = (exp_date - today).days

            if days_left <= 180:
                if search_txt and search_txt not in prod_name.lower() and search_txt not in str(batch).lower():
                    continue
                if type_filter != "All Types" and str(p_type).lower() != type_filter.lower():
                    continue
                
                filtered_items.append({
                    "prod_id": prod_id,
                    "prod_name": prod_name,
                    "type": str(p_type),
                    "batch": batch,
                    "qty": qty,
                    "exp_date_str": exp_date_str,
                    "days_left": days_left,
                    "tps": tps
                })

        if sort_opt == "Days Left (Low to High)":
            filtered_items.sort(key=lambda x: x['days_left'])
        elif sort_opt == "Days Left (High to Low)":
            filtered_items.sort(key=lambda x: x['days_left'], reverse=True)
        elif sort_opt == "Product Name (A-Z)":
            filtered_items.sort(key=lambda x: x['prod_name'].lower())

        for row_idx, item in enumerate(filtered_items):
            self.exp_table.insertRow(row_idx)
            self.exp_table.setRowHeight(row_idx, 40)

            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk_layout.setContentsMargins(0,0,0,0)
            
            chk = QCheckBox()
            chk.setProperty("prod_id", item["prod_id"])
            chk.setProperty("batch", item["batch"])
            chk.toggled.connect(lambda state, r=row_idx: self.highlight_exp_row(state, r))
            chk_layout.addWidget(chk)
            self.exp_table.setCellWidget(row_idx, 0, chk_widget)

            self.exp_table.setItem(row_idx, 1, QTableWidgetItem(item["prod_name"]))
            self.exp_table.setItem(row_idx, 2, QTableWidgetItem(item["type"]))
            self.exp_table.setItem(row_idx, 3, QTableWidgetItem(str(item["batch"])))

            tps = int(item["tps"]) if item["tps"] else 1
            raw_qty = item["qty"]
            disp_qty = f"{int(raw_qty)//tps}s + {int(raw_qty)%tps}t" if tps > 1 else str(raw_qty)
            
            item_qty = QTableWidgetItem(disp_qty)
            item_qty.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.exp_table.setItem(row_idx, 4, item_qty)

            item_exp = QTableWidgetItem(item["exp_date_str"])
            item_exp.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.exp_table.setItem(row_idx, 5, item_exp)

            item_days = QTableWidgetItem(str(item["days_left"]))
            item_days.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.exp_table.setItem(row_idx, 6, item_days)

            status = "Expired" if item["days_left"] < 0 else "Expiring Soon"
            color = COLOR_RED_BTN if item["days_left"] < 0 else "#fd7e14"

            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor(color))
            status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.exp_table.setItem(row_idx, 7, status_item)

    def highlight_exp_row(self, is_checked, row):
        bg_color = QColor("#d0e1f5") if is_checked else QColor("white")
        for col in range(1, self.exp_table.columnCount()):
            item = self.exp_table.item(row, col)
            if item:
                item.setBackground(bg_color)

    def add_expiring_to_return(self):
        selected_items = []
        for i in range(self.exp_table.rowCount()):
            chk_widget = self.exp_table.cellWidget(i, 0)
            if chk_widget:
                chk = chk_widget.findChild(QCheckBox)
                if chk and chk.isChecked():
                    selected_items.append({
                        "prod_id": chk.property("prod_id"),
                        "batch": chk.property("batch")
                    })

        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select at least one item to return.")
            return

        self.tabs.setCurrentIndex(0)

        for item in selected_items:
            self.add_row()
            row = self.table.rowCount() - 1

            cmb_prod = self.table.cellWidget(row, 0)
            idx_p = cmb_prod.findData(item["prod_id"])
            if idx_p >= 0:
                cmb_prod.setCurrentIndex(idx_p)

                cmb_batch = self.table.cellWidget(row, 1)
                for b_idx in range(cmb_batch.count()):
                    b_data = cmb_batch.itemData(b_idx)
                    if b_data and b_data.get('batch') == item["batch"]:
                        cmb_batch.setCurrentIndex(b_idx)
                        
                        # Pre-fill max available strips and loose tabs
                        spin_strips = self.table.cellWidget(row, 3)
                        spin_tabs = self.table.cellWidget(row, 4)
                        
                        max_s = b_data.get('total_units', 0) // b_data.get('tps', 1)
                        max_t = b_data.get('total_units', 0) % b_data.get('tps', 1)
                        
                        spin_strips.setValue(int(max_s))
                        if spin_tabs.isEnabled():
                            spin_tabs.setValue(int(max_t))
                        break

        for i in range(self.exp_table.rowCount()):
            chk_widget = self.exp_table.cellWidget(i, 0)
            if chk_widget:
                chk = chk_widget.findChild(QCheckBox)
                if chk: chk.setChecked(False)

    # --- New Return Form Logic (UPDATED FOR STRIPS & LOOSE TABS) ---
    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 45)

        cmb_prod = QComboBox()
        cmb_prod.setEditable(True)
        cmb_prod.setPlaceholderText("Type Product Name")
        cmb_prod.addItem("", None)
        for prod_id, name in self.products_cache:
            cmb_prod.addItem(name, prod_id)
        
        completer = QCompleter([name for _, name in self.products_cache])
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        cmb_prod.setCompleter(completer)
        cmb_prod.currentIndexChanged.connect(lambda _, r=row: self.on_prod_selected(r))
        self.table.setCellWidget(row, 0, cmb_prod)

        cmb_batch = QComboBox()
        cmb_batch.setPlaceholderText("Select Batch")
        cmb_batch.currentIndexChanged.connect(lambda _, r=row: self.on_batch_selected(r))
        self.table.setCellWidget(row, 1, cmb_batch)

        lbl_exp = QLabel("-")
        lbl_exp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_exp.setStyleSheet("color: black; font-weight: bold;")
        self.table.setCellWidget(row, 2, lbl_exp)

        # COLUMN 3: STRIPS
        spin_strips = QSpinBox()
        spin_strips.setRange(0, 99999)
        spin_strips.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setCellWidget(row, 3, spin_strips)

        # COLUMN 4: LOOSE TABS
        spin_tabs = QSpinBox()
        spin_tabs.setRange(0, 99999)
        spin_tabs.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setCellWidget(row, 4, spin_tabs)

        # COLUMN 5: AMOUNT
        spin_amt = QDoubleSpinBox()
        spin_amt.setRange(0, 999999)
        spin_amt.setPrefix("₹ ")
        spin_amt.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        spin_amt.valueChanged.connect(self.calculate_totals)
        self.table.setCellWidget(row, 5, spin_amt)

        # COLUMN 6: DELETE BUTTON
        btn_del = QPushButton("✖")
        btn_del.setStyleSheet("color: white; background-color: #dc3545; font-weight: bold; border-radius: 4px; margin: 5px;")
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.clicked.connect(lambda _, r=row: self.remove_row(r))
        self.table.setCellWidget(row, 6, btn_del)

    def remove_row(self, row):
        self.table.removeRow(row)
        self.calculate_totals()
        
        for i in range(self.table.rowCount()):
            btn = self.table.cellWidget(i, 6)
            try: btn.clicked.disconnect() 
            except: pass
            btn.clicked.connect(lambda _, r=i: self.remove_row(r))
            
            cmb_prod = self.table.cellWidget(i, 0)
            try: cmb_prod.currentIndexChanged.disconnect()
            except: pass
            cmb_prod.currentIndexChanged.connect(lambda _, r=i: self.on_prod_selected(r))
            
            cmb_batch = self.table.cellWidget(i, 1)
            try: cmb_batch.currentIndexChanged.disconnect()
            except: pass
            cmb_batch.currentIndexChanged.connect(lambda _, r=i: self.on_batch_selected(r))

    def on_prod_selected(self, row):
        cmb_prod = self.table.cellWidget(row, 0)
        prod_id = cmb_prod.currentData()
        
        cmb_batch = self.table.cellWidget(row, 1)
        cmb_batch.clear()
        
        if not prod_id: return

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.batch_no, s.quantity, s.exp_date, s.purchase_rate, d.tabs_per_strip 
            FROM Product_Stock s
            JOIN Product_Details d ON s.prod_id = d.prod_id
            WHERE s.prod_id = ? AND s.quantity > 0
        """, (prod_id,))
        batches = cursor.fetchall()
        conn.close()

        cmb_batch.addItem("Select Batch", None)
        for batch_no, qty, exp, rate_unit, tps in batches:
            tps = int(tps) if tps else 1
            disp_qty = f"{int(qty)//tps}s + {int(qty)%tps}t" if tps > 1 else str(qty)
            rate_strip = rate_unit * tps
            
            cmb_batch.addItem(f"{batch_no} (Stock: {disp_qty})", 
                              {"exp": exp, "rate_strip": rate_strip, "batch": batch_no, "tps": tps, "total_units": qty})

    def on_batch_selected(self, row):
        cmb_batch = self.table.cellWidget(row, 1)
        data = cmb_batch.currentData()
        
        lbl_exp = self.table.cellWidget(row, 2)
        spin_strips = self.table.cellWidget(row, 3)
        spin_tabs = self.table.cellWidget(row, 4)
        spin_amt = self.table.cellWidget(row, 5)
        
        if data:
            lbl_exp.setText(data['exp'])
            rate_strip = data['rate_strip']
            tps = data['tps']
            total_units = data.get('total_units', 0)
            rate_tab = rate_strip / tps if tps > 0 else rate_strip
            
            # 1. Set absolute maximum for Strips based on total units
            max_strips = int(total_units // tps) if tps > 0 else int(total_units)
            spin_strips.setMaximum(max_strips)
            
            # Disable the "Loose Tabs" box if the product is single-unit (like Syrup or Cream)
            if tps <= 1:
                spin_tabs.setValue(0)
                spin_tabs.setMaximum(0)
                spin_tabs.setEnabled(False)
            else:
                spin_tabs.setEnabled(True)

            try: 
                spin_strips.valueChanged.disconnect() 
                spin_tabs.valueChanged.disconnect() 
            except: pass
            
            # 2. Auto-calculate amount and DYNAMICALLY LIMIT Loose Tabs
            def auto_calc_amount():
                s_val = spin_strips.value()
                
                # --- THE LIMITER LOGIC ---
                if tps > 1:
                    # Calculate how many units are left after selecting strips
                    remaining_units = total_units - (s_val * tps)
                    
                    # The max loose tabs is either the remaining units, or (tabs_per_strip - 1)
                    max_allowed_tabs = min(tps - 1, remaining_units)
                    spin_tabs.setMaximum(int(max(0, max_allowed_tabs)))
                # -------------------------
                
                t_val = spin_tabs.value()
                spin_amt.setValue((s_val * rate_strip) + (t_val * rate_tab))
                self.calculate_totals()
                
            spin_strips.valueChanged.connect(auto_calc_amount)
            spin_tabs.valueChanged.connect(auto_calc_amount)
            
            auto_calc_amount()
        else:
            lbl_exp.setText("-")
            spin_amt.setValue(0)
            spin_strips.setMaximum(99999)
            spin_tabs.setMaximum(99999)

        self.calculate_totals()

    def calculate_totals(self):
        total = 0.0
        for i in range(self.table.rowCount()):
            spin_amt = self.table.cellWidget(i, 5)
            if spin_amt:
                total += spin_amt.value()
        
        self.lbl_total_amount.setText(f"Total Return Value: ₹{total:,.2f}")
        self.calculate_balance()
        return total

    def calculate_balance(self):
        try:
            total_text = self.lbl_total_amount.text().replace("Total Return Value: ₹", "").replace(",", "")
            total = float(total_text) if total_text else 0.0
            received = self.inp_received.value()
            balance = total - received
            self.inp_balance.setText(f"₹ {balance:.2f}")
        except:
            self.inp_balance.setText("₹ 0.00")

    def clear_form(self):
        self.table.setRowCount(0)
        self.lbl_total_amount.setText("Total Return Value: ₹0.00")
        self.cmb_supplier.setCurrentIndex(0)
        self.inp_received.setValue(0)
        self.inp_balance.setText("₹ 0.00")
        self.cmb_pay_mode.setCurrentIndex(0)
        self.lbl_return_no.setText("New Return")
        self.btn_save.setText("Process Return")
        self.editing_return_id = None
        self.add_row()

    def save_return(self):
        supp_id = self.cmb_supplier.currentData()
        if not supp_id:
            QMessageBox.warning(self, "Error", "Please select a Supplier.")
            return
        
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "Please add items to return.")
            return

        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        total_amt = self.calculate_totals()
        pay_mode = self.cmb_pay_mode.currentText()
        amt_received = self.inp_received.value()
        balance = total_amt - amt_received
        
        items_to_save = []
        conn = database.get_connection()
        cursor = conn.cursor()
        
        for i in range(self.table.rowCount()):
            cmb_prod = self.table.cellWidget(i, 0)
            prod_id = cmb_prod.currentData()
            
            cmb_batch = self.table.cellWidget(i, 1)
            batch_data = cmb_batch.currentData()
            
            qty_strips = self.table.cellWidget(i, 3).value()
            qty_tabs = self.table.cellWidget(i, 4).value()
            amt = self.table.cellWidget(i, 5).value()
            
            if not prod_id or not batch_data:
                continue 
                
            qty_units = (qty_strips * batch_data['tps']) + qty_tabs
            
            if qty_units <= 0:
                QMessageBox.warning(self, "Error", f"Row {i+1}: Return quantity must be greater than 0.")
                conn.close()
                return
            
            cursor.execute("SELECT quantity FROM Product_Stock WHERE prod_id=? AND batch_no=?", (prod_id, batch_data['batch']))
            stock_record = cursor.fetchone()
            current_stock = stock_record[0] if stock_record else 0
            
            o_qty = 0
            if self.editing_return_id:
                cursor.execute("SELECT return_qty FROM Purchase_Return_Item WHERE return_id=? AND Prod_id=? AND batch_no=?", (self.editing_return_id, prod_id, batch_data['batch']))
                old_rec = cursor.fetchone()
                if old_rec: o_qty = old_rec[0]
                
            if qty_units > (current_stock + o_qty):
                available_total = current_stock + o_qty
                av_s = available_total // batch_data['tps']
                av_t = available_total % batch_data['tps']
                QMessageBox.warning(self, "Stock Error", f"Row {i+1}: Cannot return more than available stock ({av_s} strips and {av_t} tabs).")
                conn.close()
                return

            items_to_save.append({
                "prod_id": prod_id,
                "batch": batch_data['batch'],
                "exp": batch_data['exp'],
                "qty_units": qty_units, 
                "amt": amt,
                "tps": batch_data['tps']
            })

        if not items_to_save:
            QMessageBox.warning(self, "Error", "No valid items to save.")
            conn.close()
            return

        try:
            if self.editing_return_id:
                cursor.execute("SELECT balance, supp_id FROM Purchase_Return WHERE return_id=?", (self.editing_return_id,))
                old_ret = cursor.fetchone()
                if old_ret:
                    old_bal, old_supp = old_ret
                    cursor.execute("UPDATE Supplier SET balance = balance + ? WHERE Supp_id=?", (old_bal, old_supp))
                
                cursor.execute("SELECT Prod_id, batch_no, return_qty FROM Purchase_Return_Item WHERE return_id=?", (self.editing_return_id,))
                old_items = cursor.fetchall()
                for pid, b_no, o_qty in old_items:
                    cursor.execute("UPDATE Product_Stock SET quantity = quantity + ? WHERE prod_id=? AND batch_no=?", (o_qty, pid, b_no))
                
                cursor.execute("DELETE FROM Purchase_Return_Item WHERE return_id=?", (self.editing_return_id,))
                
                return_no = self.lbl_return_no.text()
                cursor.execute("""
                    UPDATE Purchase_Return 
                    SET supp_id=?, return_date=?, total_amount=?, payment_mode=?, amount_received=?, balance=?
                    WHERE return_id=?
                """, (supp_id, date_str, total_amt, pay_mode, amt_received, balance, self.editing_return_id))
                return_id = self.editing_return_id
            
            else:
                cursor.execute("SELECT MAX(return_id) FROM Purchase_Return")
                last_id = cursor.fetchone()[0]
                next_id = (last_id if last_id else 0) + 1
                return_no = f"PR-{datetime.datetime.now().strftime('%y%m')}-{next_id:03d}"

                cursor.execute("""
                    INSERT INTO Purchase_Return (return_number, supp_id, return_date, total_amount, payment_mode, amount_received, balance)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (return_no, supp_id, date_str, total_amt, pay_mode, amt_received, balance))
                return_id = cursor.lastrowid
            
            for item in items_to_save:
                cursor.execute("""
                    INSERT INTO Purchase_Return_Item (return_id, Prod_id, batch_no, expiry_date, return_qty, return_amount)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (return_id, item['prod_id'], item['batch'], item['exp'], item['qty_units'], item['amt']))
                
                cursor.execute("""
                    UPDATE Product_Stock 
                    SET quantity = quantity - ? 
                    WHERE prod_id = ? AND batch_no = ?
                """, (item['qty_units'], item['prod_id'], item['batch']))

            cursor.execute("UPDATE Supplier SET balance = balance - ? WHERE Supp_id = ?", (balance, supp_id))
            
            # --- AUTO-DELETE EXHAUSTED BATCHES ---
            cursor.execute("DELETE FROM Product_Stock WHERE quantity <= 0")
            
            conn.commit()
            msg = f"Purchase Return {return_no} updated successfully!" if self.editing_return_id else f"Purchase Return {return_no} saved successfully!"
            QMessageBox.information(self, "Success", msg)
            
            self.return_processed.emit()

            reply = QMessageBox.question(self, "Generate PDF", "Do you want to generate a Debit Note PDF?", 
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.generate_pdf(return_id, return_no, supp_id, items_to_save, total_amt, date_str)

            self.clear_form()
            self.load_history()
            self.load_expiring_data()
            
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Database Error", str(e))
        finally:
            conn.close()

    def load_history(self):
        search_txt = self.search_history.text().lower()
        self.hist_table.setRowCount(0)
        
        conn = database.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT pr.return_id, pr.return_number, s.Sup_name, pr.return_date, pr.total_amount, pr.amount_received, pr.balance 
            FROM Purchase_Return pr
            JOIN Supplier s ON pr.supp_id = s.Supp_id
            ORDER BY pr.return_id DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for r in rows:
            rid, rno, sname, rdate, total, received, balance = r
            received = received if received else 0.0
            balance = balance if balance else 0.0

            if search_txt and (search_txt not in sname.lower() and search_txt not in rno.lower()):
                continue
            
            cursor.execute("SELECT COUNT(*) FROM Purchase_Return_Item WHERE return_id=?", (rid,))
            count = cursor.fetchone()[0]
            
            row_idx = self.hist_table.rowCount()
            self.hist_table.insertRow(row_idx)
            self.hist_table.setRowHeight(row_idx, 40)
            
            items = [
                QTableWidgetItem(rno),
                QTableWidgetItem(sname),
                QTableWidgetItem(rdate),
                QTableWidgetItem(str(count)),
                QTableWidgetItem(f"₹{total:,.2f}"),
                QTableWidgetItem(f"₹{received:,.2f}"),
                QTableWidgetItem(f"₹{balance:,.2f}")
            ]
            
            for col, item in enumerate(items):
                item.setForeground(QColor("black"))
                if col in [3, 4, 5, 6]: 
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.hist_table.setItem(row_idx, col, item)
            
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(5, 2, 5, 2)
            btn_layout.setSpacing(5)

            btn_edit = QPushButton("Edit")
            btn_edit.setStyleSheet("background-color: #ffc107; color: black; border-radius: 4px; padding: 5px;")
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.clicked.connect(lambda _, x=rid: self.load_return_for_editing(x))

            btn_view = QPushButton("Print")
            btn_view.setStyleSheet("background-color: #17a2b8; color: white; border-radius: 4px; padding: 5px;")
            btn_view.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_view.clicked.connect(lambda _, x=rid: self.print_history_item(x))
            
            btn_layout.addWidget(btn_edit)
            btn_layout.addWidget(btn_view)
            self.hist_table.setCellWidget(row_idx, 7, btn_container)
            
        conn.close()

    def load_return_for_editing(self, return_id):
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT return_number, supp_id, return_date, payment_mode, amount_received
            FROM Purchase_Return WHERE return_id=?
        """, (return_id,))
        ret_data = cursor.fetchone()
        
        if not ret_data:
            conn.close()
            return
            
        r_no, supp_id, r_date, p_mode, a_rec = ret_data
        
        cursor.execute("""
            SELECT d.prod_id, d.prod_name, i.batch_no, i.return_qty, i.return_amount, i.expiry_date, d.tabs_per_strip
            FROM Purchase_Return_Item i
            JOIN Product_Details d ON i.Prod_id = d.prod_id
            WHERE i.return_id=?
        """, (return_id,))
        items = cursor.fetchall()
        conn.close()

        self.tabs.setCurrentIndex(0)
        self.editing_return_id = return_id
        
        self.lbl_return_no.setText(r_no)
        idx = self.cmb_supplier.findData(supp_id)
        if idx >= 0: self.cmb_supplier.setCurrentIndex(idx)
        
        self.date_edit.setDate(QDate.fromString(r_date, "yyyy-MM-dd"))
        self.cmb_pay_mode.setCurrentText(p_mode if p_mode else "Credit")
        self.inp_received.setValue(a_rec if a_rec else 0.0)
        
        self.table.setRowCount(0)
        for prod_id, p_name, batch, qty_units, amt, exp, tps in items:
            row = self.table.rowCount()
            self.add_row()
            
            cmb_prod = self.table.cellWidget(row, 0)
            idx_m = cmb_prod.findData(prod_id)
            if idx_m >= 0: cmb_prod.setCurrentIndex(idx_m)
            
            cmb_batch = self.table.cellWidget(row, 1)
            for i in range(cmb_batch.count()):
                data = cmb_batch.itemData(i)
                if data and data['batch'] == batch:
                    cmb_batch.setCurrentIndex(i)
                    break
            
            tps = int(tps) if tps else 1
            qty_strips = qty_units // tps
            qty_tabs = qty_units % tps
            
            spin_strips = self.table.cellWidget(row, 3)
            spin_strips.setValue(qty_strips)
            
            spin_tabs = self.table.cellWidget(row, 4)
            if spin_tabs.isEnabled():
                spin_tabs.setValue(qty_tabs)
            
            spin_amt = self.table.cellWidget(row, 5)
            spin_amt.setValue(amt)
            
        self.btn_save.setText("Update Return")
        self.calculate_totals()

    def print_history_item(self, return_id):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pr.return_number, pr.supp_id, pr.return_date, pr.total_amount, s.Sup_name, s.address
            FROM Purchase_Return pr
            JOIN Supplier s ON pr.supp_id = s.Supp_id
            WHERE pr.return_id = ?
        """, (return_id,))
        master = cursor.fetchone()
        
        if not master: return
        r_no, supp_id, date, total, s_name, s_addr = master
        
        cursor.execute("""
            SELECT d.prod_name, i.batch_no, i.expiry_date, i.return_qty, i.return_amount, d.tabs_per_strip
            FROM Purchase_Return_Item i
            JOIN Product_Details d ON i.Prod_id = d.prod_id
            WHERE i.return_id = ?
        """, (return_id,))
        items_db = cursor.fetchall()
        
        items_fmt = []
        for n, b, e, q, a, t in items_db:
            items_fmt.append({"prod_name": n, "batch": b, "exp": e, "qty_units": q, "amt": a, "tps": t})
            
        conn.close()
        self.generate_pdf(return_id, r_no, supp_id, items_fmt, total, date, supplier_name=s_name, supplier_addr=s_addr)

    def generate_pdf(self, return_id, return_no, supp_id, items, total, date, supplier_name=None, supplier_addr=""):
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Debit Note", f"DebitNote_{return_no}.pdf", "PDF Files (*.pdf)")
            if not file_path: return

            doc = SimpleDocTemplate(file_path, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            styleN = styles['Normal']
            
            elements.append(Paragraph("<b>DEBIT NOTE / PURCHASE RETURN</b>", styles['Title']))
            elements.append(Spacer(1, 12))
            
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT p_name, location, phone FROM Pharmacy LIMIT 1")
            pharma = cursor.fetchone()
            
            p_name = pharma[0] if pharma else "My Pharmacy"
            p_loc = pharma[1] if pharma else ""
            p_phone = pharma[2] if pharma else ""
            
            if not supplier_name:
                cursor.execute("SELECT Sup_name, address FROM Supplier WHERE Supp_id=?", (supp_id,))
                sup = cursor.fetchone()
                supplier_name = sup[0] if sup else "Unknown"
                supplier_addr = sup[1] if sup else ""
            conn.close()

            data_info = [
                [Paragraph(f"<b>From:</b> {p_name}", styleN), Paragraph(f"<b>To:</b> {supplier_name}", styleN)],
                [Paragraph(f"{p_loc}", styleN), Paragraph(f"{supplier_addr}", styleN)],
                [Paragraph(f"<b>Phone:</b> {p_phone}", styleN), Paragraph(f"<b>Return #:</b> {return_no}", styleN)],
                ["", Paragraph(f"<b>Date:</b> {date}", styleN)]
            ]
            
            t_info = Table(data_info, colWidths=[300, 200])
            t_info.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
            elements.append(t_info)
            elements.append(Spacer(1, 20))
            
            data_items = [["Product Name", "Batch", "Expiry", "Qty (Strips/Tabs)", "Amount (Rs)"]]
            for item in items:
                p_name = item.get('prod_name') if 'prod_name' in item else self.get_prod_name(item['prod_id'])
                
                tps = int(item['tps']) if item['tps'] else 1
                units = item['qty_units']
                if tps > 1:
                    qty_str = f"{units // tps}s + {units % tps}t"
                else:
                    qty_str = str(units)
                
                data_items.append([p_name, item['batch'], item['exp'], qty_str, f"{item['amt']:.2f}"])
            
            data_items.append(["", "", "", "TOTAL", f"{total:.2f}"])

            t_items = Table(data_items, colWidths=[200, 100, 80, 100, 70])
            t_items.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), 
                ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), 
            ]))
            elements.append(t_items)
            
            elements.append(Spacer(1, 30))
            elements.append(Paragraph("Authorized Signature: _______________________", styles['Normal']))

            doc.build(elements)
            QMessageBox.information(self, "PDF Saved", f"Debit note saved to {file_path}")
            
            if os.name == 'nt':
                os.startfile(file_path)
            
        except Exception as e:
            QMessageBox.critical(self, "PDF Error", str(e))

    def get_prod_name(self, prod_id):
        for pid, name in self.products_cache:
            if pid == prod_id: return name
        return "Unknown"

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    database.init_db()
    window = PurchaseReturnInterface()
    window.show()
    sys.exit(app.exec())