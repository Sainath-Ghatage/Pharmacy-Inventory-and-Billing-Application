import sys
import sqlite3
import datetime
import os
import smtplib
import webbrowser
import urllib.parse
import time
# --- IMPORTS FOR FILE HIGHLIGHTING ---
if sys.platform == 'win32':
    import subprocess
    try:
        import pyautogui
    except ImportError:
        print("PyAutoGUI not installed. Automated pasting won't work.")
# ------------------------------------

from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QFrame, QMessageBox, QTabWidget, QCheckBox,
    QComboBox, QSpinBox, QAbstractItemView, QCompleter, 
    QListView, QSplitter, QGroupBox, QDialog
)
from PyQt6.QtCore import Qt, QUrl, QMimeData
from PyQt6.QtGui import QFont, QColor

# PDF Imports
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
except ImportError:
    print("ReportLab is missing. Run: pip install reportlab")

import database

# --- COLORS ---
COLOR_BG = "#f8f9fa"
COLOR_WHITE = "#ffffff"
COLOR_NAVBAR = "#0d47a1"
COLOR_TEXT = "#000000"
COLOR_ACCENT = "#198754" 
COLOR_DANGER = "#dc3545" 
COLOR_BORDER = "#dee2e6"

# Removed the global QPushButton { color: white; } so we can control text color manually
STYLE_SHEET = f"""
    QWidget {{ font-family: 'Segoe UI', Arial, sans-serif; color: #000000; background-color: {COLOR_BG}; }}
    QLabel, QCheckBox, QRadioButton, QTabWidget {{ color: #000000; background: transparent; }}
    QLineEdit, QComboBox, QSpinBox {{
        border: 1px solid #ced4da; border-radius: 4px; padding: 5px; 
        font-size: 14px; background-color: #ffffff; color: #000000; 
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border: 1px solid {COLOR_NAVBAR}; }}
    QListView {{ background-color: {COLOR_WHITE}; color: #000000; outline: none; }}
    QTableWidget {{ background-color: #ffffff; gridline-color: #dee2e6; color: #000000; border: 1px solid #dee2e6; }}
    QTableWidget::item {{ color: #000000; padding: 5px; }}
    QTableWidget::item:selected {{ background-color: #d0e1f5; color: #000000; border: none; }}
    QHeaderView::section {{ background-color: #e9ecef; color: #000000; padding: 5px; border: 1px solid #d0d0d0; font-weight: bold; }}
    QSplitter::handle {{ background-color: {COLOR_BORDER}; }}
    QGroupBox {{ font-weight: bold; border: 1px solid #ccc; margin-top: 10px; padding-top: 15px; border-radius: 5px; background: transparent; }} 
    QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; color: {COLOR_NAVBAR}; }}
"""

class SendMethodDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Send Purchase Order")
        # INCREASED WIDTH to 600 so "Skip" is never hidden
        self.setFixedSize(600, 150) 
        self.setStyleSheet(STYLE_SHEET)
        self.choice = "NONE"

        layout = QVBoxLayout(self)
        lbl = QLabel("Order saved successfully!\nHow would you like to send the PO to the supplier?")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(lbl)

        btn_layout = QHBoxLayout()
        
        # CHANGED COLORS: Lighter backgrounds with pure BLACK text
        btn_email = QPushButton("📧 Email")
        btn_email.setStyleSheet("background-color: #b3d4ff; color: black; padding: 10px; border-radius: 4px; font-weight: bold; font-size: 14px;")
        
        btn_wa = QPushButton("💬 WhatsApp")
        btn_wa.setStyleSheet("background-color: #b3ffc6; color: black; padding: 10px; border-radius: 4px; font-weight: bold; font-size: 14px;")
        
        btn_both = QPushButton("📧 + 💬 Both")
        btn_both.setStyleSheet("background-color: #85e0a3; color: black; padding: 10px; border-radius: 4px; font-weight: bold; font-size: 14px;")
        
        btn_skip = QPushButton("Skip / Don't Send")
        btn_skip.setStyleSheet("background-color: #d9d9d9; color: black; padding: 10px; border-radius: 4px; font-weight: bold; font-size: 14px;")

        btn_email.clicked.connect(lambda: self.make_choice("EMAIL"))
        btn_wa.clicked.connect(lambda: self.make_choice("WHATSAPP"))
        btn_both.clicked.connect(lambda: self.make_choice("BOTH"))
        btn_skip.clicked.connect(lambda: self.make_choice("NONE"))

        btn_layout.addWidget(btn_email)
        btn_layout.addWidget(btn_wa)
        btn_layout.addWidget(btn_both)
        btn_layout.addWidget(btn_skip)

        layout.addLayout(btn_layout)

    def make_choice(self, choice):
        self.choice = choice
        self.accept()

class OrdersInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Purchase Orders")
        self.setStyleSheet(STYLE_SHEET)
        
        self.order_cart = {} 
        self.current_po_id = None 
        self.selected_alerts = set() 

        self.init_ui()
        self.load_alerts()
        self.load_order_history()

    def create_item(self, text):
        item = QTableWidgetItem(str(text))
        item.setForeground(QColor("black"))
        return item

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid #dee2e6; background: {COLOR_WHITE}; border-radius: 5px; }}
            QTabBar::tab {{ background: #e9ecef; padding: 10px 20px; margin-right: 2px; color: {COLOR_TEXT}; }}
            QTabBar::tab:selected {{ background: {COLOR_WHITE}; border-bottom: 2px solid {COLOR_NAVBAR}; font-weight: bold; color: {COLOR_NAVBAR}; }}
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

    def setup_tab_alerts(self):
        layout = QVBoxLayout(self.tab_alerts)
        filter_layout = QHBoxLayout()
        self.txt_search_alert = QLineEdit()
        self.txt_search_alert.setPlaceholderText("🔍 Search Product...")
        self.txt_search_alert.textChanged.connect(self.load_alerts)
        
        self.combo_type_filter = QComboBox()
        self.combo_type_filter.setView(QListView()) 
        self.combo_type_filter.addItem("All Types")
        self.combo_type_filter.addItems(["Tablet", "Capsule", "Syrup", "Injection", "Cream", 
            "Ointment", "Drops", "Personal Care & Wellness", "Spray", "Powder", "Medical Devices"])
        self.combo_type_filter.currentIndexChanged.connect(self.load_alerts)

        btn_add_selected = QPushButton("Add Selected to Order List")
        btn_add_selected.setStyleSheet(f"background-color: {COLOR_NAVBAR}; color: white; padding: 8px; font-weight: bold;")
        btn_add_selected.clicked.connect(self.add_alerts_to_cart)

        filter_layout.addWidget(self.txt_search_alert)
        filter_layout.addWidget(self.combo_type_filter)
        filter_layout.addWidget(btn_add_selected)
        layout.addLayout(filter_layout)

        self.alert_table = QTableWidget()
        self.alert_table.setColumnCount(6)
        self.alert_table.setHorizontalHeaderLabels(["Select", "Product Name", "Type", "Stock Qty", "Expiry Date", "Status"])
        self.alert_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.alert_table.setColumnWidth(0, 60)
        self.alert_table.verticalHeader().setDefaultSectionSize(45) 
        self.alert_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.alert_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.alert_table)

    def load_alerts(self):
        search = self.txt_search_alert.text().lower()
        prod_type = self.combo_type_filter.currentText()
        
        conn = database.get_connection()
        cursor = conn.cursor()
        query = """
            SELECT d.prod_name, d.type, SUM(s.quantity), MIN(s.exp_date)
            FROM Product_Details d LEFT JOIN Product_Stock s ON d.prod_id = s.prod_id GROUP BY d.prod_id
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        self.alert_table.setRowCount(0)
        self.selected_alerts.clear() 
        today = datetime.date.today()
        row_idx = 0
        
        for name, m_type, qty, exp_date_str in rows:
            if not name: continue
            if search and search not in name.lower(): continue
            if prod_type != "All Types" and prod_type.lower() != str(m_type).lower(): continue

            qty = qty if qty is not None else 0
            is_low_stock = (qty < 20)
            is_expiring = False
            
            try:
                if exp_date_str:
                    if "/" in exp_date_str:
                          m, y = map(int, exp_date_str.split('/'))
                          exp_date = datetime.date(2000+y, m, 1)
                    else:
                          exp_date = datetime.datetime.strptime(exp_date_str, "%Y-%m-%d").date()
                    if (exp_date - today).days < 120: is_expiring = True
            except: pass

            if is_low_stock or is_expiring:
                self.alert_table.insertRow(row_idx)
                cell_widget = QWidget()
                layout = QHBoxLayout(cell_widget)
                layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.setContentsMargins(0, 0, 0, 0)
                
                chk = QCheckBox()
                chk.clicked.connect(lambda checked, n=name, r=row_idx: self.toggle_alert_selection(checked, n, r))
                
                layout.addWidget(chk)
                self.alert_table.setCellWidget(row_idx, 0, cell_widget)
                self.alert_table.setItem(row_idx, 1, self.create_item(name))
                self.alert_table.setItem(row_idx, 2, self.create_item(str(m_type)))
                self.alert_table.setItem(row_idx, 3, self.create_item(str(qty)))
                self.alert_table.setItem(row_idx, 4, self.create_item(str(exp_date_str if exp_date_str else "-")))
                
                status = []
                if is_low_stock: status.append("Low Stock")
                if is_expiring: status.append("Expiring")
                
                lbl_status = QTableWidgetItem(", ".join(status))
                lbl_status.setForeground(QColor(COLOR_DANGER)) 
                lbl_status.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                self.alert_table.setItem(row_idx, 5, lbl_status)
                row_idx += 1

    def toggle_alert_selection(self, checked, prod_name, row):
        cell_widget = self.alert_table.cellWidget(row, 0)
        if checked:
            self.selected_alerts.add(prod_name)
            if cell_widget: cell_widget.setStyleSheet("background-color: #d0e1f5;")
        else:
            self.selected_alerts.discard(prod_name)
            if cell_widget: cell_widget.setStyleSheet("background-color: transparent;")

    def add_alerts_to_cart(self):
        if not self.selected_alerts:
            QMessageBox.warning(self, "Selection", "No items selected.")
            return
        
        count = 0
        for name in self.selected_alerts:
            if name not in self.order_cart:
                self.order_cart[name] = 50 
                count += 1
        
        QMessageBox.information(self, "Success", f"{count} items added to Create Order tab.")
        self.refresh_cart_table()
        self.tabs.setCurrentIndex(1)
        self.selected_alerts.clear()
        self.load_alerts()

    def setup_tab_create(self):
        layout = QVBoxLayout(self.tab_create)
        grp_supp = QGroupBox("Supplier Information")
        supp_layout = QVBoxLayout(grp_supp)
        
        row1 = QHBoxLayout()
        self.txt_supp_name = QLineEdit()
        self.txt_supp_name.setPlaceholderText("Search Supplier Name...")
        self.setup_supplier_completer() 
        self.txt_supp_name.editingFinished.connect(self.fill_supplier_details)
        row1.addWidget(QLabel("Supplier Name:"))
        row1.addWidget(self.txt_supp_name)
        
        row2 = QHBoxLayout()
        self.txt_supp_phone = QLineEdit()
        self.txt_supp_phone.setPlaceholderText("Phone Number")
        self.txt_supp_email = QLineEdit()
        self.txt_supp_email.setPlaceholderText("Email Address")
        row2.addWidget(QLabel("Phone:"))
        row2.addWidget(self.txt_supp_phone)
        row2.addWidget(QLabel("Email:"))
        row2.addWidget(self.txt_supp_email)

        supp_layout.addLayout(row1)
        supp_layout.addLayout(row2)
        layout.addWidget(grp_supp)

        grp_add = QGroupBox("Add Product to Order")
        add_layout = QHBoxLayout(grp_add)
        self.txt_new_item = QLineEdit()
        self.txt_new_item.setPlaceholderText("Type Product Name...")
        self.setup_product_completer() 
        
        self.spin_new_qty = QSpinBox()
        self.spin_new_qty.setRange(1, 10000)
        self.spin_new_qty.setValue(50)
        
        btn_add_manual = QPushButton("+ Add Item")
        btn_add_manual.setStyleSheet(f"background-color: {COLOR_NAVBAR}; color: white; padding: 6px 15px;")
        btn_add_manual.clicked.connect(self.add_manual_item)
        
        add_layout.addWidget(QLabel("Product:"))
        add_layout.addWidget(self.txt_new_item)
        add_layout.addWidget(QLabel("Qty:"))
        add_layout.addWidget(self.spin_new_qty)
        add_layout.addWidget(btn_add_manual)
        layout.addWidget(grp_add)

        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(3)
        self.cart_table.setHorizontalHeaderLabels(["Product Name", "Quantity", "Action"])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.cart_table.verticalHeader().setDefaultSectionSize(45) 
        layout.addWidget(self.cart_table)

        self.btn_save = QPushButton("Save Order & Generate PDF")
        self.btn_save.setFixedHeight(45)
        self.btn_save.setStyleSheet(f"background-color: {COLOR_ACCENT}; color: white; font-weight: bold; font-size: 15px;")
        self.btn_save.clicked.connect(self.save_order)
        layout.addWidget(self.btn_save)
        
        # INCREASED WIDTH of Clear Form Button
        self.btn_cancel_edit = QPushButton("Cancel Editing / Clear Form")
        self.btn_cancel_edit.setMinimumWidth(300) 
        self.btn_cancel_edit.setFixedHeight(35)
        self.btn_cancel_edit.setStyleSheet("background-color: #6c757d; color: white; font-weight: bold;")
        self.btn_cancel_edit.clicked.connect(self.clear_form)
        layout.addWidget(self.btn_cancel_edit)

    def setup_supplier_completer(self):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Sup_name FROM Supplier")
        suppliers = [row[0] for row in cursor.fetchall()]
        conn.close()
        completer = QCompleter(suppliers)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains) 
        self.txt_supp_name.setCompleter(completer)

    def setup_product_completer(self):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT prod_name FROM Product_Details")
        products = [row[0] for row in cursor.fetchall()]
        conn.close()
        completer = QCompleter(products)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.txt_new_item.setCompleter(completer)

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
        if not name: return

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT prod_id FROM Product_Details WHERE prod_name=?", (name,))
        result = cursor.fetchone()
        
        if not result:
            reply = QMessageBox.question(self, "New Product", 
                                         f"'{name}' is not in the database.\nAdd it to database now?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    cursor.execute("INSERT INTO Product_Details (prod_name, type, tabs_per_strip, gst) VALUES (?, 'Unknown', 10, 12)", (name,))
                    prod_id = cursor.lastrowid
                    cursor.execute("INSERT INTO Product_Stock (prod_id, quantity) VALUES (?, 0)", (prod_id,))
                    conn.commit()
                    QMessageBox.information(self, "Added", f"{name} added to database.")
                    self.setup_product_completer() 
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
                    conn.close()
                    return
            else:
                conn.close()
                return
        conn.close()

        self.order_cart[name] = qty
        self.txt_new_item.clear()
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
            btn_del.setStyleSheet(f"color: white; background-color: {COLOR_DANGER}; border-radius: 3px;")
            btn_del.clicked.connect(lambda _, n=name: self.remove_from_cart(n))
            self.cart_table.setCellWidget(i, 2, btn_del)

    def update_cart_qty(self, name, new_qty):
        self.order_cart[name] = new_qty

    def remove_from_cart(self, name):
        if name in self.order_cart: del self.order_cart[name]
        self.refresh_cart_table()

    def clear_form(self):
        self.order_cart.clear()
        self.refresh_cart_table()
        self.txt_supp_name.clear()
        self.txt_supp_phone.clear()
        self.txt_supp_email.clear()
        self.current_po_id = None
        self.btn_save.setText("Save Order & Generate PDF")
        self.btn_cancel_edit.setText("Cancel Editing / Clear Form")

    # === WHATSAPP AUTOMATION LOGIC (WINDOWS ONLY) ===
    def send_po_via_whatsapp(self, supplier_phone, po_id, pdf_path):
        if sys.platform != 'win32':
             QMessageBox.warning(self, "Not Supported", "WhatsApp automation is only supported on Windows.")
             return

        clean_phone = str(supplier_phone).replace("+", "").replace(" ", "").replace("-", "")
        if len(clean_phone) == 10:
            clean_phone = "91" + clean_phone 
            
        message = f"Hello,\n\nPlease find attached a new Purchase Order (#{po_id}) from our Pharmacy.\nKindly confirm receipt and process the order.\nThank you!"
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_message}"
        
        # 1. Add the file to the system clipboard
        if pdf_path and os.path.exists(pdf_path):
            clipboard = QApplication.clipboard()
            mime_data = QMimeData()
            mime_data.setUrls([QUrl.fromLocalFile(os.path.abspath(pdf_path))])
            clipboard.setMimeData(mime_data)

        # 2. Open WhatsApp Web/Desktop
        webbrowser.open(whatsapp_url)
        
        # 3. Use PyAutoGUI to simulate pasting the file (Ctrl + V)
        if pdf_path and os.path.exists(pdf_path):
            try:
                # Give WhatsApp Web/Desktop 8 seconds to open and load the chat window
                time.sleep(8) 
                
                # Simulate pressing Ctrl + V to paste the copied PDF
                pyautogui.hotkey('ctrl', 'v')
                
                # Wait 2 seconds for the attachment preview to load, then hit Enter to send
                time.sleep(2)
                pyautogui.press('enter')
            except Exception as e:
                 print(f"Automation Error: {e}")
                 QMessageBox.warning(self, "Automation Failed", "Could not auto-paste. Please press Ctrl+V in WhatsApp manually.")


    # === MAIN SAVE LOGIC ===
    def save_order(self):
        supp_name = self.txt_supp_name.text().strip()
        phone = self.txt_supp_phone.text().strip()
        email = self.txt_supp_email.text().strip()
        
        if not supp_name or not self.order_cart:
            QMessageBox.warning(self, "Error", "Supplier and Cart required!")
            return

        conn = database.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT Supp_id FROM Supplier WHERE Sup_name=?", (supp_name,))
            res = cursor.fetchone()
            if res:
                supp_id = res[0]
                cursor.execute("UPDATE Supplier SET contact=?, email=? WHERE Supp_id=?", (phone, email, supp_id))
            else:
                cursor.execute("INSERT INTO Supplier (Sup_name, contact, email) VALUES (?, ?, ?)", (supp_name, phone, email))
                supp_id = cursor.lastrowid

            today_str = datetime.date.today().strftime("%Y-%m-%d")

            if self.current_po_id:
                po_id = self.current_po_id
                cursor.execute("UPDATE Purchase_order SET supp_id=?, status='Updated' WHERE po_id=?", (supp_id, po_id))
                cursor.execute("DELETE FROM PO_item WHERE po_id=?", (po_id,))
                msg_text = f"Order #{po_id} Updated!"
            else:
                cursor.execute("INSERT INTO Purchase_order (order_date, supp_id, status) VALUES (?, ?, ?)", (today_str, supp_id, "Created"))
                po_id = cursor.lastrowid
                msg_text = f"Order #{po_id} Created!"
            
            for name, qty in self.order_cart.items():
                cursor.execute("SELECT prod_id FROM Product_Details WHERE prod_name=?", (name,))
                prod_res = cursor.fetchone()
                
                if prod_res:
                    prod_id = prod_res[0]
                    cursor.execute("INSERT INTO PO_item (po_id, Prod_id, Quantity) VALUES (?, ?, ?)", (po_id, prod_id, qty))
            
            conn.commit()
            
            # Generate the PDF
            pdf_path = self.generate_pdf(po_id, supp_name, phone, email, today_str)

            # --- POPUP DIALOG FOR SENDING ---
            dlg = SendMethodDialog(self)
            dlg.exec()

            email_status = ""
            wa_status = ""
            
            # --- HANDLE EMAIL ---
            if dlg.choice in ["EMAIL", "BOTH"]:
                if email:
                    if self.send_email_to_supplier(pdf_path, email, supp_name, po_id):
                        email_status = "- Email Sent Successfully!\n"
                        cursor.execute("UPDATE Purchase_order SET status='Sent' WHERE po_id=?", (po_id,))
                    else:
                        email_status = "- Email Failed (Check SMTP Settings).\n"
                else:
                    email_status = "- Email Failed (No email address provided).\n"

            # --- HANDLE WHATSAPP ---
            if dlg.choice in ["WHATSAPP", "BOTH"]:
                if phone:
                    # Ensure pyautogui is available before trying
                    if sys.platform == 'win32' and 'pyautogui' in sys.modules:
                        self.send_po_via_whatsapp(phone, po_id, pdf_path)
                        wa_status = "- WhatsApp Opened & File Auto-Attached!\n"
                        cursor.execute("UPDATE Purchase_order SET status='Sent' WHERE po_id=?", (po_id,))
                    else:
                         QMessageBox.warning(self, "WhatsApp Error", "WhatsApp automation requires Windows and the 'pyautogui' library installed.")
                         wa_status = "- WhatsApp Failed (Missing requirements).\n"
                else:
                    wa_status = "- WhatsApp Failed (No phone number provided).\n"

            conn.commit()
            
            # Final Message to user
            final_msg = f"{msg_text}\n\n{email_status}{wa_status}"
            if dlg.choice == "NONE":
                final_msg += "- Order saved without sending."
                
            QMessageBox.information(self, "Success", final_msg)
            
            self.clear_form()
            self.load_order_history()
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))
        finally:
            conn.close()

    def generate_pdf(self, po_id, s_name, s_phone, s_email, date_str):
        # CREATE A SPECIFIC FOLDER FOR PDFs
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        if hasattr(sys, 'frozen'):
            base_dir = os.path.dirname(sys.executable)
            
        po_folder = os.path.join(base_dir, "Purchase_Orders")
        os.makedirs(po_folder, exist_ok=True)
        
        filename = f"Order_{po_id}_{s_name.replace(' ', '_')}.pdf"
        filepath = os.path.join(po_folder, filename)
        
        if 'SimpleDocTemplate' not in globals():
            return None

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT p_name, location, phone, email FROM Pharmacy LIMIT 1")
        pharmacy = cursor.fetchone()
        conn.close()
        
        p_name, p_addr, p_phone, p_email = "My Pharmacy", "Address", "Phone", "Email"
        if pharmacy:
            p_name = pharmacy[0] if pharmacy[0] else "My Pharmacy"
            p_addr = pharmacy[1] if pharmacy[1] else ""
            p_phone = pharmacy[2] if pharmacy[2] else ""
            p_email = pharmacy[3] if pharmacy[3] else ""

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        style_center = ParagraphStyle(name='Center', parent=styles['Normal'], alignment=TA_CENTER)
        style_header = ParagraphStyle(name='Header', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=18)
        
        elements.append(Paragraph(f"<b>{p_name}</b>", style_header))
        elements.append(Paragraph(f"{p_addr}", style_center))
        elements.append(Paragraph(f"Tel: {p_phone} | Email: {p_email}", style_center))
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("_" * 60, style_center)) 
        elements.append(Spacer(1, 20))

        data_header = [
            [f"TO SUPPLIER:\n{s_name}\n{s_phone}\n{s_email}", 
             f"PURCHASE ORDER\n\nOrder ID: #{po_id}\nDate: {date_str}"]
        ]
        
        tbl_header = Table(data_header, colWidths=[300, 200])
        tbl_header.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ]))
        elements.append(tbl_header)
        elements.append(Spacer(1, 30))

        data = [["Product Name", "Quantity"]]
        for name, qty in self.order_cart.items():
            data.append([name, str(qty)])
            
        table = Table(data, colWidths=[350, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 40))
        
        try:
            doc.build(elements)
            return filepath # Returning the full file path
        except Exception as e:
            print(f"PDF Error: {e}")
            return None

    def get_email_credentials(self):
        conn = database.get_connection()
        if not conn: return None, None
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT smtp_email, smtp_password FROM Pharmacy LIMIT 1")
            row = cursor.fetchone()
            if row: return row[0], row[1]
        except Exception as e:
            print(f"Error fetching email credentials: {e}")
        finally:
            conn.close()
        return None, None

    def send_email_to_supplier(self, pdf_path, to_email, supp_name, po_id):
        if not pdf_path or not os.path.exists(pdf_path): return False

        sender_email, sender_password = self.get_email_credentials()
        
        if not sender_email or not sender_password:
            print("No email credentials found in settings.")
            return False

        msg = MIMEMultipart()
        msg['Subject'] = f"Purchase Order #{po_id}"
        msg['From'] = sender_email
        msg['To'] = to_email

        body = f"Dear {supp_name},\n\nPlease find attached Purchase Order #{po_id}.\n\nRegards,\nPharmacy Admin"
        msg.attach(MIMEText(body, 'plain'))

        try:
            with open(pdf_path, "rb") as f:
                attach = MIMEApplication(f.read(), _subtype="pdf")
                attach.add_header('Content-Disposition', 'attachment', filename=os.path.basename(pdf_path))
                msg.attach(attach)
        except Exception as e: 
            return False

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(sender_email, sender_password)
                smtp.send_message(msg)
            return True
        except Exception as e:
            print(f"SMTP Error: {e}")
            return False

    def setup_tab_history(self):
        layout = QVBoxLayout(self.tab_history)
        btn_refresh = QPushButton("⟳ Refresh History")
        btn_refresh.setStyleSheet(f"background-color: {COLOR_NAVBAR}; color: white; padding: 5px; font-weight: bold;")
        btn_refresh.clicked.connect(self.load_order_history)
        layout.addWidget(btn_refresh)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Order ID", "Supplier", "Date", "Status"])
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.history_table.verticalHeader().setDefaultSectionSize(45)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.itemSelectionChanged.connect(self.on_history_selection_changed)
        splitter.addWidget(self.history_table)
        
        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet(f"background: {COLOR_WHITE}; border: 1px solid #ccc;")
        self.preview_frame.setVisible(False) 
        
        prev_layout = QVBoxLayout(self.preview_frame)
        hdr_layout = QHBoxLayout()
        self.lbl_prev_info = QLabel("Order Details")
        self.lbl_prev_info.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        hdr_layout.addWidget(self.lbl_prev_info)
        
        btn_close = QPushButton("✕")
        btn_close.setFixedWidth(30)
        btn_close.clicked.connect(lambda: self.history_table.clearSelection())
        hdr_layout.addWidget(btn_close)
        prev_layout.addLayout(hdr_layout)
        
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.combo_status = QComboBox()
        self.combo_status.addItems(["Created", "Sent", "Received", "Declined"])
        self.btn_update_status = QPushButton("Update")
        self.btn_update_status.setMinimumWidth(120)
        self.btn_update_status.clicked.connect(self.update_order_status)
        status_layout.addWidget(self.combo_status)
        status_layout.addWidget(self.btn_update_status)
        prev_layout.addLayout(status_layout)
        
        # INCREASED WIDTH of Edit Button
        self.btn_edit_resend = QPushButton("✎ Edit / Resend Order")
        self.btn_edit_resend.setMinimumWidth(250)
        self.btn_edit_resend.setFixedHeight(35)
        self.btn_edit_resend.setStyleSheet(f"background-color: {COLOR_NAVBAR}; color: white; font-weight: bold;")
        self.btn_edit_resend.clicked.connect(self.load_order_for_editing)
        prev_layout.addWidget(self.btn_edit_resend)

        self.prev_items_table = QTableWidget()
        self.prev_items_table.setColumnCount(2)
        self.prev_items_table.setHorizontalHeaderLabels(["Product", "Qty"])
        self.prev_items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        prev_layout.addWidget(self.prev_items_table)
        
        splitter.addWidget(self.preview_frame)
        splitter.setStretchFactor(0, 3) 
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

    def load_order_history(self):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT po.po_id, s.Sup_name, po.order_date, po.status 
            FROM Purchase_order po JOIN Supplier s ON po.supp_id = s.Supp_id ORDER BY po.po_id DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        self.history_table.setRowCount(0)
        self.history_table.blockSignals(True) 
        for i, (pid, sname, date, status) in enumerate(rows):
            self.history_table.insertRow(i)
            self.history_table.setItem(i, 0, self.create_item(str(pid)))
            self.history_table.setItem(i, 1, self.create_item(sname))
            self.history_table.setItem(i, 2, self.create_item(date))
            self.history_table.setItem(i, 3, self.create_item(status))
        self.history_table.blockSignals(False)

    def on_history_selection_changed(self):
        selected_items = self.history_table.selectedItems()
        if not selected_items:
            self.preview_frame.setVisible(False)
            return

        self.preview_frame.setVisible(True)
        row = self.history_table.currentRow()
        
        po_id = self.history_table.item(row, 0).text()
        supp = self.history_table.item(row, 1).text()
        status = self.history_table.item(row, 3).text()
        
        self.lbl_prev_info.setText(f"Order #{po_id}\n{supp}")
        self.combo_status.setCurrentText(status)
        
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.prod_name, pi.Quantity FROM PO_item pi 
            JOIN Product_Details d ON pi.Prod_id = d.prod_id WHERE pi.po_id = ?
        """, (po_id,))
        items = cursor.fetchall()
        conn.close()
        
        self.prev_items_table.setRowCount(0)
        for i, (m_name, qty) in enumerate(items):
            self.prev_items_table.insertRow(i)
            self.prev_items_table.setItem(i, 0, self.create_item(m_name))
            self.prev_items_table.setItem(i, 1, self.create_item(str(qty)))

    def update_order_status(self):
        selected_items = self.history_table.selectedItems()
        if not selected_items: return
        
        row = self.history_table.currentRow()
        po_id = self.history_table.item(row, 0).text()
        new_status = self.combo_status.currentText()
        
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Purchase_order SET status=? WHERE po_id=?", (new_status, po_id))
        conn.commit()
        conn.close()
        
        self.history_table.setItem(row, 3, self.create_item(new_status))
        QMessageBox.information(self, "Updated", f"Order #{po_id} marked as {new_status}")

    def load_order_for_editing(self):
        selected_items = self.history_table.selectedItems()
        if not selected_items: return
        
        row = self.history_table.currentRow()
        po_id = self.history_table.item(row, 0).text()
        supp_name = self.history_table.item(row, 1).text()
        
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.prod_name, pi.Quantity FROM PO_item pi 
            JOIN Product_Details d ON pi.Prod_id = d.prod_id WHERE pi.po_id = ?
        """, (po_id,))
        items = cursor.fetchall()
        
        cursor.execute("SELECT contact, email FROM Supplier WHERE Sup_name=?", (supp_name,))
        supp_details = cursor.fetchone()
        conn.close()
        
        self.tabs.setCurrentIndex(1)
        self.clear_form() 
        
        self.current_po_id = po_id
        self.btn_save.setText(f"Update Order #{po_id}")
        self.btn_cancel_edit.setText("Cancel Edit")
        self.btn_cancel_edit.setVisible(True) 
        
        self.txt_supp_name.setText(supp_name)
        if supp_details:
            self.txt_supp_phone.setText(supp_details[0])
            self.txt_supp_email.setText(supp_details[1])
            
        for name, qty in items:
            self.order_cart[name] = qty
            
        self.refresh_cart_table()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OrdersInterface()
    window.resize(1100, 700)
    window.show()
    sys.exit(app.exec())