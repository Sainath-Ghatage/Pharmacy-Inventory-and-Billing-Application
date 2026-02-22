import sys
import sqlite3
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QFrame, QMessageBox, QFormLayout,
    QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox, 
    QAbstractItemView, QTabWidget, QStackedWidget, QGroupBox, QCompleter,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QStringListModel
from PyQt6.QtGui import QColor, QFont, QIcon, QBrush

# Ensure database.py is in the same folder
import database 

# --- STYLES ---
COLOR_NAVBAR = "#0d47a1"
COLOR_GREEN_BTN = "#198754"
COLOR_BLUE_BTN = "#0d6efd"
COLOR_DELETE = "#dc3545"
COLOR_EDIT = "#ffc107"
COLOR_TEXT = "#000000"
COLOR_WHITE = "#ffffff"
COLOR_EXPIRED = "#dc3545" 
COLOR_WARNING = "#fd7e14" 

STYLE_GLOBAL = f"""
    QWidget {{ font-family: 'Segoe UI', sans-serif; color: {COLOR_TEXT}; font-size: 14px; }}
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background-color: {COLOR_WHITE};
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 6px;
        color: {COLOR_TEXT};
    }}
    QTableWidget {{
        background-color: {COLOR_WHITE};
        gridline-color: #eee;
        color: {COLOR_TEXT};
        border: 1px solid #ddd;
        selection-background-color: #e3f2fd;
        selection-color: {COLOR_TEXT};
    }}
    QHeaderView::section {{
        background-color: #f8f9fa;
        padding: 8px;
        font-weight: bold;
        color: #495057;
        border: none;
        border-bottom: 2px solid #dee2e6;
        border-right: 1px solid #dee2e6;
    }}
    QTableWidget::item {{
        padding: 5px;
    }}
    QGroupBox {{
        font-weight: bold;
        border: 1px solid #ccc;
        border-radius: 6px;
        margin-top: 20px;
        padding-top: 15px;
        background-color: #fff;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 10px;
        color: {COLOR_NAVBAR};
        background-color: #fff;
    }}
    /* Main Tab Styles */
    QTabWidget::pane {{ border: 1px solid #ccc; background: white; border-radius: 4px; }}
    QTabBar::tab {{ 
        background: #f1f3f5; 
        color: #495057; 
        padding: 8px 25px; 
        font-weight: 600;
        border: 1px solid #ddd;
        border-bottom: none;
        margin-right: 4px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        min-width: 120px;
    }}
    QTabBar::tab:selected {{ 
        background: {COLOR_NAVBAR}; 
        color: white; 
        border-color: {COLOR_NAVBAR};
    }}
    QTabBar::tab:hover {{
        background: #e9ecef;
    }}
"""

# ==========================================
# 0. DB HELPER
# ==========================================
def ensure_schema_update():
    conn = database.get_connection()
    if not conn: return
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(Product_Stock)")
        columns = [info[1] for info in cursor.fetchall()]
        if "min_qty" not in columns:
            cursor.execute("ALTER TABLE Product_Stock ADD COLUMN min_qty INTEGER DEFAULT 10")
            conn.commit()
    except Exception as e:
        print(f"DB Update Error: {e}")
    finally:
        conn.close()

# ==========================================
# 1. PRODUCT DETAILS FORM (Add & Edit)
# ==========================================
class ProductDetailsForm(QWidget):
    saved = pyqtSignal()
    canceled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.edit_mode_id = None 
        self.init_ui()
        

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.group_box = QGroupBox("Register New Product Details")
        self.group_box.setFixedWidth(600)
        
        layout = QVBoxLayout(self.group_box)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(15)

        self.name = QLineEdit()
        self.mfg = QLineEdit()
        self.hsn = QLineEdit()
        self.type = QComboBox()
        self.type.addItems(["Tablet", "Capsule", "Syrup", "Injection", "Cream", 
            "Ointment", "Drops", "Personal Care & Wellness", 
            "Spray", "Powder", "Medical Devices"])
        self.rack = QLineEdit()
        self.gst = QDoubleSpinBox()
        self.gst.setValue(12.0)
        self.tabs_per = QSpinBox()
        self.tabs_per.setRange(0, 1000)
        self.uses = QLineEdit()

        form.addRow("Product Name:", self.name)
        form.addRow("Manufacturer:", self.mfg)
        form.addRow("HSN Code:", self.hsn)
        form.addRow("Type:", self.type)
        form.addRow("Rack No:", self.rack)
        form.addRow("GST %:", self.gst)
        form.addRow("Tabs per Strip:", self.tabs_per)
        form.addRow("Uses/Indications:", self.uses)
        
        layout.addLayout(form)

        btns = QHBoxLayout()
        self.btn_save = QPushButton("Save Details")
        self.btn_save.clicked.connect(self.save_data)
        self.btn_save.setStyleSheet(f"background-color: {COLOR_GREEN_BTN}; color: white; padding: 8px 20px; border-radius: 4px; font-weight: bold;")
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.cancel_action)
        btn_cancel.setStyleSheet(f"background-color: #6c757d; color: white; padding: 8px 20px; border-radius: 4px;")
        
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(self.btn_save)
        layout.addSpacing(15)
        layout.addLayout(btns)

        main_layout.addWidget(self.group_box)

    def load_for_edit(self, data):
        self.edit_mode_id = data['id']
        self.group_box.setTitle("Edit Product Details")
        self.btn_save.setText("Update Product")
        self.name.setText(str(data['name']))
        self.mfg.setText(str(data['mfg']))
        self.hsn.setText(str(data['hsn']))
        self.type.setCurrentText(str(data['type']))
        self.rack.setText(str(data['rack']))
        self.gst.setValue(float(data['gst']))
        self.tabs_per.setValue(int(data['tabs']))
        self.uses.setText(str(data['uses']))

    def cancel_action(self):
        self.clear_fields()
        self.canceled.emit()

    def clear_fields(self):
        self.edit_mode_id = None
        self.group_box.setTitle("Register New Product Details")
        self.btn_save.setText("Save Details")
        self.name.clear(); self.mfg.clear(); self.hsn.clear(); self.rack.clear()
        self.gst.setValue(12.0); self.tabs_per.setValue(0); self.uses.clear()

    def save_data(self):
        if not self.name.text():
            QMessageBox.warning(self, "Input Error", "Name is required")
            return
        
        conn = database.get_connection()
        cursor = conn.cursor()
        try:
            if self.edit_mode_id:
                cursor.execute("""
                    UPDATE Product_Details 
                    SET prod_name=?, manufacturer=?, hsn_code=?, gst=?, rack_no=?, type=?, tabs_per_strip=?, uses=?
                    WHERE prod_id=?
                """, (self.name.text(), self.mfg.text(), self.hsn.text(), self.gst.value(), 
                      self.rack.text(), self.type.currentText(), self.tabs_per.value(), self.uses.text(), self.edit_mode_id))
            else:
                cursor.execute("""
                    INSERT INTO Product_Details (prod_name, manufacturer, hsn_code, gst, rack_no, type, tabs_per_strip, uses)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (self.name.text(), self.mfg.text(), self.hsn.text(), self.gst.value(), 
                      self.rack.text(), self.type.currentText(), self.tabs_per.value(), self.uses.text()))
            
            conn.commit()
            self.saved.emit()
            self.clear_fields()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()

# ==========================================
# 2. PRODUCT MASTER VIEW (The "Products" Tab)
# ==========================================
class ProductMasterView(QWidget):
    request_edit = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 10)
        
        # --- FILTER BAR FOR PRODUCTS TAB ---
        top_bar = QHBoxLayout()
        
        lbl_search = QLabel("Search Product:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type name to search...")
        self.search_input.textChanged.connect(self.load_data)
        
        lbl_type = QLabel("Type Filter:")
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "Tablet", "Capsule", "Syrup", "Injection", "Cream", 
            "Ointment", "Drops", "Personal Care & Wellness", "Spray", "Powder", "Medical Devices"])
        self.type_filter.currentTextChanged.connect(self.load_data)

        lbl_sort = QLabel("Sort By:")
        self.sort_filter = QComboBox()
        self.sort_filter.addItems([
            "ID (Lowest First)", 
            "ID (Highest First)", 
            "Name (A-Z)", 
            "Name (Z-A)", 
            "GST (Highest First)"
        ])
        self.sort_filter.currentTextChanged.connect(self.load_data)
        
        btn_refresh = QPushButton("Clear Filters")
        btn_refresh.clicked.connect(self.clear_filters_and_refresh)
        btn_refresh.setStyleSheet(f"background-color: {COLOR_NAVBAR}; color: white; padding: 6px 15px; border-radius: 4px;")

        top_bar.addWidget(lbl_search)
        top_bar.addWidget(self.search_input)
        top_bar.addWidget(lbl_type)
        top_bar.addWidget(self.type_filter)
        top_bar.addWidget(lbl_sort)
        top_bar.addWidget(self.sort_filter)
        top_bar.addWidget(btn_refresh)
        layout.addLayout(top_bar)
        
        self.table = QTableWidget()
        self.columns = ["ID", "Name", "Type", "Rack No", "Manufacturer", "HSN", "GST", "Actions"]
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        
        self.table.setColumnWidth(0, 50)  # ID
        self.table.setColumnWidth(2, 100) # Type
        self.table.setColumnWidth(3, 80)  # Rack
        self.table.setColumnWidth(4, 150) # Mfg
        self.table.setColumnWidth(5, 100) # HSN
        self.table.setColumnWidth(6, 60)  # GST
        self.table.setColumnWidth(7, 200) # Actions
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(45) 
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
        
    def clear_filters_and_refresh(self):
        self.search_input.clear()
        self.type_filter.setCurrentIndex(0)
        self.sort_filter.setCurrentIndex(0)
        self.load_data()

    def load_data(self):
        search_text = self.search_input.text().strip()
        prod_type = self.type_filter.currentText()
        sort_choice = self.sort_filter.currentText()
        
        self.table.setRowCount(0)
        conn = database.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        query = "SELECT * FROM Product_Details WHERE 1=1"
        params = []
        
        if search_text:
            query += " AND prod_name LIKE ?"
            params.append(f"%{search_text}%")
            
        if prod_type != "All Types":
            query += " AND type = ?"
            params.append(prod_type)
            
        # --- DYNAMIC SORTING LOGIC ---
        if sort_choice == "Name (A-Z)":
            query += " ORDER BY prod_name ASC"
        elif sort_choice == "Name (Z-A)":
            query += " ORDER BY prod_name DESC"
        elif sort_choice == "ID (Lowest First)":
            query += " ORDER BY prod_id ASC"
        elif sort_choice == "ID (Highest First)":
            query += " ORDER BY prod_id DESC"
        elif sort_choice == "GST (Highest First)":
            query += " ORDER BY gst DESC"
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        for row_data in rows:
            prod_id, name, mfg, hsn, gst, rack, current_prod_type, tabs, uses = row_data
            
            full_data = {
                'id': prod_id, 'name': name, 'mfg': mfg, 'hsn': hsn, 'gst': gst,
                'rack': rack, 'type': current_prod_type, 'tabs': tabs, 'uses': uses
            }
            
            display_items = [str(prod_id), name, current_prod_type, rack, mfg, hsn, str(gst), ""]
            
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            
            for i, val in enumerate(display_items):
                if i == len(display_items) - 1:
                    widget = QWidget()
                    hbox = QHBoxLayout(widget)
                    hbox.setContentsMargins(5, 2, 5, 2) 
                    hbox.setSpacing(10)

                    btn_edit = QPushButton("Edit")
                    btn_edit.setStyleSheet(f"background-color: {COLOR_EDIT}; color: black; border: none; border-radius: 3px; padding: 6px 12px; font-weight: bold;")
                    btn_edit.clicked.connect(lambda _, d=full_data: self.request_edit.emit(d))
                    
                    btn_del = QPushButton("Del")
                    btn_del.setStyleSheet(f"background-color: {COLOR_DELETE}; color: white; border: none; border-radius: 3px; padding: 6px 12px; font-weight: bold;")
                    btn_del.clicked.connect(lambda _, pid=prod_id: self.delete_product(pid))
                    
                    hbox.addWidget(btn_edit)
                    hbox.addWidget(btn_del)
                    self.table.setCellWidget(row_idx, i, widget)
                else:
                    item = QTableWidgetItem(str(val))
                    if i in [0, 2, 3, 6]: 
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(row_idx, i, item)
        conn.close()

    def delete_product(self, prod_id):
        reply = QMessageBox.warning(self, "Delete Product", 
                                    "Deleting this product will also DELETE ALL STOCK associated with it.\n\nAre you sure?", 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            conn = database.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Product_Stock WHERE prod_id = ?", (prod_id,))
                cursor.execute("DELETE FROM Product_Details WHERE prod_id = ?", (prod_id,))
                conn.commit()
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
            finally:
                conn.close()

# ==========================================
# 3. STOCK FORM (Editing existing stock)
# ==========================================
class ProductStockForm(QWidget):
    saved = pyqtSignal()
    canceled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.edit_mode_id = None 
        self.current_tps = 1 # Tabs per strip for currently edited item
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.group_box = QGroupBox("Edit Stock Entry")
        self.group_box.setFixedWidth(550)
        
        layout = QVBoxLayout(self.group_box)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(15)

        self.name_input = QLineEdit()
        self.name_input.setReadOnly(True) 

        self.batch = QLineEdit()
        
        # --- Split Quantity Inputs ---
        self.spin_strips = QSpinBox()
        self.spin_strips.setRange(0, 99999)
        self.spin_strips.setSuffix(" Strips")
        
        self.spin_loose = QSpinBox()
        self.spin_loose.setRange(0, 99999)
        self.spin_loose.setSuffix(" Tabs")

        self.min_qty = QSpinBox() 
        self.min_qty.setRange(0, 1000)
        self.min_qty.setValue(10)
        self.min_qty.setSuffix(" units (total tabs)")

        # --- Prices (Per Strip or Per Unit) ---
        self.p_price = QDoubleSpinBox()
        self.p_price.setMaximum(99999)
        self.p_price.setPrefix("₹ ")
        
        self.s_price = QDoubleSpinBox()
        self.s_price.setMaximum(99999)
        self.s_price.setPrefix("₹ ")
        
        self.lbl_price_info = QLabel("(Price per Strip)")
        self.lbl_price_info.setStyleSheet("font-size: 11px; color: grey;")

        self.mfg_date = QLineEdit()
        self.mfg_date.setPlaceholderText("MM/YY")
        self.exp_date = QLineEdit()
        self.exp_date.setPlaceholderText("MM/YY")

        form.addRow("Product:", self.name_input)
        form.addRow("Batch No:", self.batch)
        form.addRow("Stock (Strips):", self.spin_strips)
        form.addRow("Stock (Loose):", self.spin_loose)
        form.addRow(self.lbl_price_info)
        form.addRow("Buy Rate:", self.p_price)
        form.addRow("MRP (Sale Rate):", self.s_price)
        form.addRow("Mfg Date:", self.mfg_date)
        form.addRow("Exp Date:", self.exp_date)
        form.addRow("Low Stock Limit:", self.min_qty)

        layout.addLayout(form)
        btns = QHBoxLayout()
        self.btn_save = QPushButton("Update Stock")
        self.btn_save.clicked.connect(self.save_data)
        self.btn_save.setStyleSheet(f"background-color: {COLOR_BLUE_BTN}; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.cancel_action)
        btn_cancel.setStyleSheet(f"background-color: #6c757d; color: white; padding: 8px 15px; border-radius: 4px;")
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(self.btn_save)
        layout.addSpacing(10)
        layout.addLayout(btns)
        main_layout.addWidget(self.group_box)

    def load_for_edit(self, data):
        self.edit_mode_id = data['stock_id']
        self.current_tps = int(data.get('tps', 1))
        if self.current_tps < 1: self.current_tps = 1
        
        self.name_input.setText(data['name'])
        self.batch.setText(data['batch'])
        
        # Convert Total Units -> Strips + Loose
        total_units = float(data['qty'])
        strips = int(total_units // self.current_tps)
        loose = int(total_units % self.current_tps)
        
        self.spin_strips.setValue(strips)
        self.spin_loose.setValue(loose)
        self.min_qty.setValue(int(data['min_qty']))
        
        # Convert Unit Price -> Strip Price for display
        unit_pp = float(data['pp'])
        unit_sp = float(data['sp'])
        
        self.p_price.setValue(unit_pp * self.current_tps)
        self.s_price.setValue(unit_sp * self.current_tps)
        
        if self.current_tps > 1:
            self.lbl_price_info.setText(f"(Price per Strip of {self.current_tps} tabs)")
            self.spin_loose.setEnabled(True)
        else:
            self.lbl_price_info.setText("(Price per Unit/Bottle)")
            self.spin_loose.setEnabled(False) # No loose for bottles

        self.mfg_date.setText(data['mfg'])
        self.exp_date.setText(data['exp'])

    def cancel_action(self):
        self.canceled.emit()

    def save_data(self):
        # Convert UI (Strips/Strip Price) -> DB (Units/Unit Price)
        strips = self.spin_strips.value()
        loose = self.spin_loose.value()
        total_units = (strips * self.current_tps) + loose
        
        strip_pp = self.p_price.value()
        strip_sp = self.s_price.value()
        
        unit_pp = strip_pp / self.current_tps
        unit_sp = strip_sp / self.current_tps

        conn = database.get_connection()
        cursor = conn.cursor()
        try:
            if self.edit_mode_id:
                cursor.execute("""
                    UPDATE Product_Stock 
                    SET batch_no=?, quantity=?, min_qty=?, purchase_rate=?, sale_rate=?, mfg_date=?, exp_date=?
                    WHERE stock_id=?
                """, (self.batch.text(), total_units, self.min_qty.value(), 
                      unit_pp, unit_sp, self.mfg_date.text(), 
                      self.exp_date.text(), self.edit_mode_id))
            conn.commit()
            self.saved.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
class StockInterface(QWidget):
    stock_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        ensure_schema_update()
        self.setStyleSheet(STYLE_GLOBAL)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        self.stack = QStackedWidget()
        
        # === PAGE 0: DASHBOARD ===
        self.page_dashboard = QWidget()
        dash_layout = QVBoxLayout(self.page_dashboard)
        dash_layout.setContentsMargins(0, 0, 0, 0)
        dash_layout.setSpacing(15)
        
        # 1. Register Button
        self.btn_register = QPushButton("+ Register New Product")
        self.btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_register.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_NAVBAR}; 
                color: white; 
                padding: 6px 15px; 
                border-radius: 4px; 
                font-weight: bold; 
                font-size: 13px;
                border: 1px solid {COLOR_NAVBAR};
            }}
            QPushButton:hover {{
                background-color: #1565c0;
            }}
        """)
        self.btn_register.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        # 2. Main Tabs
        self.main_tabs = QTabWidget()
        self.main_tabs.setCornerWidget(self.btn_register, Qt.Corner.TopRightCorner)
        
        # --- Tab A: Stock Dashboard ---
        self.tab_stock_widget = QWidget()
        stock_layout = QVBoxLayout(self.tab_stock_widget)
        stock_layout.setContentsMargins(10, 10, 10, 10)
        
        # --- FILTER BAR FOR STOCK DASHBOARD ---
        filter_bar = QHBoxLayout()
        lbl_search = QLabel("Search:")
        self.stock_search_input = QLineEdit()
        self.stock_search_input.setPlaceholderText("Search by product or batch...")
        self.stock_search_input.textChanged.connect(self.load_data)

        lbl_type = QLabel("Type:")
        self.stock_type_filter = QComboBox()
        self.stock_type_filter.addItems(["All Types", "Tablet", "Capsule", "Syrup", "Injection", "Cream", 
            "Ointment", "Drops", "Personal Care & Wellness", "Spray", "Powder", "Medical Devices"])
        self.stock_type_filter.currentTextChanged.connect(self.load_data)

        # --- UPDATED: SORT BY FOR STOCK DASHBOARD ---
        lbl_sort = QLabel("Sort By:")
        self.stock_sort_filter = QComboBox()
        self.stock_sort_filter.addItems([
            "ID (Lowest First)", 
            "ID (Highest First)",
            "Name (A-Z)", 
            "Name (Z-A)", 
            "Expiry (Earliest First)", 
            "Expiry (Latest First)", 
            "Quantity (Lowest First)", 
            "Quantity (Highest First)",
            "Price (Lowest First)",
            "Price (Highest First)"
        ])
        self.stock_sort_filter.currentTextChanged.connect(self.load_data)

        btn_stock_refresh = QPushButton("Clear Filters")
        btn_stock_refresh.clicked.connect(self.clear_stock_filters)
        btn_stock_refresh.setStyleSheet(f"background-color: {COLOR_NAVBAR}; color: white; padding: 6px 15px; border-radius: 4px;")

        filter_bar.addWidget(lbl_search)
        filter_bar.addWidget(self.stock_search_input)
        filter_bar.addWidget(lbl_type)
        filter_bar.addWidget(self.stock_type_filter)
        filter_bar.addWidget(lbl_sort)
        filter_bar.addWidget(self.stock_sort_filter)
        filter_bar.addWidget(btn_stock_refresh)
        
        stock_layout.addLayout(filter_bar)
        
        self.inner_stock_tabs = QTabWidget()
        self.inner_stock_tabs.setStyleSheet("QTabWidget::pane { border: none; }")
        
        self.table_all = QTableWidget()
        self.table_low = QTableWidget()
        self.table_exp = QTableWidget()
        
        # Columns
        cols_std = ["ID", "Name", "Type", "Rack", "Batch", "Stock (Display)", "P.Price", "S.Price", "Mfg Date", "Exp Date", "Actions"]
        cols_exp = ["ID", "Name", "Type", "Rack", "Batch", "Stock (Display)", "P.Price", "S.Price", "Mfg Date", "Exp Date", "Status"]
        
        self.setup_table(self.table_all, cols_std)
        self.setup_table(self.table_low, cols_std)
        self.setup_table(self.table_exp, cols_exp, is_expiry_table=True)
        
        self.inner_stock_tabs.addTab(self.table_all, "All Stock")
        self.inner_stock_tabs.addTab(self.table_low, "Low Stock Alert")
        self.inner_stock_tabs.addTab(self.table_exp, "Expiring Soon")
        
        stock_layout.addWidget(self.inner_stock_tabs)
        
        # --- Tab B: Products ---
        self.master_view = ProductMasterView()
        self.master_view.request_edit.connect(self.goto_edit_product)

        self.main_tabs.addTab(self.tab_stock_widget, "Stock Dashboard")
        self.main_tabs.addTab(self.master_view, "Products")
        
        dash_layout.addWidget(self.main_tabs)
        self.stack.addWidget(self.page_dashboard)

        # === PAGE 1: DETAILS FORM ===
        self.details_form = ProductDetailsForm()
        self.details_form.saved.connect(self.on_form_success)
        self.details_form.canceled.connect(lambda: self.stack.setCurrentIndex(0))
        self.stack.addWidget(self.details_form)

        # === PAGE 2: STOCK FORM ===
        self.stock_form = ProductStockForm()
        self.stock_form.saved.connect(self.on_form_success)
        self.stock_form.canceled.connect(lambda: self.stack.setCurrentIndex(0))
        self.stack.addWidget(self.stock_form)

        self.main_layout.addWidget(self.stack)

    def clear_stock_filters(self):
        self.stock_search_input.clear()
        self.stock_type_filter.setCurrentIndex(0)
        self.stock_sort_filter.setCurrentIndex(0)
        self.load_data()

    def setup_table(self, table, columns, is_expiry_table=False):
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(40) 
        
        table.setColumnWidth(0, 50)  # ID
        table.setColumnWidth(2, 100) # Type
        table.setColumnWidth(3, 80)  # Rack
        table.setColumnWidth(4, 100) # Batch
        table.setColumnWidth(5, 120) # Qty Display
        table.setColumnWidth(6, 80)  # PP
        table.setColumnWidth(7, 80)  # SP
        table.setColumnWidth(8, 80)  # Mfg
        table.setColumnWidth(9, 80)  # Exp
        table.setColumnWidth(10, 130)# Actions/Status

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) 
        for i in range(2, 11):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)

    def goto_edit_product(self, data):
        self.details_form.load_for_edit(data)
        self.stack.setCurrentIndex(1)

    def on_form_success(self):
        self.load_data()
        self.master_view.load_data()
        self.stack.setCurrentIndex(0)
        self.stock_updated.emit()

    def load_data(self):
        search_text = self.stock_search_input.text().strip()
        prod_type = self.stock_type_filter.currentText()
        sort_choice = self.stock_sort_filter.currentText()
        
        self.table_all.setRowCount(0)
        self.table_low.setRowCount(0)
        self.table_exp.setRowCount(0)
        
        conn = database.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        query = """
            SELECT s.stock_id, d.prod_name, d.type, d.rack_no, s.batch_no, s.quantity, s.min_qty,
                   s.purchase_rate, s.sale_rate, s.mfg_date, s.exp_date, d.tabs_per_strip
            FROM Product_Details d
            JOIN Product_Stock s ON d.prod_id = s.prod_id
            WHERE 1=1
        """
        params = []
        
        if search_text:
            query += " AND (d.prod_name LIKE ? OR s.batch_no LIKE ?)"
            params.extend([f"%{search_text}%", f"%{search_text}%"])
            
        if prod_type != "All Types":
            query += " AND d.type = ?"
            params.append(prod_type)
            
        # --- DYNAMIC SORTING LOGIC ---
        if sort_choice == "ID (Lowest First)":
            query += " ORDER BY s.stock_id ASC"
        elif sort_choice == "ID (Highest First)":
            query += " ORDER BY s.stock_id DESC"
        elif sort_choice == "Name (A-Z)":
            query += " ORDER BY d.prod_name ASC"
        elif sort_choice == "Name (Z-A)":
            query += " ORDER BY d.prod_name DESC"
        elif sort_choice == "Quantity (Lowest First)":
            query += " ORDER BY s.quantity ASC"
        elif sort_choice == "Quantity (Highest First)":
            query += " ORDER BY s.quantity DESC"
        elif sort_choice == "Price (Lowest First)":
            query += " ORDER BY s.sale_rate ASC"
        elif sort_choice == "Price (Highest First)":
            query += " ORDER BY s.sale_rate DESC"
        elif sort_choice == "Expiry (Earliest First)":
            # Rough sort via text; Python finishes it below
            query += " ORDER BY s.exp_date ASC"
        elif sort_choice == "Expiry (Latest First)":
            query += " ORDER BY s.exp_date DESC"
        else:
            query += " ORDER BY s.stock_id ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # --- POST-PROCESSING SORT FOR DATES ---
        if "Expiry" in sort_choice:
            def extract_date(row):
                exp_str = row[10]
                if not exp_str: return date.max if "Earliest" in sort_choice else date.min
                try:
                    if "/" in exp_str:
                        m, y = map(int, exp_str.split('/'))
                        return date(2000+y, m, 1)
                    else:
                        return datetime.strptime(exp_str, "%Y-%m-%d").date()
                except:
                    return date.max if "Earliest" in sort_choice else date.min

            rows.sort(key=extract_date, reverse=("Latest" in sort_choice))

        today = date.today()

        for row in rows:
            stock_id, name, m_type, rack, batch, qty, min_qty, pp, sp, mfg, exp, tps = row
            
            if min_qty is None: min_qty = 0
            if qty is None: qty = 0
            if pp is None: pp = 0.0
            if sp is None: sp = 0.0
            tps = int(tps) if tps else 1
            
            # --- CONVERSION LOGIC FOR DISPLAY ---
            disp_pp = pp * tps
            disp_sp = sp * tps
            
            qty_tabs = int(qty)
            if tps > 1:
                strips = qty_tabs // tps
                loose = qty_tabs % tps
                disp_qty = f"{strips} Strips"
                if loose > 0: disp_qty += f" + {loose}"
            else:
                disp_qty = f"{qty_tabs} Units"

            days_left = 9999
            try:
                if exp and "/" in exp:
                    m, y = map(int, exp.split('/'))
                    exp_dt = date(2000+y, m, 1)
                    days_left = (exp_dt - today).days
                elif exp:
                    exp_dt = datetime.strptime(exp, "%Y-%m-%d").date()
                    days_left = (exp_dt - today).days
            except: pass

            row_data = {
                'stock_id': stock_id, 'name': name, 'batch': batch, 'qty': qty, 
                'min_qty': min_qty, 'pp': pp, 'sp': sp, 'mfg': mfg, 'exp': exp, 'tps': tps
            }

            items_std = [str(stock_id), name, m_type, rack, batch, disp_qty, f"{disp_pp:.2f}", f"{disp_sp:.2f}", mfg, exp, ""]
            
            self.add_row_std(self.table_all, items_std, row_data)
            
            if qty <= min_qty:
                self.add_row_std(self.table_low, items_std, row_data)
                
            if days_left <= 180:
                if days_left < 0:
                    status_text = "Expired"
                else:
                    months_left = days_left // 30
                    if months_left >= 1:
                        status_text = f"~{months_left} Months Left"
                    else:
                        status_text = f"{days_left} Days Left"
                
                items_exp = [str(stock_id), name, m_type, rack, batch, disp_qty, f"{disp_pp:.2f}", f"{disp_sp:.2f}", mfg, exp, status_text]
                self.add_row_exp(self.table_exp, items_exp, days_left)
                
        conn.close()

    def add_row_std(self, table, display_list, full_data):
        row = table.rowCount()
        table.insertRow(row)
        for i, val in enumerate(display_list):
            if i == len(display_list) - 1: 
                widget = QWidget()
                hbox = QHBoxLayout(widget)
                hbox.setContentsMargins(4,4,4,4)
                hbox.setSpacing(8)

                btn_edit = QPushButton("Edit")
                btn_edit.setStyleSheet(f"background-color: {COLOR_EDIT}; color: black; border: none; border-radius: 3px; padding: 5px; font-weight: bold;")
                btn_edit.clicked.connect(lambda _, d=full_data: self.edit_stock_entry(d))
                
                btn_del = QPushButton("Del")
                btn_del.setStyleSheet(f"background-color: {COLOR_DELETE}; color: white; border: none; border-radius: 3px; padding: 5px; font-weight: bold;")
                btn_del.clicked.connect(lambda _, sid=full_data['stock_id']: self.delete_batch(sid))
                
                hbox.addWidget(btn_edit)
                hbox.addWidget(btn_del)
                table.setCellWidget(row, i, widget)
            else:
                item = QTableWidgetItem(str(val))
                if i in [0, 2, 3, 5, 6, 7, 8, 9]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, i, item)

    def add_row_exp(self, table, display_list, days_left):
        row = table.rowCount()
        table.insertRow(row)
        for i, val in enumerate(display_list):
            item = QTableWidgetItem(str(val))
            if i in [0, 2, 3, 5, 6, 7, 8, 9]:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if i == len(display_list) - 1: 
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if days_left < 0:
                    item.setForeground(QBrush(QColor(COLOR_EXPIRED)))
                    item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                else:
                    item.setForeground(QBrush(QColor(COLOR_WARNING)))
                    item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            table.setItem(row, i, item)

    def edit_stock_entry(self, data):
        self.stock_form.load_for_edit(data)
        self.stack.setCurrentIndex(2)

    def delete_batch(self, stock_id):
        reply = QMessageBox.question(self, "Confirm", "Delete this batch permanently?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            conn = database.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Product_Stock WHERE stock_id = ?", (stock_id,))
                conn.commit()
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
            finally:
                conn.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StockInterface()
    window.showMaximized()
    sys.exit(app.exec())