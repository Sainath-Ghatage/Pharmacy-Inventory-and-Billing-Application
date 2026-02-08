import sys
import sqlite3
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QFrame, QMessageBox, QFormLayout,
    QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox, 
    QAbstractItemView, QTabWidget, QStackedWidget, QGroupBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QFont

import database  # Ensure this matches your DB file name

# --- COLORS & STYLES ---
COLOR_BG = "#f8f9fa"
COLOR_WHITE = "#ffffff"
COLOR_NAVBAR = "#0d47a1"
COLOR_TEXT = "#212529" # Black text
COLOR_BORDER = "#dee2e6"
COLOR_GREEN_BTN = "#198754"
COLOR_BLUE_BTN = "#0d6efd"
COLOR_DELETE = "#dc3545"
COLOR_EDIT = "#ffc107"
COLOR_SELECTION = "#e3f2fd" # Light Blue for selection
COLOR_EXPIRED= "#d20112"  # Light Red for expired items

# Global Stylesheet for consistency
STYLE_GLOBAL = f"""
    QWidget {{
        font-family: 'Segoe UI', sans-serif;
        color: {COLOR_TEXT};
    }}
    /* Fix for Inputs */
    QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit {{
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        padding: 5px;
        background-color: {COLOR_WHITE};
        color: {COLOR_TEXT};
        min-height: 25px;
    }}
    QLineEdit:focus, QComboBox:focus {{ border: 1px solid {COLOR_NAVBAR}; }}

    /* Fix for Dropdowns (Text Color) */
    QComboBox {{
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        padding: 5px;
        background-color: {COLOR_WHITE};
        color: {COLOR_TEXT}; /* Black Text */
    }}
    QComboBox QAbstractItemView {{
        background-color: {COLOR_WHITE};
        color: {COLOR_TEXT}; /* Black Text in list */
        selection-background-color: {COLOR_SELECTION};
        selection-color: {COLOR_TEXT};
    }}

    /* Fix for Popups (Message Box) */
    QMessageBox {{
        background-color: {COLOR_WHITE};
    }}
    QMessageBox QLabel {{
        color: {COLOR_TEXT}; /* Black Text */
    }}
    QMessageBox QPushButton {{
        background-color: {COLOR_BG};
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        padding: 5px 15px;
        color: {COLOR_TEXT};
    }}
"""

STYLE_LABEL = f"color: {COLOR_TEXT}; font-weight: 500;"

# --- CUSTOM TABLE WIDGET ---
class StockTable(QTableWidget):
    def __init__(self, columns):
        super().__init__()
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        # --- FIX 1: Make rows taller so buttons fit ---
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(50)  # Row height = 50px
        
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        
        # 1. ID Column
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(0, 50)

        # 2. Actions Column (Last)
        last_col_idx = len(columns) - 1
        header.setSectionResizeMode(last_col_idx, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(last_col_idx, 180) # Wide enough for text buttons

        # 3. Middle Columns
        for i in range(2, last_col_idx):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            self.setColumnWidth(i, 110)

        # 4. Name Column (Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # Styles
        self.setStyleSheet(f"""
            QTableWidget {{ 
                border: 1px solid {COLOR_BORDER}; 
                background-color: {COLOR_WHITE}; 
                border-radius: 8px; 
                gridline-color: #f0f0f0;
                color: {COLOR_TEXT};
                outline: 0;
            }}
            QHeaderView::section {{
                background-color: #e9ecef;
                color: {COLOR_TEXT};
                border: none;
                padding: 10px;
                font-weight: bold;
                border-bottom: 2px solid {COLOR_BORDER};
            }}
            QTableWidget::item {{ 
                padding: 8px; 
                border-bottom: 1px solid #f0f0f0; 
                color: {COLOR_TEXT};
            }}
            QTableWidget::item:selected {{
                background-color: {COLOR_SELECTION};
                color: {COLOR_TEXT}; 
            }}
        """)

# --- MEDICINE FORM WIDGET ---
class MedicineFormWidget(QWidget):
    save_clicked = pyqtSignal(dict)           # Save & Close
    save_add_more_clicked = pyqtSignal(dict)  # Save & Clear (Keep open)
    cancel_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.med_id = None 
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        self.setStyleSheet(f"background-color: {COLOR_WHITE}; border-radius: 10px;")

        # Title
        self.lbl_title = QLabel("Add New Medicine")
        self.lbl_title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_NAVBAR}; margin-bottom: 15px;")
        layout.addWidget(self.lbl_title)

        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # -- Fields --
        self.inp_name = QLineEdit()
        self.inp_mfg = QLineEdit()
        
        self.inp_type = QComboBox()
        types = [
            "Tablet", "Capsule", "Syrup", "Injection", "Cream", 
            "Ointment", "Drops", "Personal Care & Wellness", 
            "Spray", "Powder", "Medical Devices"
        ]
        self.inp_type.addItems(types)
        self.inp_type.currentTextChanged.connect(self.toggle_strip_fields)

        self.inp_qty = QSpinBox()
        self.inp_qty.setRange(0, 100000)
        
        self.inp_p_price = QDoubleSpinBox()
        self.inp_p_price.setRange(0, 100000)
        self.inp_p_price.setPrefix("₹ ")

        self.inp_s_price = QDoubleSpinBox()
        self.inp_s_price.setRange(0, 100000)
        self.inp_s_price.setPrefix("₹ ")

        self.inp_date_mfg = QDateEdit()
        self.inp_date_mfg.setCalendarPopup(True)
        self.inp_date_mfg.setDate(QDate.currentDate())
        
        self.inp_date_exp = QDateEdit()
        self.inp_date_exp.setCalendarPopup(True)
        self.inp_date_exp.setDate(QDate.currentDate().addYears(1))

        # -- Add Rows --
        self.add_row(form_layout, "Medicine Name:", self.inp_name)
        self.add_row(form_layout, "Manufacturer:", self.inp_mfg)
        self.add_row(form_layout, "Type:", self.inp_type)
        self.add_row(form_layout, "Total Quantity (Packs/Strips):", self.inp_qty)
        self.add_row(form_layout, "Purchase Price:", self.inp_p_price)
        self.add_row(form_layout, "Sale Price:", self.inp_s_price)
        self.add_row(form_layout, "Mfg Date:", self.inp_date_mfg)
        self.add_row(form_layout, "Exp Date:", self.inp_date_exp)

        layout.addLayout(form_layout)

        # -- Strip Details --
        self.grp_strip = QGroupBox("Strip Details (Tablets/Capsules Only)")
        self.grp_strip.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {COLOR_NAVBAR}; border: 1px solid {COLOR_BORDER}; margin-top: 10px; padding-top: 15px; }}")
        strip_layout = QFormLayout(self.grp_strip)
        
        self.inp_tabs_per_strip = QSpinBox()
        self.inp_tabs_per_strip.setRange(1, 1000)
        self.inp_tabs_per_strip.setValue(10)
        
        self.inp_rate_per_tab = QDoubleSpinBox()
        self.inp_rate_per_tab.setRange(0, 10000)
        self.inp_rate_per_tab.setPrefix("₹ ")

        self.add_row(strip_layout, "Tabs/Caps per Strip:", self.inp_tabs_per_strip)
        self.add_row(strip_layout, "Rate per Tab/Cap:", self.inp_rate_per_tab)
        
        layout.addWidget(self.grp_strip)

        # -- Buttons --
        btn_box = QHBoxLayout()
        btn_box.setContentsMargins(0, 20, 0, 0)
        btn_box.setSpacing(10)
        
        self.btn_save_more = QPushButton("Save & Add Another")
        self.btn_save_more.setFixedHeight(40)
        self.btn_save_more.clicked.connect(self.handle_save_more)
        self.btn_save_more.setStyleSheet(f"background-color: {COLOR_BLUE_BTN}; color: white; font-weight: bold; border-radius: 5px; padding: 0 15px;")

        btn_save = QPushButton("Save")
        btn_save.setFixedHeight(40)
        btn_save.clicked.connect(self.handle_save)
        btn_save.setStyleSheet(f"background-color: {COLOR_GREEN_BTN}; color: white; font-weight: bold; border-radius: 5px; padding: 0 20px;")
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(40)
        btn_cancel.clicked.connect(self.clear_and_close)
        btn_cancel.setStyleSheet(f"background-color: #6c757d; color: white; border-radius: 5px; padding: 0 20px;")
        
        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(self.btn_save_more)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)
        
        layout.addStretch() 
        self.toggle_strip_fields(self.inp_type.currentText())

    def add_row(self, layout, label_text, widget):
        lbl = QLabel(label_text)
        lbl.setStyleSheet(STYLE_LABEL)
        # widget style handled globally
        layout.addRow(lbl, widget)

    def toggle_strip_fields(self, type_text):
        is_strip_type = type_text in ["Tablet", "Capsule"]
        self.grp_strip.setVisible(is_strip_type)

    def load_data(self, data):
        self.med_id = data[0]
        self.lbl_title.setText("Edit Medicine")
        # Hide "Add Another" when editing an existing item
        self.btn_save_more.setVisible(False) 
        
        self.inp_name.setText(str(data[1]))
        self.inp_mfg.setText(str(data[2]))
        self.inp_type.setCurrentText(str(data[3]))
        
        tabs_per = data[6] if data[6] else 0
        rate_per = data[7] if data[7] else 0.0
        
        self.inp_tabs_per_strip.setValue(int(tabs_per))
        self.inp_rate_per_tab.setValue(float(rate_per))
        
        self.inp_qty.setValue(int(data[8]))
        self.inp_p_price.setValue(float(data[4]))
        self.inp_s_price.setValue(float(data[5]))

        try:
            self.inp_date_mfg.setDate(QDate.fromString(data[9], "yyyy-MM-dd"))
            self.inp_date_exp.setDate(QDate.fromString(data[10], "yyyy-MM-dd"))
        except:
            pass
        self.toggle_strip_fields(self.inp_type.currentText())

    def get_form_data(self):
        return {
            "med_id": self.med_id,
            "name": self.inp_name.text(),
            "mfg": self.inp_mfg.text(),
            "type": self.inp_type.currentText(),
            "qty": self.inp_qty.value(),
            "p_price": self.inp_p_price.value(),
            "s_price": self.inp_s_price.value(),
            "mfg_date": self.inp_date_mfg.date().toString("yyyy-MM-dd"),
            "exp_date": self.inp_date_exp.date().toString("yyyy-MM-dd"),
            "tabs_per_strip": self.inp_tabs_per_strip.value() if self.grp_strip.isVisible() else 1,
            "rate_per_tab": self.inp_rate_per_tab.value() if self.grp_strip.isVisible() else 0.0
        }

    def handle_save(self):
        data = self.get_form_data()
        self.save_clicked.emit(data)

    def handle_save_more(self):
        data = self.get_form_data()
        self.save_add_more_clicked.emit(data)

    def clear_fields_only(self):
        """Clears inputs but keeps the form open (for 'Add Another')"""
        self.med_id = None
        self.lbl_title.setText("Add New Medicine")
        self.btn_save_more.setVisible(True) # Ensure it's visible for new entries
        self.inp_name.clear()
        self.inp_mfg.clear()
        self.inp_qty.setValue(0)
        self.inp_p_price.setValue(0)
        self.inp_s_price.setValue(0)
        self.inp_name.setFocus()

    def clear_and_close(self):
        self.clear_fields_only()
        self.cancel_clicked.emit()

# --- MAIN STOCK INTERFACE ---
class StockInterface(QWidget):
    stock_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stock Management")
        self.setStyleSheet(STYLE_GLOBAL) # Apply global fixes
        self.init_ui()
        self.load_all_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # --- PAGE 0: DASHBOARD ---
        self.page_dashboard = QWidget()
        dash_layout = QVBoxLayout(self.page_dashboard)
        dash_layout.setContentsMargins(20, 20, 20, 20)

        # Top Bar
        top_bar = QHBoxLayout()
        lbl_header = QLabel("Stock Dashboard")
        lbl_header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLOR_NAVBAR};")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search Medicine...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self.load_all_data)
        
        btn_add = QPushButton("+ Add Medicine")
        btn_add.setFixedSize(140, 38)
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self.show_add_form)
        btn_add.setStyleSheet(f"background-color: {COLOR_NAVBAR}; color: white; font-weight: bold; border-radius: 5px;")

        top_bar.addWidget(lbl_header)
        top_bar.addStretch()
        top_bar.addWidget(self.search_input)
        top_bar.addWidget(btn_add)
        dash_layout.addLayout(top_bar)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {COLOR_BORDER}; background: white; border-radius: 5px; }}
            QTabBar::tab {{
                background: #e9ecef; color: {COLOR_TEXT}; padding: 10px 20px; margin-right: 2px;
                border-top-left-radius: 4px; border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{ background: {COLOR_WHITE}; border-top: 3px solid {COLOR_NAVBAR}; font-weight: bold; color: {COLOR_TEXT}; }}
        """)
        
        # 1. All Medicines Tab
        self.table_all = StockTable(["ID", "Name", "Type", "Qty", "Sale Price", "Exp Date", "Actions"])
        
        # 2. Low Stock Tab
        self.table_low = StockTable(["ID", "Name", "Type", "Qty", "Status", "Actions"])
        
        # 3. Expiry Tab
        self.table_exp = StockTable(["ID", "Name", "Exp Date", "Days Remaining", "Status", "Actions"])

        self.tabs.addTab(self.table_all, "All Medicines")
        self.tabs.addTab(self.table_low, "Low Stock")
        self.tabs.addTab(self.table_exp, "Expiry Tracker")
        
        dash_layout.addWidget(self.tabs)
        self.stacked_widget.addWidget(self.page_dashboard)

        # --- PAGE 1: FORM ---
        self.form_widget = MedicineFormWidget()
        self.form_widget.save_clicked.connect(self.process_save_and_close)
        self.form_widget.save_add_more_clicked.connect(self.process_save_and_continue)
        self.form_widget.cancel_clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.stacked_widget.addWidget(self.form_widget)

    def show_add_form(self):
        self.form_widget.clear_fields_only()
        self.stacked_widget.setCurrentIndex(1)

    def show_edit_form(self, row_data):
        self.form_widget.load_data(row_data)
        self.stacked_widget.setCurrentIndex(1)

    def load_all_data(self):
        query = self.search_input.text().strip().lower()
        
        conn = database.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        # Ensure we select 'Type' correctly
        cursor.execute("""
            SELECT Med_id, Med_name, Manufacturer, Type, Purchase_Price, Sale_Price, 
                   tabs_per_strip, rate_per_tab, Quantity, MFG_Date, EXP_Date 
            FROM Medicine ORDER BY Med_name ASC
        """)
        rows = cursor.fetchall()
        conn.close()

        self.table_all.setRowCount(0)
        self.table_low.setRowCount(0)
        self.table_exp.setRowCount(0)

        row_all, row_low, row_exp = 0, 0, 0
        today = datetime.now().date()

        for r in rows:
            name = str(r[1])
            if query and query not in name.lower():
                continue
                
            med_id = r[0]
            m_type = r[3]
            qty = r[8]
            sale_price = r[5]
            exp_date_str = r[10]

            try:
                exp_dt = datetime.strptime(exp_date_str, "%Y-%m-%d").date()
                days_left = (exp_dt - today).days
            except:
                days_left = 9999
                exp_dt = today

            # -- 1. All Medicines --
            self.table_all.insertRow(row_all)
            self.table_all.setItem(row_all, 0, QTableWidgetItem(str(med_id)))
            self.table_all.setItem(row_all, 1, QTableWidgetItem(name))
            self.table_all.setItem(row_all, 2, QTableWidgetItem(m_type))
            self.table_all.setItem(row_all, 3, QTableWidgetItem(str(qty)))
            self.table_all.setItem(row_all, 4, QTableWidgetItem(f"₹{sale_price:.2f}"))
            self.table_all.setItem(row_all, 5, QTableWidgetItem(exp_date_str))
            self.add_action_buttons(self.table_all, row_all, r)
            row_all += 1

            # -- 2. Low Stock --
            if qty < 10:
                self.table_low.insertRow(row_low)
                self.table_low.setItem(row_low, 0, QTableWidgetItem(str(med_id)))
                self.table_low.setItem(row_low, 1, QTableWidgetItem(name))
                self.table_low.setItem(row_low, 2, QTableWidgetItem(m_type))
                self.table_low.setItem(row_low, 3, QTableWidgetItem(str(qty)))
                
                status_item = QTableWidgetItem("Out of Stock" if qty == 0 else "Low Stock")
                status_item.setForeground(QColor("#dc3545") if qty == 0 else QColor("#ffc107"))
                status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                self.table_low.setItem(row_low, 4, status_item)
                
                self.add_action_buttons(self.table_low, row_low, r)
                row_low += 1

            # -- 3. Expiry --
            if days_left < 120: 
                self.table_exp.insertRow(row_exp)
                self.table_exp.setItem(row_exp, 0, QTableWidgetItem(str(med_id)))
                self.table_exp.setItem(row_exp, 1, QTableWidgetItem(name))
                self.table_exp.setItem(row_exp, 2, QTableWidgetItem(exp_date_str))
                
                days_item = QTableWidgetItem(f"{days_left} days")
                status_str = "Expired" if days_left < 0 else "Expiring Soon"
                color = QColor(COLOR_DELETE) if days_left < 0 else QColor("#fd7e14") # Orange
                
                status_item = QTableWidgetItem(status_str)
                status_item.setForeground(color)
                status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                
                self.table_exp.setItem(row_exp, 3, days_item)
                self.table_exp.setItem(row_exp, 4, status_item)
                self.add_action_buttons(self.table_exp, row_exp, r)
                
                if days_left < 0:
                    for c in range(self.table_exp.columnCount()):
                        item = self.table_exp.item(row_exp, c)
                        if item: item.setBackground(QColor(COLOR_EXPIRED))
                
                row_exp += 1

    def add_action_buttons(self, table, row, row_data):
        btn_frame = QFrame()
        layout = QHBoxLayout(btn_frame)
        layout.setContentsMargins(5, 5, 5, 5) # Add margin so buttons don't touch edges
        layout.setSpacing(10)

        # --- STYLE FOR BUTTONS ---
        # Using a variable to avoid repeating the long string
        btn_style = """
            QPushButton {
                color: white;
                border-radius: 4px;
                padding: 0px 10px;
                font-weight: bold;
                font-size: 12px;
                border: none;
            }
        """

        # --- EDIT BUTTON ---
        btn_edit = QPushButton("Edit")
        btn_edit.setFixedHeight(30) # FIX 2: Force button height
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.clicked.connect(lambda: self.show_edit_form(row_data))
        btn_edit.setStyleSheet(btn_style + f"QPushButton {{ background-color: {COLOR_NAVBAR}; }} QPushButton:hover {{ background-color: #0a3d8f; }}")

        # --- DELETE BUTTON ---
        btn_del = QPushButton("Delete")
        btn_del.setFixedHeight(30) # FIX 2: Force button height
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.clicked.connect(lambda: self.delete_medicine(row_data[0]))
        btn_del.setStyleSheet(btn_style + f"QPushButton {{ background-color: {COLOR_DELETE}; }} QPushButton:hover {{ background-color: #b02a37; }}")

        layout.addWidget(btn_edit)
        layout.addWidget(btn_del)
        
        table.setCellWidget(row, table.columnCount()-1, btn_frame)

    def save_data_to_db(self, data):
        """Helper to run the DB insert/update"""
        conn = database.get_connection()
        if not conn: return False
        cursor = conn.cursor()
        success = False
        try:
            if data['med_id']: # UPDATE
                cursor.execute("""
                    UPDATE Medicine SET 
                        Med_name=?, Manufacturer=?, Type=?, Quantity=?, 
                        Purchase_Price=?, Sale_Price=?, tabs_per_strip=?, rate_per_tab=?,
                        MFG_Date=?, EXP_Date=?
                    WHERE Med_id=?
                """, (
                    data['name'], data['mfg'], data['type'], data['qty'],
                    data['p_price'], data['s_price'], data['tabs_per_strip'], data['rate_per_tab'],
                    data['mfg_date'], data['exp_date'], data['med_id']
                ))
            else: # INSERT
                cursor.execute("""
                    INSERT INTO Medicine (
                        Med_name, Manufacturer, Type, Quantity, 
                        Purchase_Price, Sale_Price, tabs_per_strip, rate_per_tab,
                        MFG_Date, EXP_Date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['name'], data['mfg'], data['type'], data['qty'],
                    data['p_price'], data['s_price'], data['tabs_per_strip'], data['rate_per_tab'],
                    data['mfg_date'], data['exp_date']
                ))
            conn.commit()
            success = True
            self.stock_updated.emit()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))
        finally:
            conn.close()
        return success

    def process_save_and_close(self, data):
        if self.save_data_to_db(data):
            QMessageBox.information(self, "Success", "Medicine saved successfully!")
            self.stacked_widget.setCurrentIndex(0) # Go back to dashboard
            self.load_all_data()

    def process_save_and_continue(self, data):
        if self.save_data_to_db(data):
            # Show small toast/message but stay on page
            msg = QMessageBox(self)
            msg.setWindowTitle("Success")
            msg.setText("Medicine added! Ready for next entry.")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
            
            self.form_widget.clear_fields_only()
            self.load_all_data() # Update background list

    def delete_medicine(self, med_id):
        reply = QMessageBox.question(self, "Confirm Delete", "Permanently delete this medicine?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Medicine WHERE Med_id=?", (med_id,))
            conn.commit()
            conn.close()
            self.load_all_data()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StockInterface()
    window.show()
    sys.exit(app.exec())