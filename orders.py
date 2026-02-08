import sys
import sqlite3
import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QFrame, QMessageBox, QTabWidget, QCheckBox,
    QComboBox, QSpinBox, QAbstractItemView, QCompleter, 
    QListView, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

# PDF Imports
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

import database

# --- COLORS ---
COLOR_BG = "#f8f9fa"
COLOR_WHITE = "#ffffff"
COLOR_NAVBAR = "#0d47a1"
COLOR_TEXT = "#000000"
COLOR_ACCENT = "#198754" 
COLOR_DANGER = "#dc3545" 
COLOR_BORDER = "#dee2e6"

STYLE_SHEET = f"""
    /* GLOBAL: Force text to black and set font */
    * {{ color: #000000; font-family: 'Segoe UI', Arial, sans-serif; }}
    
    QWidget {{ background-color: {COLOR_BG}; }}
    
    /* Force Labels and specific widgets to use black text */
    QLabel, QCheckBox, QRadioButton, QTabWidget {{ color: #000000; }}

    /* --- INPUTS (Search, Filter, Qty) --- */
    /* Explicitly set background to white and text to black */
    QLineEdit, QComboBox, QSpinBox {{
        border: 1px solid #ced4da; 
        border-radius: 4px; 
        padding: 5px; 
        font-size: 14px;
        background-color: #ffffff; 
        color: #000000; 
    }}
    
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border: 1px solid {COLOR_NAVBAR}; }}

    QListView {{ background-color: {COLOR_WHITE}; color: #000000; outline: none; }}

    /* --- TABLE STYLING --- */
    QTableWidget {{ 
        background-color: #ffffff; 
        gridline-color: #dee2e6; 
        color: #000000; 
        border: 1px solid #dee2e6; 
    }}
    
    QTableWidget::item {{ color: #000000; }}
    
    /* Selected row styling */
    QTableWidget::item:selected {{ 
        background-color: #d0e1f5; 
        color: #000000; 
        border: 1px solid #0d47a1; 
    }}
    
    /* --- TABLE HEADERS (The invisible part in your screenshot) --- */
    QHeaderView::section {{
        background-color: #e9ecef; 
        color: #000000; /* Force Black Text Here */
        padding: 5px;
        border: 1px solid #d0d0d0; 
        font-weight: bold;
    }}
    
    QSplitter::handle {{ background-color: {COLOR_BORDER}; }}

    /* --- CHECKBOX STYLES (From previous step) --- */
    QTableView::indicator, QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 3px;
        border: 2px solid #555555;
        background-color: #f0f0f0;
    }}

    QTableView::indicator:unchecked, QCheckBox::indicator:unchecked {{
        background-color: #f0f0f0;
        border: 2px solid #555555;
    }}

    QTableView::indicator:unchecked:hover, QCheckBox::indicator:unchecked:hover {{
        background-color: #ffffff;
        border: 2px solid {COLOR_NAVBAR};
    }}

    QTableView::indicator:checked, QCheckBox::indicator:checked {{
        background-color: {COLOR_NAVBAR};
        border: 2px solid {COLOR_NAVBAR};
        image: none;
    }}
"""

STYLE_BTN_PRIMARY = f"""
    QPushButton {{
        background-color: {COLOR_NAVBAR}; color: white; border-radius: 5px;
        padding: 8px 15px; font-weight: bold; font-size: 14px;
    }}
    QPushButton:hover {{ background-color: #0a3675; }}
"""

STYLE_BTN_SUCCESS = f"""
    QPushButton {{
        background-color: {COLOR_ACCENT}; color: white; border-radius: 5px;
        padding: 8px 15px; font-weight: bold;
    }}
    QPushButton:hover {{ background-color: #146c43; }}
"""

STYLE_BTN_DANGER = f"""
    QPushButton {{
        background-color: {COLOR_DANGER}; color: white; border-radius: 5px;
        padding: 8px 15px; font-weight: bold;
    }}
    QPushButton:hover {{ background-color: #b02a37; }}
"""

class OrdersInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Purchase Orders")
        self.setStyleSheet(STYLE_SHEET)
        
        self.order_cart = {} 
        self.current_po_id = None 
        self.selected_history_po_id = None 
        
        # Tracks items selected in the Alerts tab
        self.selected_alerts = set() 

        self.init_ui()
        self.load_alerts()
        self.load_order_history()

    def create_item(self, text):
        """Creates a table item forcing black text."""
        item = QTableWidgetItem(str(text))
        item.setForeground(QColor("black"))
        return item

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid #dee2e6; background: {COLOR_WHITE}; border-radius: 5px; }}
            QTabBar::tab {{
                background: #e9ecef; padding: 10px 20px; margin-right: 2px; color: {COLOR_TEXT}; 
            }}
            QTabBar::tab:selected {{ 
                background: {COLOR_WHITE}; border-bottom: 2px solid {COLOR_NAVBAR}; 
                font-weight: bold; color: {COLOR_NAVBAR};
            }}
        """)
        
        self.tab_alerts = QWidget()
        self.tab_create = QWidget()
        self.tab_history = QWidget()
        
        self.tabs.addTab(self.tab_alerts, "Stock Alerts")
        self.tabs.addTab(self.tab_create, "Create/Edit Order")
        self.tabs.addTab(self.tab_history, "Order History")
        
        main_layout.addWidget(self.tabs)

        self.setup_tab_alerts()
        self.setup_tab_create()
        self.setup_tab_history()

    # =========================================================
    # TAB 1: STOCK ALERTS (FIXED SELECTION)
    # =========================================================
    def setup_tab_alerts(self):
        layout = QVBoxLayout(self.tab_alerts)
        
        # 1. Filters
        filter_layout = QHBoxLayout()
        self.txt_search_alert = QLineEdit()
        self.txt_search_alert.setPlaceholderText("🔍 Search Medicine...")
        self.txt_search_alert.textChanged.connect(self.load_alerts)
        
        self.combo_type_filter = QComboBox()
        self.combo_type_filter.setView(QListView()) 
        self.combo_type_filter.addItem("All Types")
        self.combo_type_filter.addItems(["Tablet", "Capsule", "Syrup", "Injection", "Cream", "Ointment", "Drops", "Personal Care & Wellness", "Spray", "Powder", "Medical Devices"])
        self.combo_type_filter.currentIndexChanged.connect(self.load_alerts)

        btn_add_selected = QPushButton("Add Selected to Order List")
        btn_add_selected.setStyleSheet(STYLE_BTN_PRIMARY)
        btn_add_selected.clicked.connect(self.add_alerts_to_cart)

        filter_layout.addWidget(self.txt_search_alert)
        filter_layout.addWidget(self.combo_type_filter)
        filter_layout.addWidget(btn_add_selected)
        layout.addLayout(filter_layout)

        # 2. Table
        self.alert_table = QTableWidget()
        self.alert_table.setColumnCount(6)
        self.alert_table.setHorizontalHeaderLabels(["Select", "Medicine Name", "Type", "Stock Qty", "Expiry Date", "Status"])
        
        # COLUMN SIZING
        self.alert_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.alert_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.alert_table.setColumnWidth(0, 60)
        
        self.alert_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.alert_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        # --- FIX: Connect the table's native itemChanged signal ---
        self.alert_table.itemChanged.connect(self.on_alert_item_changed)
        
        layout.addWidget(self.alert_table)

    def load_alerts(self):
        search = self.txt_search_alert.text().lower()
        med_type = self.combo_type_filter.currentText()
        
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Med_name, Type, SUM(Quantity), MIN(EXP_Date) FROM Medicine GROUP BY Med_name")
        rows = cursor.fetchall()
        conn.close()

        # Block signals isn't strictly necessary for setCellWidget, but good practice
        self.alert_table.blockSignals(True)
        self.alert_table.setRowCount(0)
        self.selected_alerts.clear() 

        today = datetime.date.today()
        row_idx = 0
        
        for name, m_type, qty, exp_date_str in rows:
            if search and search not in name.lower(): continue
            if med_type != "All Types" and med_type.lower() != str(m_type).lower(): continue

            is_low_stock = (qty is not None and qty < 20)
            is_expiring = False
            try:
                if exp_date_str:
                    exp_date = datetime.datetime.strptime(exp_date_str, "%Y-%m-%d").date()
                    days_left = (exp_date - today).days
                    if days_left < 120: is_expiring = True
            except: pass

            if is_low_stock or is_expiring:
                self.alert_table.insertRow(row_idx)
                
                # --- NEW CENTERED CHECKBOX LOGIC ---
                # 1. Create a container widget to hold the checkbox
                cell_widget = QWidget()
                layout = QHBoxLayout(cell_widget)
                layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.setContentsMargins(0, 0, 0, 0)
                
                # 2. Create the checkbox
                chk = QCheckBox()
                chk.setStyleSheet("margin-left:5px;") # Optional tweak
                
                # 3. Connect directly to a specific handler, passing the medicine name
                # This removes the need to look up the row later
                chk.stateChanged.connect(lambda state, n=name: self.on_alert_checkbox_toggled(state, n))
                
                layout.addWidget(chk)
                
                # 4. Set the widget into the cell
                self.alert_table.setCellWidget(row_idx, 0, cell_widget)
                # -----------------------------------
                
                # Add text items
                self.alert_table.setItem(row_idx, 1, self.create_item(name))
                self.alert_table.setItem(row_idx, 2, self.create_item(str(m_type)))
                self.alert_table.setItem(row_idx, 3, self.create_item(str(qty)))
                self.alert_table.setItem(row_idx, 4, self.create_item(str(exp_date_str)))
                
                status = []
                if is_low_stock: status.append("Low Stock")
                if is_expiring: status.append("Expiring")
                
                lbl_status = QTableWidgetItem(", ".join(status))
                lbl_status.setForeground(QColor(COLOR_DANGER)) 
                lbl_status.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                self.alert_table.setItem(row_idx, 5, lbl_status)
                
                row_idx += 1
        
        self.alert_table.blockSignals(False)
    
    def on_alert_checkbox_toggled(self, state, med_name):
        """Handle clicks on the centered checkbox widget"""
        # state 2 is Checked, 0 is Unchecked
        if state == 2: 
            self.selected_alerts.add(med_name)
        else:
            if med_name in self.selected_alerts:
                self.selected_alerts.remove(med_name)

    def on_alert_item_changed(self, item):
        """Handle clicks on the native checkbox (Column 0)"""
        if item.column() == 0:
            row = item.row()
            # Retrieve the medicine name from Column 1
            name_item = self.alert_table.item(row, 1)
            if not name_item:
                return
            
            name = name_item.text()
            
            if item.checkState() == Qt.CheckState.Checked:
                self.selected_alerts.add(name)
            else:
                if name in self.selected_alerts:
                    self.selected_alerts.remove(name)

    def add_alerts_to_cart(self):
        """Add items tracked in selected_alerts to the order cart"""
        count = 0
        if not self.selected_alerts:
            QMessageBox.warning(self, "Selection", "No items selected.")
            return

        for name in self.selected_alerts:
            if name not in self.order_cart:
                self.order_cart[name] = 50 # Default quantity
                count += 1
        
        if count > 0:
            self.refresh_cart_table()
            self.tabs.setCurrentIndex(1) # Switch to Create Order tab
            
            # Reset selections visually and in data
            self.selected_alerts.clear()
            self.load_alerts() # Reload to uncheck boxes
            
            QMessageBox.information(self, "Added", f"{count} items added to order list.")
        else:
            QMessageBox.information(self, "Info", "Selected items are already in the order list.")

    # =========================================================
    # TAB 2: CREATE / EDIT ORDER
    # =========================================================
    def setup_tab_create(self):
        layout = QVBoxLayout(self.tab_create)
        
        # 1. Supplier Details
        grp_supp = QFrame()
        grp_supp.setStyleSheet(f"background: {COLOR_WHITE}; border: 1px solid #dee2e6; border-radius: 5px;")
        supp_layout = QHBoxLayout(grp_supp)
        
        self.txt_supp_name = QLineEdit()
        self.txt_supp_name.setPlaceholderText("Supplier Name (Type to Search)")
        self.setup_supplier_completer() 
        self.txt_supp_name.editingFinished.connect(self.fill_supplier_details)

        self.txt_supp_phone = QLineEdit()
        self.txt_supp_phone.setPlaceholderText("Phone Number")

        self.txt_supp_email = QLineEdit()
        self.txt_supp_email.setPlaceholderText("Email Address")

        supp_layout.addWidget(QLabel("Supplier:"))
        supp_layout.addWidget(self.txt_supp_name)
        supp_layout.addWidget(self.txt_supp_phone)
        supp_layout.addWidget(self.txt_supp_email)
        
        layout.addWidget(grp_supp)

        # 2. Add Manual Item
        grp_add = QHBoxLayout()
        self.txt_new_item = QLineEdit()
        self.txt_new_item.setPlaceholderText("Add New Medicine Name...")
        
        self.spin_new_qty = QSpinBox()
        self.spin_new_qty.setRange(1, 10000)
        self.spin_new_qty.setValue(50)
        
        btn_add_manual = QPushButton("+ Add Item")
        btn_add_manual.setStyleSheet(STYLE_BTN_PRIMARY)
        btn_add_manual.clicked.connect(self.add_manual_item)
        
        grp_add.addWidget(self.txt_new_item)
        grp_add.addWidget(QLabel("Qty:"))
        grp_add.addWidget(self.spin_new_qty)
        grp_add.addWidget(btn_add_manual)
        
        layout.addLayout(grp_add)

        # 3. Order List Table
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(3)
        self.cart_table.setHorizontalHeaderLabels(["Medicine Name", "Quantity", "Action"])
        
        header = self.cart_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)           
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)             
        self.cart_table.setColumnWidth(1, 100)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  
        
        layout.addWidget(self.cart_table)

        # 4. Save Button
        self.btn_save = QPushButton("Save Order and Generate PDF")
        self.btn_save.setFixedHeight(45)
        self.btn_save.setStyleSheet(STYLE_BTN_SUCCESS)
        self.btn_save.clicked.connect(self.save_order)
        layout.addWidget(self.btn_save)
        
        # Cancel Edit Button
        self.btn_cancel_edit = QPushButton("Cancel Editing")
        self.btn_cancel_edit.setStyleSheet(f"background-color: #6c757d; color: white; padding: 8px;")
        self.btn_cancel_edit.clicked.connect(self.clear_form)
        self.btn_cancel_edit.setVisible(False)
        layout.addWidget(self.btn_cancel_edit)

    def setup_supplier_completer(self):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Sup_name FROM Supplier")
        suppliers = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        completer = QCompleter(suppliers)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setPopup(QListView())
        self.txt_supp_name.setCompleter(completer)

    def fill_supplier_details(self):
        name = self.txt_supp_name.text().strip()
        if not name: return
        
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT contact, email FROM Supplier WHERE Sup_name=?", (name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            self.txt_supp_phone.setText(row[0])
            self.txt_supp_email.setText(row[1])

    def add_manual_item(self):
        name = self.txt_new_item.text().strip()
        qty = self.spin_new_qty.value()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a medicine name.")
            return
        self.order_cart[name] = qty
        self.txt_new_item.clear()
        self.spin_new_qty.setValue(50)
        self.refresh_cart_table()

    def refresh_cart_table(self):
        self.cart_table.setRowCount(0)
        for i, (name, qty) in enumerate(self.order_cart.items()):
            self.cart_table.insertRow(i)
            self.cart_table.setItem(i, 0, self.create_item(name))
            
            sb = QSpinBox()
            sb.setRange(1, 100000)
            sb.setValue(qty)
            sb.valueChanged.connect(lambda val, n=name: self.update_cart_qty(n, val))
            self.cart_table.setCellWidget(i, 1, sb)
            
            btn_del = QPushButton("Remove")
            btn_del.setStyleSheet(f"color: white; background-color: {COLOR_DANGER}; border-radius: 4px;")
            btn_del.clicked.connect(lambda _, n=name: self.remove_from_cart(n))
            self.cart_table.setCellWidget(i, 2, btn_del)

    def update_cart_qty(self, name, new_qty):
        self.order_cart[name] = new_qty

    def remove_from_cart(self, name):
        if name in self.order_cart:
            del self.order_cart[name]
            self.refresh_cart_table()

    def clear_form(self):
        self.order_cart.clear()
        self.refresh_cart_table()
        self.txt_supp_name.clear()
        self.txt_supp_phone.clear()
        self.txt_supp_email.clear()
        self.current_po_id = None
        self.btn_save.setText("💾 Save Order & Generate PDF")
        self.btn_cancel_edit.setVisible(False)

    def save_order(self):
        supp_name = self.txt_supp_name.text().strip()
        phone = self.txt_supp_phone.text().strip()
        email = self.txt_supp_email.text().strip()
        
        if not supp_name:
            QMessageBox.warning(self, "Error", "Supplier Name is required!")
            return
        if not self.order_cart:
            QMessageBox.warning(self, "Error", "Order list is empty!")
            return

        conn = database.get_connection()
        cursor = conn.cursor()
        try:
            # Handle Supplier
            cursor.execute("SELECT Supp_id FROM Supplier WHERE Sup_name=?", (supp_name,))
            res = cursor.fetchone()
            if res:
                supp_id = res[0]
                cursor.execute("UPDATE Supplier SET contact=?, email=? WHERE Supp_id=?", 
                               (phone, email, supp_id))
            else:
                cursor.execute("INSERT INTO Supplier (Sup_name, contact, email) VALUES (?, ?, ?)", 
                               (supp_name, phone, email))
                supp_id = cursor.lastrowid

            today_str = datetime.date.today().strftime("%Y-%m-%d")

            if self.current_po_id:
                # Update existing order
                po_id = self.current_po_id
                cursor.execute("UPDATE Purchase_order SET supp_id=?, status='Updated' WHERE po_id=?", 
                               (supp_id, po_id))
                cursor.execute("DELETE FROM PO_item WHERE po_id=?", (po_id,))
                msg_text = f"Order #{po_id} Updated Successfully!"
            else:
                # Create new order
                cursor.execute("INSERT INTO Purchase_order (order_date, supp_id, status) VALUES (?, ?, ?)", 
                               (today_str, supp_id, "Created"))
                po_id = cursor.lastrowid
                msg_text = f"Order #{po_id} Created Successfully!"
            
            for name, qty in self.order_cart.items():
                cursor.execute("SELECT Med_id FROM Medicine WHERE Med_name=?", (name,))
                med_res = cursor.fetchone()
                if med_res:
                    med_id = med_res[0]
                else:
                    cursor.execute("INSERT INTO Medicine (Med_name, Quantity) VALUES (?, 0)", (name,))
                    med_id = cursor.lastrowid
                
                cursor.execute("INSERT INTO PO_item (po_id, Med_id, Quantity) VALUES (?, ?, ?)", 
                               (po_id, med_id, qty))
            
            conn.commit()
            self.generate_pdf(po_id, supp_name, phone, email, today_str)
            QMessageBox.information(self, "Success", msg_text)
            self.clear_form()
            self.load_order_history()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()

    def get_pharmacy_details(self):
        try:
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT p_name, location, phone, email FROM Pharmacy LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            if row and row[0]:
                return row[0], row[1], row[2], row[3]
        except Exception as e:
            print("DB Error fetching pharmacy:", e)
        return "MY PHARMACY", "City, Country", "9999999999", "admin@pharma.com"

    def generate_pdf(self, po_id, s_name, s_phone, s_email, date_str):
        filename = f"Order_{po_id}_{s_name}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        p_name, p_addr, p_phone, p_email = self.get_pharmacy_details()

        elements.append(Paragraph(f"<b>{p_name}</b>", styles['Title']))
        elements.append(Paragraph(p_addr, styles['Normal']))
        elements.append(Paragraph(f"Contact: {p_phone} | Email: {p_email}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        elements.append(Paragraph(f"<b>PURCHASE ORDER #{po_id}</b>", styles['Heading3']))
        elements.append(Paragraph(f"<b>Date:</b> {date_str}", styles['Normal']))
        elements.append(Spacer(1, 10))
        
        elements.append(Paragraph("<b>Supplier Details:</b>", styles['Heading3']))
        elements.append(Paragraph(f"Name: {s_name}", styles['Normal']))
        elements.append(Paragraph(f"Phone: {s_phone}", styles['Normal']))
        elements.append(Paragraph(f"Email: {s_email}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        data = [["Medicine Name", "Quantity"]]
        for name, qty in self.order_cart.items():
            data.append([name, str(qty)])
            
        table = Table(data, colWidths=[300, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
        try:
            doc.build(elements)
        except PermissionError:
            QMessageBox.warning(self, "PDF Error", "Close the PDF file if it is open and try again.")

    # =========================================================
    # TAB 3: ORDER HISTORY (MASTER-DETAIL)
    # =========================================================
    def setup_tab_history(self):
        layout = QVBoxLayout(self.tab_history)
        
        # 1. Top Bar
        top_bar = QHBoxLayout()
        btn_refresh = QPushButton("⟳ Refresh History")
        btn_refresh.setFixedWidth(150)
        btn_refresh.setStyleSheet(STYLE_BTN_PRIMARY)
        btn_refresh.clicked.connect(self.load_order_history)
        top_bar.addWidget(btn_refresh)
        top_bar.addStretch()
        layout.addLayout(top_bar)
        
        # 2. Splitter for Master-Detail View
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)

        # LEFT SIDE: Order List Table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Order ID", "Supplier", "Date", "Status"])
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.cellClicked.connect(self.on_history_row_clicked)
        
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0,0,0,0)
        left_layout.addWidget(self.history_table)
        
        # RIGHT SIDE: Preview Panel
        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet(f"background: {COLOR_WHITE}; border-left: 1px solid {COLOR_BORDER};")
        self.preview_frame.setVisible(False)
        
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(15, 15, 15, 15)
        
        # Details Header
        self.lbl_prev_id = QLabel("Order #")
        self.lbl_prev_id.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_NAVBAR};")
        
        self.lbl_prev_supp = QLabel("Supplier: -")
        self.lbl_prev_date = QLabel("Date: -")
        self.combo_prev_status = QComboBox()
        self.combo_prev_status.setView(QListView())
        self.combo_prev_status.addItems(["Created", "Shared", "Arrived", "Cancelled"])
        self.combo_prev_status.currentIndexChanged.connect(self.update_history_status)

        preview_layout.addWidget(self.lbl_prev_id)
        preview_layout.addWidget(self.lbl_prev_supp)
        preview_layout.addWidget(self.lbl_prev_date)
        preview_layout.addWidget(QLabel("Status:"))
        preview_layout.addWidget(self.combo_prev_status)
        
        preview_layout.addSpacing(10)
        
        # Items Table in Preview
        self.prev_items_table = QTableWidget()
        self.prev_items_table.setColumnCount(2)
        self.prev_items_table.setHorizontalHeaderLabels(["Medicine", "Qty"])
        self.prev_items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.prev_items_table.verticalHeader().setVisible(False)
        preview_layout.addWidget(self.prev_items_table)
        
        # Action Buttons (Edit / Delete)
        btn_box = QHBoxLayout()
        self.btn_edit_order = QPushButton("Edit Order")
        self.btn_edit_order.setStyleSheet(STYLE_BTN_PRIMARY)
        self.btn_edit_order.clicked.connect(self.edit_selected_order)
        
        self.btn_del_order = QPushButton("Delete Order")
        self.btn_del_order.setStyleSheet(STYLE_BTN_DANGER)
        self.btn_del_order.clicked.connect(self.delete_selected_order)
        
        btn_box.addWidget(self.btn_edit_order)
        btn_box.addWidget(self.btn_del_order)
        preview_layout.addLayout(btn_box)

        splitter.addWidget(left_frame)
        splitter.addWidget(self.preview_frame)
        splitter.setSizes([600, 300]) # Initial sizes
        
        layout.addWidget(splitter)

    def load_order_history(self):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT po.po_id, s.Sup_name, po.order_date, po.status 
            FROM Purchase_order po
            JOIN Supplier s ON po.supp_id = s.Supp_id
            ORDER BY po.po_id DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        self.history_table.setRowCount(0)
        self.preview_frame.setVisible(False)
        self.selected_history_po_id = None
        
        for i, (pid, sname, date, status) in enumerate(rows):
            self.history_table.insertRow(i)
            self.history_table.setItem(i, 0, self.create_item(str(pid)))
            self.history_table.setItem(i, 1, self.create_item(sname))
            self.history_table.setItem(i, 2, self.create_item(date))
            self.history_table.setItem(i, 3, self.create_item(status))

    def on_history_row_clicked(self, row, col):
        po_id = self.history_table.item(row, 0).text()
        supp = self.history_table.item(row, 1).text()
        date = self.history_table.item(row, 2).text()
        status = self.history_table.item(row, 3).text()
        
        self.selected_history_po_id = int(po_id)
        
        # Update Preview Labels
        self.lbl_prev_id.setText(f"Order #{po_id}")
        self.lbl_prev_supp.setText(f"Supplier: {supp}")
        self.lbl_prev_date.setText(f"Date: {date}")
        self.combo_prev_status.blockSignals(True)
        self.combo_prev_status.setCurrentText(status)
        self.combo_prev_status.blockSignals(False)
        
        # Load Items for Preview
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.Med_name, pi.Quantity 
            FROM PO_item pi 
            JOIN Medicine m ON pi.Med_id = m.Med_id
            WHERE pi.po_id = ?
        """, (po_id,))
        items = cursor.fetchall()
        conn.close()
        
        self.prev_items_table.setRowCount(0)
        for i, (m_name, qty) in enumerate(items):
            self.prev_items_table.insertRow(i)
            self.prev_items_table.setItem(i, 0, self.create_item(m_name))
            self.prev_items_table.setItem(i, 1, self.create_item(str(qty)))
            
        self.preview_frame.setVisible(True)

    def update_history_status(self):
        if not self.selected_history_po_id: return
        new_status = self.combo_prev_status.currentText()
        
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Purchase_order SET status=? WHERE po_id=?", 
                       (new_status, self.selected_history_po_id))
        conn.commit()
        conn.close()
        
        # Update table text without full reload
        items = self.history_table.findItems(str(self.selected_history_po_id), Qt.MatchFlag.MatchExactly)
        if items:
            row = items[0].row()
            self.history_table.setItem(row, 3, self.create_item(new_status))

    def edit_selected_order(self):
        if not self.selected_history_po_id: return
        
        po_id = self.selected_history_po_id
        
        # 1. Fetch Details to populate Tab 2
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # Supplier Info
        cursor.execute("""
            SELECT s.Sup_name, s.contact, s.email 
            FROM Purchase_order po
            JOIN Supplier s ON po.supp_id = s.Supp_id
            WHERE po.po_id = ?
        """, (po_id,))
        supp_row = cursor.fetchone()
        
        # Items
        cursor.execute("""
            SELECT m.Med_name, pi.Quantity 
            FROM PO_item pi 
            JOIN Medicine m ON pi.Med_id = m.Med_id
            WHERE pi.po_id = ?
        """, (po_id,))
        item_rows = cursor.fetchall()
        conn.close()
        
        if not supp_row: return

        # 2. Switch to Create Tab and Fill Data
        self.clear_form() # Reset first
        
        self.current_po_id = po_id # MARK AS EDIT MODE
        self.btn_save.setText(f"Update Order #{po_id}")
        self.btn_cancel_edit.setVisible(True)
        
        self.txt_supp_name.setText(supp_row[0])
        self.txt_supp_phone.setText(supp_row[1])
        self.txt_supp_email.setText(supp_row[2])
        
        for name, qty in item_rows:
            self.order_cart[name] = qty
            
        self.refresh_cart_table()
        self.tabs.setCurrentIndex(1) # Switch tab
        
    def delete_selected_order(self):
        if not self.selected_history_po_id: return
        
        ret = QMessageBox.question(self, "Confirm", "Delete this order? This cannot be undone.", 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ret == QMessageBox.StandardButton.Yes:
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM PO_item WHERE po_id=?", (self.selected_history_po_id,))
            cursor.execute("DELETE FROM Purchase_order WHERE po_id=?", (self.selected_history_po_id,))
            conn.commit()
            conn.close()
            self.load_order_history()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = OrdersInterface()
    window.resize(1000, 650)
    window.show()
    sys.exit(app.exec())