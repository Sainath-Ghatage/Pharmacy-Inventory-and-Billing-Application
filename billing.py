import sys
import datetime
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QSpinBox, QComboBox, QFrame, QSizePolicy, QMessageBox,
    QGridLayout, QAbstractItemView, QDoubleSpinBox, QCompleter
)
from PyQt6.QtGui import QFont, QTextDocument, QColor, QIcon, QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QSize, QStringListModel
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

import database 

# --- COLOR PALETTE ---
COLOR_NAVBAR = "#0d47a1"        # Deep Blue
COLOR_BG = "#f4f7f6"            # Light Grey Background
COLOR_WHITE = "#ffffff"
COLOR_GREEN_BTN = "#198754"     # Success Green
COLOR_BLUE_BTN = "#0d6efd"      # Primary Blue
COLOR_DARK_BTN = "#212529"      # Dark Grey/Black
COLOR_RED_BTN = "#dc3545"       # Danger Red
COLOR_TEXT_PRIMARY = "#212529"
COLOR_TEXT_SECONDARY = "#6c757d"
COLOR_BORDER = "#dee2e6"

# --- GLOBAL STYLES FOR VISIBILITY ---
# Forces text to be black (#000) on white backgrounds to fix visibility issues
STYLE_INPUT_FIELD = f"""
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background-color: {COLOR_WHITE};
        color: #000000;  /* Force Black Text */
        border: 1px solid {COLOR_BORDER};
        border-radius: 5px;
        padding: 5px;
        font-size: 14px;
        selection-background-color: {COLOR_NAVBAR};
        selection-color: white;
    }}
    QLineEdit::placeholder {{ color: #6c757d; }}
    QComboBox::drop-down {{ border: none; }}
    QComboBox QAbstractItemView {{
        background-color: {COLOR_WHITE};
        color: #000000;
        selection-background-color: #e9ecef;
        selection-color: black;
    }}
"""

STYLE_LABEL_DARK = "color: #000000; font-weight: 500; font-size: 14px;"

class BillingInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Billing POS")
        # Apply global font and background
        self.setStyleSheet(f"""
            QWidget {{ background-color: {COLOR_BG}; font-family: 'Segoe UI', Arial, sans-serif; }}
            {STYLE_INPUT_FIELD}
        """)

        # --- STATE VARIABLES ---
        self.current_bill_id = None  
        self.bill_items = []         
        self.current_selected_med = None
        self.customer_names = []
        self.doctor_names = []

        # --- DATABASE CACHE ---
        self.refresh_cache()
        
        self.build_ui()

    def refresh_cache(self):
        conn = database.get_connection()
        if not conn:
            self.all_meds_cache = []
            return

        cursor = conn.cursor()
        
        # 1. Fetch Medicines
        try:
            self.all_meds_cache = database.get_all_medicines()
        except Exception as e:
            print("Med fetch error:", e)
            self.all_meds_cache = []

        # 2. Fetch Customers for Autocomplete
        try:
            cursor.execute("SELECT Name FROM Customer")
            self.customer_names = [row[0] for row in cursor.fetchall() if row[0]]
        except Exception as e:
            print("Customer fetch error:", e)
            self.customer_names = []

        # 3. Fetch Doctors for Autocomplete
        try:
            cursor.execute("SELECT Name FROM Doctor")
            self.doctor_names = [row[0] for row in cursor.fetchall() if row[0]]
        except Exception as e:
            print("Doctor fetch error:", e)
            self.doctor_names = []
        
        conn.close()

    # =================================================================
    # BUILD UI
    # =================================================================
    def build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 2. MAIN CONTENT AREA (Split Left/Right)
        content_wrapper = QWidget()
        content_layout = QHBoxLayout(content_wrapper)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)

        # --- LEFT PANEL: Product Selection ---
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel, 35) # 35% width

        # --- RIGHT PANEL: Billing ---
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, 65) # 65% width

        main_layout.addWidget(content_wrapper)

    def create_left_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"background-color: {COLOR_WHITE}; border-radius: 10px; border: 1px solid {COLOR_BORDER};")
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header
        lbl_header = QLabel("Product Search")
        lbl_header.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLOR_NAVBAR};")
        layout.addWidget(lbl_header)

        # Search Box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search Name / Barcode...")
        self.search_input.setFixedHeight(40)
        self.search_input.textChanged.connect(self.on_search_text)
        layout.addWidget(self.search_input)

        # Match List
        self.match_list = QListWidget()
        self.match_list.itemClicked.connect(self.on_match_click)
        self.match_list.setStyleSheet(f"""
            QListWidget {{ border: 1px solid {COLOR_BORDER}; border-radius: 5px; color: #000000; background-color: white; }}
            QListWidget::item {{ color: #000000; padding: 5px; }}
            QListWidget::item:selected {{ background-color: {COLOR_NAVBAR}; color: white; }}
        """)
        layout.addWidget(self.match_list)

        # Selected Item Info
        info_box = QFrame()
        info_box.setStyleSheet(f"background-color: #f8f9fa; border-radius: 5px; padding: 10px; border: 1px solid #eee;")
        info_layout = QVBoxLayout(info_box)
        
        self.lbl_med_name = QLabel("Select Medicine")
        self.lbl_med_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #000000;")
        self.lbl_med_name.setWordWrap(True)
        
        self.lbl_details = QLabel("Stock: - | Rack: - | GST: -")
        self.lbl_details.setStyleSheet("color: #444444; font-size: 12px;")
        
        info_layout.addWidget(self.lbl_med_name)
        info_layout.addWidget(self.lbl_details)
        layout.addWidget(info_box)

        # Controls (Unit, Price, Qty)
        controls_layout = QGridLayout()
        
        def create_label(text):
            l = QLabel(text)
            l.setStyleSheet(STYLE_LABEL_DARK)
            return l

        # Unit Dropdown (Loose/Strip)
        self.cmb_unit = QComboBox()
        self.cmb_unit.addItems(["Pack/Strip"])
        self.cmb_unit.currentIndexChanged.connect(self.update_price_display)
        self.cmb_unit.setStyleSheet(STYLE_INPUT_FIELD)

        controls_layout.addWidget(create_label("Unit:"), 0, 0)
        controls_layout.addWidget(self.cmb_unit, 0, 1)

        # Discount Field
        self.spin_disc = QDoubleSpinBox()
        self.spin_disc.setRange(0, 100)
        self.spin_disc.setSuffix("%")
        self.spin_disc.setStyleSheet(STYLE_INPUT_FIELD)
        
        controls_layout.addWidget(create_label("Disc %:"), 0, 2)
        controls_layout.addWidget(self.spin_disc, 0, 3)

        # Price Display
        self.lbl_price = QLabel("₹0.00")
        self.lbl_price.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_GREEN_BTN};")
        controls_layout.addWidget(create_label("Price:"), 1, 0)
        controls_layout.addWidget(self.lbl_price, 1, 1)

        # Quantity
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 9999)
        self.qty_spin.setFixedSize(80, 35)
        self.qty_spin.setStyleSheet(STYLE_INPUT_FIELD)
        
        controls_layout.addWidget(create_label("Qty:"), 1, 2)
        controls_layout.addWidget(self.qty_spin, 1, 3)

        layout.addLayout(controls_layout)

        # Add Button
        self.add_btn = QPushButton("ADD TO BILL")
        self.add_btn.setFixedHeight(45)
        self.add_btn.clicked.connect(self.add_to_bill)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setStyleSheet(f"background-color: {COLOR_NAVBAR}; color: white; font-weight: bold; border-radius: 5px;")
        layout.addWidget(self.add_btn)

        return panel

    def create_right_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"background-color: {COLOR_WHITE}; border-radius: 10px; border: 1px solid {COLOR_BORDER};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Header Details
        form_layout = QHBoxLayout()
        
        # --- PATIENT INPUT WITH AUTOCOMPLETE ---
        self.inp_patient = QLineEdit()
        self.inp_patient.setPlaceholderText("Patient Name")
        self.inp_patient.setStyleSheet(STYLE_INPUT_FIELD)
        
        # Setup Patient Completer
        self.pat_completer = QCompleter(self.customer_names)
        self.pat_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.pat_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.inp_patient.setCompleter(self.pat_completer)
        
        # --- DOCTOR INPUT WITH AUTOCOMPLETE ---
        self.inp_doctor = QLineEdit()
        self.inp_doctor.setPlaceholderText("Doctor Name")
        self.inp_doctor.setStyleSheet(STYLE_INPUT_FIELD)
        
        # Setup Doctor Completer
        self.doc_completer = QCompleter(self.doctor_names)
        self.doc_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.doc_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.inp_doctor.setCompleter(self.doc_completer)
        
        lbl_pat = QLabel("Patient:")
        lbl_pat.setStyleSheet(STYLE_LABEL_DARK)
        lbl_doc = QLabel("Doctor:")
        lbl_doc.setStyleSheet(STYLE_LABEL_DARK)

        form_layout.addWidget(lbl_pat)
        form_layout.addWidget(self.inp_patient)
        form_layout.addWidget(lbl_doc)
        form_layout.addWidget(self.inp_doctor)
        layout.addLayout(form_layout)

        # Table
        self.bill_table = QTableWidget()
        self.bill_table.setColumnCount(7)
        self.bill_table.setHorizontalHeaderLabels(["Item", "Unit", "Price", "Qty", "Disc%", "Tax", "Total"])
        self.bill_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.bill_table.verticalHeader().setVisible(False)
        self.bill_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.bill_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.bill_table.setStyleSheet(f"""
            QTableWidget {{ border: none; gridline-color: #eee; color: #000000; background-color: white; }}
            QHeaderView::section {{ background-color: #f8f9fa; color: #000000; border: none; padding: 5px; font-weight: bold; }}
            QTableWidget::item {{ color: #000000; }}
            QTableWidget::item:selected {{ background-color: {COLOR_NAVBAR}; color: white; }}
        """)
        
        self.bill_table.cellDoubleClicked.connect(self.remove_item)
        layout.addWidget(self.bill_table)

        # Footer
        footer_bg = QFrame()
        footer_bg.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; border: 1px solid #eee;")
        footer_layout = QHBoxLayout(footer_bg)
        
        self.lbl_items_count = QLabel("Items: 0")
        self.lbl_items_count.setStyleSheet("color: #444444; font-weight: bold;")
        
        # --- PAYMENT DROPDOWN ---
        self.cmb_payment = QComboBox()
        self.cmb_payment.addItems(["Cash", "UPI", "Card", "Net Banking"])
        self.cmb_payment.setFixedWidth(120)
        self.cmb_payment.setStyleSheet(STYLE_INPUT_FIELD)

        self.lbl_grand_total = QLabel("Total: ₹0.00")
        self.lbl_grand_total.setStyleSheet(f"color: {COLOR_NAVBAR}; font-size: 22px; font-weight: bold;")
        
        self.btn_checkout = QPushButton("CHECKOUT & PRINT")
        self.btn_checkout.setFixedSize(180, 45)
        self.btn_checkout.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_checkout.clicked.connect(self.save_bill)
        self.btn_checkout.setStyleSheet(f"background-color: {COLOR_GREEN_BTN}; color: white; font-weight: bold; border-radius: 5px;")

        footer_layout.addWidget(self.lbl_items_count)
        footer_layout.addStretch()
        
        # Add Payment Label and Dropdown
        lbl_pay = QLabel("Payment:")
        lbl_pay.setStyleSheet(STYLE_LABEL_DARK)
        footer_layout.addWidget(lbl_pay)
        footer_layout.addWidget(self.cmb_payment)
        
        footer_layout.addSpacing(15)
        footer_layout.addWidget(self.lbl_grand_total)
        footer_layout.addWidget(self.btn_checkout)
        
        layout.addWidget(footer_bg)
        return panel

    # =================================================================
    # LOGIC
    # =================================================================
    def on_search_text(self, text):
        text = text.lower().strip()
        if not text:
            self.match_list.clear()
            return
        
        matches = []
        for row in self.all_meds_cache:
            # Index 1 = Med_name, Index 14 = Barcode (as per new schema)
            name = row[1].lower() if row[1] else ""
            barcode = str(row[14]).lower() if row[14] else ""
            
            if text in name or text == barcode:
                matches.append(row)
        
        self.populate_match_list(matches)

    def populate_match_list(self, matches):
        self.match_list.clear()
        for row in matches[:50]:
            name = row[1]
            rack = row[11] if row[11] else "-"
            stock = row[4]
            display = f"{name}  |  Rack: {rack}  |  Stock: {stock}"
            
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, row)
            self.match_list.addItem(item)

    def on_match_click(self, item):
        row = item.data(Qt.ItemDataRole.UserRole)
        
        self.current_selected_med = {
            "med_id": row[0],
            "name": row[1],
            "tabs_per_strip": row[2] if row[2] else 1,
            "rate_per_tab": row[3] if row[3] else 0.0,
            "stock": row[4],
            "type": row[5],
            "sale_price": row[7],
            "hsn": row[10],
            "rack": row[11],
            "gst_rate": row[12] if row[12] else 0.0,
            "discount": row[13] if row[13] else 0.0
        }
        
        med = self.current_selected_med
        self.lbl_med_name.setText(med['name'])
        self.lbl_details.setText(f"Stock: {med['stock']} | Rack: {med['rack']} | GST: {med['gst_rate']}% | HSN: {med['hsn']}")
        
        self.spin_disc.setValue(med['discount'])

        self.cmb_unit.blockSignals(True)
        self.cmb_unit.clear()
        
        is_tablet = med['type'] in ["Tablet", "Capsule"]
        if is_tablet:
            self.cmb_unit.addItems(["Pack/Strip", "Loose Tablet"])
        else:
            self.cmb_unit.addItems(["Pack/Unit"])
            
        self.cmb_unit.blockSignals(False)
        self.cmb_unit.setCurrentIndex(0)
        
        self.update_price_display()
        self.qty_spin.setValue(1)
        self.qty_spin.setFocus()

    def update_price_display(self):
        if not self.current_selected_med: return
        med = self.current_selected_med
        
        unit = self.cmb_unit.currentText()
        if unit == "Loose Tablet":
            price = med['rate_per_tab']
        else:
            price = med['sale_price']
            
        self.lbl_price.setText(f"₹{price:.2f}")

    def add_to_bill(self):
        if not self.current_selected_med: return
        
        med = self.current_selected_med
        qty = self.qty_spin.value()
        unit_type = self.cmb_unit.currentText()
        
        if unit_type == "Loose Tablet":
            unit_price = med['rate_per_tab']
            qty_to_deduct = qty / med['tabs_per_strip']
        else:
            unit_price = med['sale_price']
            qty_to_deduct = qty

        if qty_to_deduct > med['stock']:
            QMessageBox.warning(self, "Stock Alert", f"Insufficient Stock!\nRequired: {qty_to_deduct}\nAvailable: {med['stock']}")
            return

        discount_pct = self.spin_disc.value()

        new_item = {
            "med_id": med['med_id'],
            "name": med['name'],
            "unit": unit_type,
            "qty": qty,
            "qty_deduct": qty_to_deduct, 
            "price": unit_price,
            "gst_rate": med['gst_rate'],
            "hsn": med['hsn'],
            "discount_pct": discount_pct,
            "total": 0.0,
            "tax_amt": 0.0
        }
        self.calculate_line_item(new_item)
        self.bill_items.append(new_item)
        
        self.refresh_table()
        self.search_input.clear()
        self.search_input.setFocus()

    def calculate_line_item(self, item):
        gross = item['price'] * item['qty']
        disc_amt = gross * (item['discount_pct'] / 100.0)
        net_total = gross - disc_amt
        rate = item['gst_rate']
        tax_amt = net_total * (rate / (100 + rate)) if rate > 0 else 0.0
        
        item['total'] = net_total
        item['tax_amt'] = tax_amt

    def refresh_table(self):
        self.bill_table.setRowCount(len(self.bill_items))
        grand_total = 0.0
        
        for i, item in enumerate(self.bill_items):
            grand_total += item['total']
            
            self.bill_table.setItem(i, 0, QTableWidgetItem(item['name']))
            self.bill_table.setItem(i, 1, QTableWidgetItem(item['unit']))
            self.bill_table.setItem(i, 2, QTableWidgetItem(f"{item['price']:.2f}"))
            self.bill_table.setItem(i, 3, QTableWidgetItem(str(item['qty'])))
            self.bill_table.setItem(i, 4, QTableWidgetItem(f"{item['discount_pct']}%"))
            self.bill_table.setItem(i, 5, QTableWidgetItem(f"{item['tax_amt']:.2f}"))
            self.bill_table.setItem(i, 6, QTableWidgetItem(f"{item['total']:.2f}"))
        
        self.lbl_items_count.setText(f"Items: {len(self.bill_items)}")
        self.lbl_grand_total.setText(f"Total: ₹{grand_total:.2f}")

    def remove_item(self, row, col):
        if row >= 0:
            self.bill_items.pop(row)
            self.refresh_table()
            self.search_input.setFocus()

    def save_bill(self):
        if not self.bill_items:
            QMessageBox.warning(self, "Empty Bill", "Please add items first.")
            return

        pat_name = self.inp_patient.text().strip()
        doc_name = self.inp_doctor.text().strip()
        pay_method = self.cmb_payment.currentText()  # Get Payment Method
        total = sum(x['total'] for x in self.bill_items)
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = database.get_connection()
        if not conn: return
        cur = conn.cursor()
        
        try:
            # 1. Insert Bill Header
            cur.execute("""
                INSERT INTO Bill (patient_name, doctor_name, bill_date, total_sum, payment_method)
                VALUES (?, ?, ?, ?, ?)
            """, (pat_name, doc_name, date_str, total, pay_method))
            bill_id = cur.lastrowid
            
            # 2. Insert Items & Update Stock
            for item in self.bill_items:
                cur.execute("""
                    INSERT INTO Bill_Item (Bill_id, Med_id, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?)
                """, (bill_id, item['med_id'], item['qty'], item['price'], item['total']))
                
                cur.execute("UPDATE Medicine SET Quantity = Quantity - ? WHERE Med_id=?", 
                            (item['qty_deduct'], item['med_id']))
                
            conn.commit()
            
            # 3. Print
            self.print_receipt(bill_id, pat_name, doc_name, date_str, pay_method)
            
            # 4. Reset UI
            self.bill_items = []
            self.refresh_table()
            self.inp_patient.clear()
            self.inp_doctor.clear()
            self.cmb_payment.setCurrentIndex(0) # Reset Payment
            self.refresh_cache() 
            
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()

    def print_receipt(self, bill_id, pat, doc, date_str, pay_mode):
        printer = QPrinter()
        
        p_name = "Pharmacy"
        p_addr = "Address"
        p_phone = ""
        p_gst = ""
        
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT p_name, location, phone, GSTIN FROM Pharmacy LIMIT 1")
            row = cur.fetchone()
            if row:
                p_name, p_addr, p_phone, p_gst = row
        except: pass
        conn.close()

        html = f"""
        <h2 align='center'>{p_name}</h2>
        <p align='center'>{p_addr}<br>Phone: {p_phone}<br>GSTIN: {p_gst}</p>
        <hr>
        <p><b>Bill No:</b> {bill_id} &nbsp;&nbsp; <b>Date:</b> {date_str}<br>
           <b>Patient:</b> {pat if pat else 'Walk-in'} &nbsp;&nbsp; <b>Dr:</b> {doc if doc else '-'}<br>
           <b>Payment Mode:</b> {pay_mode}</p>
        
        <table width='100%' cellpadding='4' cellspacing='0' border='1' style='border-collapse: collapse; font-size: 10pt;'>
            <tr style='background-color: #f0f0f0;'>
                <th>Item</th>
                <th>HSN</th>
                <th>Qty</th>
                <th>Price</th>
                <th>Disc%</th>
                <th>Total</th>
            </tr>
        """
        
        grand_total = 0
        total_tax = 0
        
        for item in self.bill_items:
            grand_total += item['total']
            total_tax += item['tax_amt']
            hsn = item['hsn'] if item['hsn'] else "-"
            
            html += f"""
            <tr>
                <td>{item['name']} <br><small><i>({item['unit']})</i></small></td>
                <td align='center'>{hsn}</td>
                <td align='center'>{item['qty']}</td>
                <td align='right'>{item['price']:.2f}</td>
                <td align='center'>{item['discount_pct']}%</td>
                <td align='right'>{item['total']:.2f}</td>
            </tr>
            """
            
        html += f"""
        </table>
        <h3 align='right'>Net Payable: ₹{grand_total:.2f}</h3>
        <p align='right' style='font-size:10px;'>
            (Includes GST: ₹{total_tax:.2f})
        </p>
        <hr>
        <p align='center'>Thank you! Get Well Soon.</p>
        """

        doc = QTextDocument()
        doc.setHtml(html)
        
        dlg = QPrintDialog(printer, self)
        if dlg.exec():
            doc.print(printer)

    def load_bill_for_editing(self, bill_id):
        QMessageBox.information(self, "Info", "Edit feature coming soon.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = BillingInterface()
    w.show()
    sys.exit(app.exec())