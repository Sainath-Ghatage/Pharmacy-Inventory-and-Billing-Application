import sys
import datetime
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QSpinBox, QComboBox, QFrame, QSizePolicy, QMessageBox,
    QSpacerItem, QGridLayout
)
from PyQt6.QtGui import QFont, QTextDocument, QColor, QIcon
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

import database 

# --- COLOR PALETTE ---
COLOR_NAVBAR = "#0d47a1"        # Deep Blue
COLOR_BG = "#f4f7f6"            # Light Grey Background
COLOR_WHITE = "#ffffff"
COLOR_GREEN_BTN = "#198754"     # Bootstrap Success Green
COLOR_BLUE_BTN = "#0d6efd"      # Bootstrap Primary Blue
COLOR_DARK_BTN = "#212529"      # Dark Grey/Black
COLOR_RED_BTN = "#dc3545"       # Danger Red
COLOR_TEXT_PRIMARY = "#212529"
COLOR_TEXT_SECONDARY = "#6c757d"
COLOR_BORDER = "#dee2e6"

class BillingInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pharmacy System")
        self.setGeometry(100, 50, 1280, 800)
        self.setStyleSheet(f"background-color: {COLOR_BG}; font-family: 'Segoe UI', Arial, sans-serif;")

        # --- STATE VARIABLES ---
        self.current_bill_id = None  
        self.bill_items = []         
        self.current_selected_med = None

        # --- DATABASE CACHE ---
        try:
            self.all_meds_cache = database.get_all_medicines()
        except Exception as e:
            print("Database error or module not found:", e)
            self.all_meds_cache = []

        self.build_ui()
        self.populate_match_list(self.all_meds_cache)

    # =================================================================
    # BUILD UI
    # =================================================================
    def build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 2. MAIN CONTENT AREA (Split Left/Right)
        content_wrapper = QWidget()
        content_layout = QHBoxLayout(content_wrapper)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # --- LEFT PANEL: Product Selection ---
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel, 35) # 35% width

        # --- RIGHT PANEL: Billing ---
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, 65) # 65% width

        main_layout.addWidget(content_wrapper)

    def create_left_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_WHITE};
                border-radius: 10px;
                border: 1px solid {COLOR_BORDER};
            }}
        """)
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Header
        lbl_header = QLabel("Product Selection")
        lbl_header.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_TEXT_PRIMARY}; border: none;")
        layout.addWidget(lbl_header)

        # 2. Search Box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Type medicine...")
        self.search_input.textChanged.connect(self.on_search_text)
        self.search_input.setFixedHeight(45)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 0 10px;
                border: 1px solid {COLOR_BORDER};
                border-radius: 5px;
                font-size: 14px;
                color: #333;
            }}
            QLineEdit:focus {{ border: 1px solid {COLOR_NAVBAR}; }}
        """)
        layout.addWidget(self.search_input)

        # 3. Match List (List Widget)
        self.match_list = QListWidget()
        self.match_list.itemClicked.connect(self.on_match_click)
        self.match_list.setMaximumHeight(100)
        self.match_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 5px;
                background-color: #f8f9fa;
            }}
            QListWidget::item {{ padding: 8px; color: {COLOR_TEXT_PRIMARY}; }}
            QListWidget::item:selected {{ background-color: #e9ecef; color: {COLOR_NAVBAR}; }}
        """)
        layout.addWidget(self.match_list)

        # 4. Info Card
        info_card = QFrame()
        info_card.setStyleSheet(f"background-color: #ffffff; border: 1px solid {COLOR_BORDER}; border-radius: 10px;")
        card_layout = QVBoxLayout(info_card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_med_name = QLabel("Select Medicine")
        self.lbl_med_name.setWordWrap(True)
        self.lbl_med_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_med_name.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_TEXT_PRIMARY}; border: none; margin: 5px 0;")
        
        self.lbl_details = QLabel("Type: - | Stock: -")
        self.lbl_details.setStyleSheet("color: #666; font-size: 13px; border: none;")
        
        card_layout.addWidget(self.lbl_med_name)
        card_layout.addWidget(self.lbl_details)
        layout.addWidget(info_card, 1) # Expandable

        # 5. Controls Row (Price, Unit Type, Qty)
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        # -- Price Box --
        price_frame = QFrame()
        price_layout = QVBoxLayout(price_frame)
        price_layout.setContentsMargins(0,0,0,0)
        price_layout.setSpacing(2)
        
        self.lbl_price_title = QLabel("Unit Price")
        self.lbl_price_title.setStyleSheet("color: #666; font-size: 12px; border: none; padding:3px;")
        self.lbl_unit_price = QLabel("₹0.00")
        self.lbl_unit_price.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 22px; font-weight: bold; border: none; padding:3px;")
        
        price_layout.addWidget(self.lbl_price_title)
        price_layout.addWidget(self.lbl_unit_price)
        controls_layout.addWidget(price_frame)

        # -- Unit Type Selector --
        self.unit_selector = QComboBox()
        self.unit_selector.addItems(["Pack/Strip", "Loose Tab"])
        self.unit_selector.setVisible(False)
        self.unit_selector.setFixedSize(100, 40)
        self.unit_selector.currentTextChanged.connect(self.update_price_display)
        self.unit_selector.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 5px;
                padding-left: 5px;
                background: white;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QComboBox QAbstractItemView {{
                background-color: white;
                color: black;
                selection-background-color: #e9ecef;
                selection-color: black;
            }}
        """)
        controls_layout.addWidget(self.unit_selector)

        # -- Quantity Box --
        qty_container = QFrame()
        qty_container.setFixedSize(120, 45) 
        qty_container.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 5px;
                background-color: white;
            }}
        """)
        qty_layout = QHBoxLayout(qty_container)
        qty_layout.setContentsMargins(0, 0, 0, 0)
        qty_layout.setSpacing(0)

        btn_minus = QPushButton("-")
        btn_minus.setFixedSize(35, 45)
        btn_minus.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_minus.clicked.connect(self.decrease_qty)
        btn_minus.setStyleSheet("border: none; font-size: 20px; font-weight: bold; color: #555; background: transparent;")
        
        self.qty_spin = QSpinBox()
        self.qty_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.qty_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qty_spin.setRange(1, 9999)
        self.qty_spin.setStyleSheet("border: none; font-size: 18px; font-weight: bold; background: transparent; color: #333;")

        btn_plus = QPushButton("+")
        btn_plus.setFixedSize(35, 45)
        btn_plus.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_plus.clicked.connect(self.increase_qty)
        btn_plus.setStyleSheet("border: none; font-size: 20px; font-weight: bold; color: #555; background: transparent;")

        qty_layout.addWidget(btn_minus)
        qty_layout.addWidget(self.qty_spin)
        qty_layout.addWidget(btn_plus)

        controls_layout.addWidget(qty_container)
        layout.addLayout(controls_layout)

        # 6. Add Button
        self.add_btn = QPushButton("ADD TO BILL")
        self.add_btn.clicked.connect(self.add_to_bill)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setFixedHeight(50)
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_GREEN_BTN};
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 5px;
                border: none;
            }}
            QPushButton:hover {{ background-color: #146c43; }}
        """)
        layout.addWidget(self.add_btn)
        
        # 7. Status Label
        self.left_status = QLabel("")
        self.left_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_status.setMinimumHeight(30)
        self.left_status.setStyleSheet("font-size: 13px; border: none; padding: 5px;")
        layout.addWidget(self.left_status)

        return panel

    def create_right_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_WHITE};
                border-radius: 10px;
                border: 1px solid {COLOR_BORDER};
            }}
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # 1. Header
        header_layout = QHBoxLayout()
        lbl_bill_id = QLabel("Bill Preview") 
        lbl_bill_id.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_TEXT_PRIMARY}; border: none;")
        header_layout.addWidget(lbl_bill_id)
        layout.addLayout(header_layout)

        # --- PATIENT & DOCTOR DETAILS ---
        details_frame = QFrame()
        details_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; border: none; color: black;")
        details_layout = QHBoxLayout(details_frame)
        details_layout.setContentsMargins(10, 10, 10, 10)
        details_layout.setSpacing(15)

        # Patient Input
        self.inp_patient = QLineEdit()
        self.inp_patient.setPlaceholderText("Patient Name")
        self.inp_patient.setFixedHeight(40)
        self.inp_patient.setStyleSheet(f"border: 1px solid {COLOR_BORDER}; border-radius: 5px; padding-left: 10px; background: white; color: black;")
        
        # Doctor Input
        self.inp_doctor = QLineEdit()
        self.inp_doctor.setPlaceholderText("Doctor Name")
        self.inp_doctor.setFixedHeight(40)
        self.inp_doctor.setStyleSheet(f"border: 1px solid {COLOR_BORDER}; border-radius: 5px; padding-left: 10px; background: white; color: black;")

        details_layout.addWidget(QLabel("Patient:"))
        details_layout.addWidget(self.inp_patient, 1) # Stretch factor 1
        details_layout.addWidget(QLabel("Doctor:"))
        details_layout.addWidget(self.inp_doctor, 1) # Stretch factor 1
        
        layout.addWidget(details_frame)

        # 2. Table
        self.bill_table = QTableWidget()
        self.bill_table.setColumnCount(5)
        self.bill_table.setHorizontalHeaderLabels(["Item Name", "Price", "Qty", "Total", ""])
        self.bill_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.bill_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.bill_table.setColumnWidth(4, 50)
        self.bill_table.verticalHeader().setVisible(False)
        self.bill_table.setShowGrid(False)
        self.bill_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.bill_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.bill_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.bill_table.setStyleSheet(f"""
            QTableWidget {{ border: none; background-color: white; }}
            QHeaderView::section {{
                background-color: #f1f3f5;
                color: {COLOR_TEXT_PRIMARY};
                border: none;
                padding: 10px;
                font-weight: bold;
            }}
            QTableWidget::item {{ border-bottom: 1px solid #f8f9fa; padding: 8px; color: #333; }}
            QTableWidget::item:selected {{ background-color: #e9ecef; color: black; }}
        """)
        self.bill_table.cellClicked.connect(self.on_table_row_clicked)
        layout.addWidget(self.bill_table)

        # 3. Footer Section
        footer_bg = QFrame()
        footer_bg.setStyleSheet("background-color: #f8f9fa; border-radius: 8px; border: none;")
        footer_layout = QVBoxLayout(footer_bg)
        footer_layout.setContentsMargins(20, 20, 20, 20)
        footer_layout.setSpacing(15)

        # -- Totals --
        totals_grid = QGridLayout()
        totals_grid.setColumnStretch(0, 1)
        
        lbl_grand_txt = QLabel("Total:")
        lbl_grand_txt.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_NAVBAR};")
        self.lbl_grand_val = QLabel("₹0.00")
        self.lbl_grand_val.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {COLOR_NAVBAR};")
        
        totals_grid.addWidget(lbl_grand_txt, 2, 1, alignment=Qt.AlignmentFlag.AlignRight)
        totals_grid.addWidget(self.lbl_grand_val, 2, 2, alignment=Qt.AlignmentFlag.AlignRight)
        
        footer_layout.addLayout(totals_grid)
        footer_layout.addWidget(self.create_h_line())

        # -- Action Buttons --
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(15) 

        # Clear
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedWidth(80)
        self.clear_btn.setFixedHeight(45)
        self.clear_btn.clicked.connect(self.clear_bill)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{ background-color: #6c757d; color: white; border-radius: 5px; font-weight: bold; }}
            QPushButton:hover {{ background-color: #5a6268; }}
        """)
        
        # Payment Combo
        pay_layout = QHBoxLayout()
        pay_layout.setSpacing(8)
        lbl_pay = QLabel("Payment:")
        lbl_pay.setStyleSheet("color: #495057; font-weight: bold;")
        
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Cash", "UPI", "Card"])
        self.payment_combo.setFixedSize(140, 45)
        self.payment_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 5px;
                padding-left: 10px;
                background: white;
                color: #333;
                font-weight: bold;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox::down-arrow {{ image: none; border-left: 2px solid {COLOR_BORDER}; width: 0; height: 0; }}
            
            QComboBox QAbstractItemView {{
                background-color: white;
                color: #333333;
                selection-background-color: #e9ecef;
                selection-color: black;
                outline: none;
                border: 1px solid {COLOR_BORDER};
            }}
        """)
        
        pay_layout.addWidget(lbl_pay)
        pay_layout.addWidget(self.payment_combo)

        # New Bill
        self.new_bill_btn = QPushButton("New Bill")
        self.new_bill_btn.setFixedSize(100, 45)
        self.new_bill_btn.clicked.connect(self.start_new_bill)
        self.new_bill_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_bill_btn.setStyleSheet(f"""
            QPushButton {{ 
                background-color: white; 
                color: {COLOR_BLUE_BTN}; 
                border: 2px solid {COLOR_BLUE_BTN}; 
                border-radius: 5px; 
                font-weight: bold; 
            }}
            QPushButton:hover {{ background-color: #f0f8ff; }}
        """)

        # Checkout
        self.save_btn = QPushButton("CHECKOUT")
        self.save_btn.setFixedHeight(45)
        self.save_btn.setMinimumWidth(160)
        self.save_btn.clicked.connect(self.save_bill)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {COLOR_NAVBAR}; 
                color: white; 
                border-radius: 5px; 
                font-weight: bold; 
                font-size: 14px;
            }}
            QPushButton:hover {{ background-color: #0a3675; }}
        """)

        actions_layout.addWidget(self.clear_btn)
        actions_layout.addStretch()
        actions_layout.addLayout(pay_layout)
        actions_layout.addStretch()
        actions_layout.addWidget(self.new_bill_btn)
        actions_layout.addWidget(self.save_btn)

        footer_layout.addLayout(actions_layout)
        layout.addWidget(footer_bg)
        
        return panel

    def create_h_line(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet(f"border: none; background-color: {COLOR_BORDER}; max-height: 1px;")
        return line

    # =================================================================
    # LOGIC
    # =================================================================
    def increase_qty(self):
        val = self.qty_spin.value()
        self.qty_spin.setValue(val + 1)

    def decrease_qty(self):
        val = self.qty_spin.value()
        if val > 1:
            self.qty_spin.setValue(val - 1)

    def on_search_text(self, text: str):
        text = text.lower().strip()
        if not text:
            self.populate_match_list(self.all_meds_cache)
            return
        matches = [row for row in self.all_meds_cache if text in (row[1] or "").lower()]
        self.populate_match_list(matches)

    def populate_match_list(self, meds):
        self.match_list.clear()
        for row in meds[:50]: 
            med_id, med_name, tabs_per_strip, rate_per_tab, qty, mtype, pp, sp, mfg, exp = row
            display_text = f"{med_name} ({mtype})"
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, row)
            self.match_list.addItem(item)

    def on_match_click(self, item: QListWidgetItem):
        row = item.data(Qt.ItemDataRole.UserRole)
        self.load_medicine_details(row)
        self.qty_spin.setValue(1)
        self.left_status.setText("")
        self.add_btn.setText("ADD TO BILL")
        self.bill_table.clearSelection()

    def load_medicine_details(self, row_data):
        med_id, name, tabs_per_strip, rate_per_tab, qty, mtype, pp, sp, mfg, exp = row_data

        self.current_selected_med = {
            "med_id": med_id,
            "name": name,
            "pack_price": float(sp),
            "loose_price": float(rate_per_tab) if rate_per_tab else 0.0,
            "stock": int(qty) if qty else 0,
            "expiry": exp,
            "type": mtype,
            "tabs_per_strip": int(tabs_per_strip) if tabs_per_strip else 1
        }
        
        self.lbl_med_name.setText(name)
        self.lbl_details.setText(f"Type: {mtype} | Expiry: {exp} | Stock: {qty}")
        
        if mtype in ["Tablet", "Capsule"]:
            self.unit_selector.setVisible(True)
            self.unit_selector.setCurrentIndex(0) 
            self.lbl_price_title.setText("Price (Per Pack)")
            self.lbl_unit_price.setText(f"₹{float(sp):.2f}")
        else:
            self.unit_selector.setVisible(False)
            self.unit_selector.setCurrentIndex(0) 
            self.lbl_price_title.setText("Unit Price")
            self.lbl_unit_price.setText(f"₹{float(sp):.2f}")

        max_stock = int(qty) if qty else 0
        self.qty_spin.setMaximum(max(1, max_stock))

    def update_price_display(self, text):
        if not self.current_selected_med: return
        med = self.current_selected_med
        
        if text == "Loose Tab":
            self.lbl_price_title.setText("Price (Per Tab)")
            self.lbl_unit_price.setText(f"₹{med['loose_price']:.2f}")
            total_tabs = med['stock'] * med['tabs_per_strip']
            self.qty_spin.setMaximum(max(1, total_tabs))
        else:
            self.lbl_price_title.setText("Price (Per Pack)")
            self.lbl_unit_price.setText(f"₹{med['pack_price']:.2f}")
            self.qty_spin.setMaximum(max(1, med['stock']))

    def add_to_bill(self):
        if not self.current_selected_med:
            self.show_error("Please search and select a medicine first.")
            return

        qty_input = int(self.qty_spin.value())
        med = self.current_selected_med
        mode = self.unit_selector.currentText()
        is_loose = (mode == "Loose Tab" and self.unit_selector.isVisible())

        if qty_input <= 0:
            self.show_error("Quantity must be at least 1.")
            return

        if is_loose:
            req_strips = qty_input / med['tabs_per_strip']
            if req_strips > med['stock']:
                 self.show_error(f"Insufficient Stock. Available: {med['stock']} Strips")
                 return
        else:
            if qty_input > med['stock']:
                self.show_error(f"Insufficient Stock. Available: {med['stock']}")
                return

        final_price = med['loose_price'] if is_loose else med['pack_price']
        display_name = f"{med['name']} (Loose)" if is_loose else med['name']
        qty_db = (qty_input / med['tabs_per_strip']) if is_loose else qty_input

        existing_item = None
        for item in self.bill_items:
            if item["med_id"] == med["med_id"] and item["is_loose"] == is_loose:
                existing_item = item
                break

        if existing_item:
            existing_item["qty_display"] += qty_input
            existing_item["qty_db"] += qty_db
            existing_item["total"] = existing_item["qty_display"] * final_price
        else:
            self.bill_items.append({
                "med_id": med["med_id"],
                "name": display_name,
                "qty_display": qty_input,
                "qty_db": qty_db,
                "unit_price": final_price,
                "total": qty_input * final_price,
                "is_loose": is_loose
            })

        self.refresh_bill_table()
        self.left_status.setText("")
        self.left_status.setStyleSheet(f"color: {COLOR_GREEN_BTN}; font-size: 12px;")
        self.left_status.setText("Item added successfully!")
        self.bill_table.clearSelection()
        self.add_btn.setText("ADD TO BILL")

    def show_error(self, msg):
        self.left_status.setStyleSheet("color: #dc3545; font-size: 12px;")
        self.left_status.setText(msg)

    def refresh_bill_table(self):
        self.bill_table.setRowCount(0)
        self.bill_table.setRowCount(len(self.bill_items))

        grand_total = 0

        for i, item in enumerate(self.bill_items):
            grand_total += item["total"]
            it_name = QTableWidgetItem(item["name"])
            it_price = QTableWidgetItem(f"₹{item['unit_price']:.2f}")
            it_price.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            it_qty = QTableWidgetItem(str(item["qty_display"]))
            it_qty.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            it_total = QTableWidgetItem(f"₹{item['total']:.2f}")
            it_total.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.bill_table.setItem(i, 0, it_name)
            self.bill_table.setItem(i, 1, it_price)
            self.bill_table.setItem(i, 2, it_qty)
            self.bill_table.setItem(i, 3, it_total)

            btn_del = QPushButton("⛔")
            btn_del.setStyleSheet("color: red; border: none; font-size: 16px; background: transparent;")
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.clicked.connect(lambda _, idx=i: self.delete_item_at(idx))
            self.bill_table.setCellWidget(i, 4, btn_del)

        self.lbl_grand_val.setText(f"₹{grand_total:.2f}")

    def on_table_row_clicked(self, row, col):
        if col == 4: return 
        if row < 0 or row >= len(self.bill_items): return
        item = self.bill_items[row]
        self.left_status.setStyleSheet("color: #d63384;")
        self.left_status.setText(f"Selected: {item['name']}")

    def delete_item_at(self, idx):
        if 0 <= idx < len(self.bill_items):
            removed = self.bill_items.pop(idx)
            self.refresh_bill_table()
            self.left_status.setText(f"Removed {removed['name']}")

    def clear_bill(self):
        self.bill_items = []
        self.refresh_bill_table()
        self.lbl_med_name.setText("Select Medicine")
        self.lbl_details.setText("Type: - | Expiry: - | Stock: -")
        self.lbl_unit_price.setText("₹0.00")
        self.qty_spin.setValue(1)
        self.add_btn.setText("ADD TO BILL")
        self.left_status.setText("")
        self.unit_selector.setVisible(False)
        self.inp_patient.clear()
        self.inp_doctor.clear()

    def start_new_bill(self):
        self.clear_bill()
        self.current_bill_id = None
        self.save_btn.setText("CHECKOUT & SAVE")
        self.left_status.setStyleSheet(f"color: {COLOR_BLUE_BTN};")
        self.left_status.setText("Started New Bill")

    # --- NEW HELPER FOR PHARMACY DETAILS ---
    def get_pharmacy_details(self):
        """Fetches the first row from the Pharmacy table."""
        try:
            conn = database.get_connection()
            if not conn: return None
            cur = conn.cursor()
            cur.execute("SELECT p_name, phone, location FROM Pharmacy LIMIT 1")
            row = cur.fetchone()
            conn.close()
            if row:
                return {"name": row[0], "phone": row[1], "address": row[2]}
        except Exception as e:
            print("Error fetching pharmacy details:", e)
        # Default fallback if DB is empty or error
        return {"name": "My Pharmacy", "phone": "000-000-0000", "address": "Local Address"}

    def save_bill(self):
        if not self.bill_items:
            # Force black text for this popup and buttons
            msg = QMessageBox(self)
            msg.setWindowTitle("Empty Bill")
            msg.setText("Cannot checkout an empty bill.")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setStyleSheet("""
                QMessageBox { background-color: white; }
                QLabel { color: black; }
                QPushButton { color: black; background-color: #f0f0f0; border: 1px solid #ccc; padding: 5px 15px; border-radius: 4px; }
                QPushButton:hover { background-color: #e0e0e0; }
            """)
            msg.exec()
            return

        pat_name = self.inp_patient.text().strip()
        doc_name = self.inp_doctor.text().strip()

        conn = None
        try:
            conn = database.get_connection()
            if not conn: raise Exception("Could not connect to database")
            cur = conn.cursor()
            
            bill_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            total = sum(it["total"] for it in self.bill_items)
            payment_method = self.payment_combo.currentText()

            # --- 1. HANDLE BILL HEADER ---
            if self.current_bill_id is not None:
                # Update Logic
                cur.execute("SELECT Med_id, quantity FROM Bill_Item WHERE Bill_id = ?", (self.current_bill_id,))
                old_items = cur.fetchall()
                for o_med_id, o_qty in old_items:
                    cur.execute("UPDATE Medicine SET Quantity = Quantity + ? WHERE Med_id = ?", (o_qty, o_med_id))
                
                cur.execute("DELETE FROM Bill_Item WHERE Bill_id = ?", (self.current_bill_id,))
                cur.execute("""
                    UPDATE Bill 
                    SET total_sum = ?, payment_method = ?, bill_date = ?, patient = ?, doctor = ?
                    WHERE Bill_id = ?
                """, (total, payment_method, bill_date, pat_name, doc_name, self.current_bill_id))
                
                bill_id = self.current_bill_id
                action_type = "Updated"
            else:
                # Insert Logic
                cur.execute("""
                    INSERT INTO Bill (bill_date, discount, total_sum, payment_method, patient, doctor)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (bill_date, 0, total, payment_method, pat_name, doc_name))
                
                bill_id = cur.lastrowid
                self.current_bill_id = bill_id
                action_type = "Saved"

            # --- 2. INSERT ITEMS & DEDUCT STOCK ---
            for it in self.bill_items:
                cur.execute("""
                    INSERT INTO Bill_Item (Bill_id, Med_id, quantity)
                    VALUES (?, ?, ?)
                """, (bill_id, it["med_id"], it["qty_db"]))
                
                cur.execute("UPDATE Medicine SET Quantity = Quantity - ? WHERE Med_id = ?",
                            (it["qty_db"], it["med_id"]))

            conn.commit()
            conn.close()

            self.all_meds_cache = database.get_all_medicines()
            self.populate_match_list(self.all_meds_cache)
            self.save_btn.setText("UPDATE BILL")

            # --- SUCCESS POPUP WITH BLACK TEXT FOR BUTTONS & LABEL ---
            msg = QMessageBox(self)
            msg.setWindowTitle("Success")
            msg.setText(f"Bill #{bill_id} {action_type} Successfully!\n\nDo you want to print the receipt?")
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            # EXPLICITLY STYLE QBUTTONS TO BE VISIBLE
            msg.setStyleSheet("""
                QMessageBox { background-color: white; }
                QLabel { color: black; font-weight: bold; }
                QPushButton { color: black; background-color: #f0f0f0; border: 1px solid #ccc; padding: 5px 15px; border-radius: 4px; }
                QPushButton:hover { background-color: #e0e0e0; }
            """)
            
            if msg.exec() == QMessageBox.StandardButton.Yes:
                self.print_current_bill_logic(bill_id)
            
        except Exception as e:
            if conn: conn.close()
            print(f"Error: {e}")
            
            err = QMessageBox(self)
            err.setWindowTitle("Error")
            err.setText(str(e))
            err.setIcon(QMessageBox.Icon.Critical)
            err.setStyleSheet("""
                QMessageBox { background-color: white; }
                QLabel { color: black; }
                QPushButton { color: black; background-color: #f0f0f0; border: 1px solid #ccc; padding: 5px 15px; border-radius: 4px; }
                QPushButton:hover { background-color: #e0e0e0; }
            """)
            err.exec()

    # --- UPDATED PRINT LOGIC ---
    def print_current_bill_logic(self, bill_id):
        # 1. Get Pharmacy Details
        pharma = self.get_pharmacy_details()
        p_name = pharma.get('name', 'Pharmacy Name')
        p_phone = pharma.get('phone', '')
        p_addr = pharma.get('address', '')

        # 2. Get Date
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        lines = []
        # --- HEADER (CENTERED) ---
        lines.append(f"<h1 align='center' style='margin-bottom:0;'>{p_name}</h1>")
        lines.append(f"<p align='center' style='margin-top:0;'>{p_addr}<br>Phone: {p_phone}</p>")
        lines.append("<hr>")

        # --- BILL INFO (Date & ID) ---
        # Using a simple table to separate ID (Left) and Date (Right)
        lines.append("<table width='100%'>")
        lines.append(f"<tr><td align='left'><b>Bill No:</b> {bill_id}</td><td align='right'><b>Date:</b> {now_str}</td></tr>")
        lines.append("</table>")
        lines.append("<br>")

        # --- MAIN ITEMS TABLE ---
        # Fixed alignment: Name(Left), Qty(Center), Price(Right), Total(Right)
        lines.append("<table width='100%' cellspacing='0' cellpadding='5' style='border-collapse: collapse; border-bottom: 1px solid black;'>")
        lines.append("<thead>")
        lines.append("<tr style='background-color: #f0f0f0;'>")
        lines.append("<th align='left'>Item Name</th>")
        lines.append("<th align='center'>Qty</th>")
        lines.append("<th align='right'>Price</th>")
        lines.append("<th align='right'>Total</th>")
        lines.append("</tr>")
        lines.append("</thead>")
        lines.append("<tbody>")
        
        total = 0
        for it in self.bill_items:
            lines.append("<tr>")
            lines.append(f"<td align='left'>{it['name']}</td>")
            lines.append(f"<td align='center'>{it['qty_display']}</td>")
            lines.append(f"<td align='right'>{it['unit_price']:.2f}</td>")
            lines.append(f"<td align='right'>{it['total']:.2f}</td>")
            lines.append("</tr>")
            total += it['total']
        
        lines.append("</tbody>")
        lines.append("</table>")
        
        # --- FOOTER TOTAL ---
        lines.append(f"<h3 align='right'>Grand Total: {total:.2f}</h3>")
        lines.append("<p align='center' style='font-size: 10px;'>Thank you for your business!</p>")
        
        html = "".join(lines)
        doc = QTextDocument()
        doc.setHtml(html)
        
        printer = QPrinter()
        dlg = QPrintDialog(printer, self)
        if dlg.exec():
            doc.print(printer)
    
    def refresh_cache(self):
        try:
            self.all_meds_cache = database.get_all_medicines()
            self.populate_match_list(self.all_meds_cache)
        except Exception as e:
            print("Error refreshing billing cache:", e)

    def load_bill_for_editing(self, bill_id):
        try:
            conn = database.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT patient, doctor, payment_method FROM Bill WHERE Bill_id = ?", (bill_id,))
            header = cursor.fetchone()
            if not header: return

            cursor.execute("""
                SELECT bi.Med_id, bi.quantity, m.Med_name, m.Sale_Price, m.rate_per_tab, m.tabs_per_strip, m.Type
                FROM Bill_Item bi
                JOIN Medicine m ON bi.Med_id = m.Med_id
                WHERE bi.Bill_id = ?
            """, (bill_id,))
            items = cursor.fetchall()
            conn.close()
            
            self.start_new_bill()
            self.current_bill_id = bill_id
            self.save_btn.setText("UPDATE BILL")
            self.left_status.setText(f"Editing Bill #{bill_id}")
            
            self.inp_patient.setText(header[0])
            self.inp_doctor.setText(header[1])
            self.payment_combo.setCurrentText(header[2])
            
            for row in items:
                med_id, db_qty, name, pack_price, loose_price, tabs_per, mtype = row
                
                is_fractional = (db_qty % 1 != 0)
                
                if is_fractional:
                    is_loose = True
                    qty_display = int(round(db_qty * tabs_per))
                    unit_price = loose_price if loose_price else 0
                    final_name = f"{name} (Loose)"
                else:
                    is_loose = False
                    qty_display = int(db_qty)
                    unit_price = pack_price
                    final_name = name

                self.bill_items.append({
                    "med_id": med_id,
                    "name": final_name,
                    "qty_display": qty_display,
                    "qty_db": db_qty,
                    "unit_price": unit_price,
                    "total": qty_display * unit_price,
                    "is_loose": is_loose
                })
            
            self.refresh_bill_table()
            
        except Exception as e:
            print("Error loading bill:", e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = BillingInterface()
    w.show()
    sys.exit(app.exec())