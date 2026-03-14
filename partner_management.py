import sqlite3
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QMessageBox, QTabWidget, QDialog, QFormLayout, 
    QDialogButtonBox, QAbstractItemView, QDoubleSpinBox, QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

import database

# --- COLORS ---
COLOR_BG = "#f4f7f6"
COLOR_NAVBAR = "#0d47a1"
COLOR_ACCENT = "#1976d2"
COLOR_DELETE = "#dc3545"
COLOR_SUCCESS = "#198754"
COLOR_EDIT = "#ffc107"
COLOR_BLACK = "#000000"

class GenericPartnerTab(QWidget):
    def __init__(self, table_name, pk_column, columns_config):
        super().__init__()
        self.table_name = table_name
        self.pk_column = pk_column
        self.columns_config = columns_config
        self.sql_columns = [c[0] for c in columns_config]
        self.display_headers = [c[1] for c in columns_config]
        self.has_balance = "balance" in self.sql_columns

        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # LEFT PANEL
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        top_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(f"Search {self.table_name}...")
        self.search_input.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px; background: white; color: black;")
        self.search_input.textChanged.connect(self.load_data)
        top_bar.addWidget(self.search_input)

        btn_add = QPushButton(f"+ Add {self.table_name}")
        btn_add.setStyleSheet(f"background-color: {COLOR_ACCENT}; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
        btn_add.clicked.connect(self.add_entry)
        top_bar.addWidget(btn_add)
        left_layout.addLayout(top_bar)

        self.table = QTableWidget()
        col_count = len(self.display_headers) + 2
        headers = ["ID"] + self.display_headers + ["Actions"]
        self.table.setColumnCount(col_count)
        self.table.setHorizontalHeaderLabels(headers)
        
        # --- RESIZE LOGIC START ---
        
        # 1. MAKE ROWS TALLER (Row Height)
        self.table.verticalHeader().setDefaultSectionSize(50) 

        # 2. COLUMN WIDTHS
        # Default: Stretch all columns
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # ID Column: Fit to content (Small)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        # Actions Column: FIXED WIDTH (Wide enough for buttons)
        action_col_idx = col_count - 1
        self.table.horizontalHeader().setSectionResizeMode(action_col_idx, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(action_col_idx, 200) # Increased to 200px
        
        # --- RESIZE LOGIC END ---

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #ddd; background: white; color: #333; } 
            QHeaderView::section { background: #e0e0e0; color: #333; padding: 5px; font-weight: bold; border: 1px solid #ccc;}
            QTableWidget::item { padding: 5px; color: black; }
            QTableWidget::item:selected { background-color: #e3f2fd; color: black; }
        """)
        
        self.table.mousePressEvent = self.on_table_mouse_press
        self.table.cellClicked.connect(self.handle_cell_click) 
        
        left_layout.addWidget(self.table)

        # RIGHT PANEL
        self.side_panel = QFrame()
        self.side_panel.setFrameShape(QFrame.Shape.StyledPanel)
        self.side_panel.setStyleSheet("""
            QFrame { background-color: white; border-radius: 5px; border: 1px solid #ddd; }
            QLabel { color: black; }
            QGroupBox { color: black; font-weight: bold; border: 1px solid #ccc; margin-top: 10px; padding: 10px; }
            QGroupBox::title { color: black; subcontrol-origin: margin; left: 10px; padding: 0 3px; }
        """)
        self.side_panel.setFixedWidth(400)
        self.side_panel.hide() 

        self.side_layout = QVBoxLayout(self.side_panel)
        self.side_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.main_layout.addWidget(left_widget, 70) 
        self.main_layout.addWidget(self.side_panel, 30) 

    def on_table_mouse_press(self, event):
        if self.table.itemAt(event.pos()) is None:
            self.side_panel.hide()
            self.table.clearSelection()
        QTableWidget.mousePressEvent(self.table, event)

    def load_data(self):
        query = self.search_input.text().strip()
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cols_str = ", ".join(self.sql_columns)
        sql = f"SELECT {self.pk_column}, {cols_str} FROM {self.table_name}"
        params = []
        if query:
            search_col = self.sql_columns[0]
            sql += f" WHERE {search_col} LIKE ?"
            params.append(f"%{query}%")
        sql += f" ORDER BY {self.pk_column} DESC"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            pk_id = str(row[0])
            self.table.setItem(i, 0, QTableWidgetItem(pk_id))
            
            row_data_list = [str(val) if val is not None else "" for val in row[1:]]

            for j, val in enumerate(row[1:]):
                col_name = self.sql_columns[j]
                
                # --- NEW LOGIC: Check if it's the balance column and format it ---
                if col_name == "balance" and val is not None:
                    try:
                        val = f"{float(val):.2f}"
                    except (ValueError, TypeError):
                        pass
                
                item = QTableWidgetItem(str(val) if val is not None else "")
                self.table.setItem(i, j+1, item)
            
            # ACTIONS COLUMN
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(5, 5, 5, 5) # Added margins
            layout.setSpacing(10)

            btn_edit = QPushButton("Edit")
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.setStyleSheet(f"background-color: {COLOR_EDIT}; color: black; border: none; padding: 5px 10px; border-radius: 3px; font-weight: bold;")
            btn_edit.clicked.connect(lambda _, pid=pk_id, d=row_data_list: self.open_form(pid, d))

            btn_del = QPushButton("Delete")
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setStyleSheet(f"QPushButton {{ background-color: {COLOR_DELETE}; color: white; border: none; padding: 5px 10px; border-radius: 4px; font-weight: bold; }} QPushButton:hover {{ background-color: #c82333; }}")
            btn_del.clicked.connect(lambda _, pid=pk_id: self.confirm_delete_id(pid))

            layout.addWidget(btn_edit)
            layout.addWidget(btn_del)
            self.table.setCellWidget(i, len(self.display_headers) + 1, container)

    def handle_cell_click(self, row, col):
        actions_col_index = self.table.columnCount() - 1
        if col != actions_col_index:
            pk_id = self.table.item(row, 0).text()
            self.show_details(pk_id, row)

    def show_details(self, pk_id, row):
        self.side_panel.show()
        while self.side_layout.count():
            child = self.side_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        # Header
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        name_item = self.table.item(row, 1) 
        name_text = name_item.text() if name_item else "Unknown"
        
        lbl_name = QLabel(name_text)
        lbl_name.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_NAVBAR};")
        
        btn_close = QPushButton("X")
        btn_close.setFixedSize(30, 30)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("background-color: #ffebee; color: #d32f2f; border: none; border-radius: 15px; font-weight: bold;")
        btn_close.clicked.connect(self.side_panel.hide)

        header_layout.addWidget(lbl_name)
        header_layout.addStretch()
        header_layout.addWidget(btn_close)
        self.side_layout.addWidget(header_widget)

        lbl_id = QLabel(f"ID: {pk_id} | Type: {self.table_name}")
        lbl_id.setStyleSheet("color: gray; font-size: 12px; margin-bottom: 10px;")
        self.side_layout.addWidget(lbl_id)

        # Contact Details
        details_box = QGroupBox("Contact Details")
        grid = QFormLayout()
        for i, header in enumerate(self.display_headers):
            val = self.table.item(row, i+1).text()
            grid.addRow(f"{header}:", QLabel(val))
        details_box.setLayout(grid)
        self.side_layout.addWidget(details_box)

        # Balance
        if self.has_balance:
            bal_idx = self.sql_columns.index('balance')
            balance_val = self.table.item(row, bal_idx + 1).text()
            try: current_balance = float(balance_val)
            except (ValueError, TypeError): current_balance = 0.0

            bal_box = QGroupBox("Account Balance")
            bal_layout = QVBoxLayout()
            lbl_bal = QLabel(f"₹ {current_balance:.2f}")
            
            # Color logic: Red if not 0, Green if 0
            color_bal = COLOR_DELETE if current_balance != 0 else COLOR_SUCCESS
            lbl_bal.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color_bal};")
            bal_layout.addWidget(lbl_bal)

            # --- UPDATED SETTLE LOGIC (Supports Negative and Positive Balances) ---
            if current_balance != 0:
                settle_layout = QHBoxLayout()
                self.spin_settle = QDoubleSpinBox()
                self.spin_settle.setPrefix("₹ ")
                
                # Use absolute value for the max input limit
                abs_balance = abs(current_balance)
                self.spin_settle.setMaximum(abs_balance)
                self.spin_settle.setValue(abs_balance)
                self.spin_settle.setStyleSheet("color: black;")
                
                btn_settle = QPushButton("Settle")
                btn_settle.setStyleSheet(f"background-color: {COLOR_SUCCESS}; color: white; border: none; padding: 5px; border-radius: 3px;")
                btn_settle.clicked.connect(lambda: self.settle_balance(pk_id, current_balance))
                
                settle_layout.addWidget(self.spin_settle)
                settle_layout.addWidget(btn_settle)
                bal_layout.addLayout(settle_layout)
                
            bal_box.setLayout(bal_layout)
            self.side_layout.addWidget(bal_box)

        # History
        can_show_bills = False
        bill_col = None
        if self.table_name == "Customer":
            can_show_bills = True; bill_col = "patient_name"
        elif self.table_name == "Doctor":
            can_show_bills = True; bill_col = "doctor_name"

        if can_show_bills:
            hist_box = QGroupBox("Bill History")
            hist_layout = QVBoxLayout()
            hist_table = QTableWidget()
            hist_table.setColumnCount(3)
            hist_table.setHorizontalHeaderLabels(["ID", "Date", "Amount"])
            hist_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            hist_table.verticalHeader().setVisible(False)
            hist_table.setStyleSheet("border: none; font-size: 11px; color: black;")
            
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT Bill_id, bill_date, total_sum FROM Bill WHERE {bill_col} = ? ORDER BY Bill_id DESC LIMIT 20", (name_text,))
            bills = cursor.fetchall()
            conn.close()
            
            hist_table.setRowCount(len(bills))
            for b_idx, b_row in enumerate(bills):
                hist_table.setItem(b_idx, 0, QTableWidgetItem(str(b_row[0])))
                hist_table.setItem(b_idx, 1, QTableWidgetItem(str(b_row[1])))
                hist_table.setItem(b_idx, 2, QTableWidgetItem(f"₹{b_row[2]:.2f}"))
            
            hist_layout.addWidget(hist_table)
            hist_box.setLayout(hist_layout)
            self.side_layout.addWidget(hist_box)
        
        self.side_layout.addStretch()

    def settle_balance(self, pk_id, current_bal):
        amount = self.spin_settle.value()
        if amount <= 0: return
        
        # --- NEW LOGIC: Move balance closer to zero whether it's positive or negative ---
        if current_bal > 0:
            new_bal = current_bal - amount
        else:
            new_bal = current_bal + amount
            
        conn = database.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f"UPDATE {self.table_name} SET balance = ? WHERE {self.pk_column} = ?", (new_bal, pk_id))
            conn.commit()
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Success")
            msg_box.setText(f"Payment of ₹{amount} recorded.")
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setStyleSheet("QLabel { color: black; } QPushButton { color: black; background-color: white; border: 1px solid gray; padding: 5px; }")
            msg_box.exec()
            self.load_data() 
            self.side_panel.hide() 
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()

    def confirm_delete_id(self, pk_id):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Delete")
        msg_box.setText(f"Are you sure you want to delete ID {pk_id} from {self.table_name}?")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setStyleSheet("QLabel { color: black; } QPushButton { color: black; background-color: white; border: 1px solid gray; padding: 5px; }")
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.delete_entry(pk_id)

    def delete_entry(self, pk_id):
        conn = database.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f"DELETE FROM {self.table_name} WHERE {self.pk_column}=?", (pk_id,))
            conn.commit()
            self.load_data()
            self.side_panel.hide()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()

    def add_entry(self):
        self.open_form()

    def open_form(self, pk_id=None, current_data=None):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{'Edit' if pk_id else 'Add'} {self.table_name}")
        dialog.setFixedSize(400, 450)
        dialog.setStyleSheet("""
            QDialog { background-color: white; }
            QLabel { color: #333; font-weight: bold; }
            QLineEdit { color: #333; background-color: #f9f9f9; border: 1px solid #ccc; padding: 5px; border-radius: 4px; }
            QLineEdit:focus { border: 1px solid #0d47a1; }
            QPushButton { background-color: #0d47a1; color: white; padding: 8px; border-radius: 4px; }
        """)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        form.setSpacing(15)

        inputs = []
        for i, (col_sql, col_header) in enumerate(self.columns_config):
            le = QLineEdit()
            if current_data:
                le.setText(str(current_data[i]))
            form.addRow(f"{col_header}:", le)
            inputs.append(le)
        
        layout.addLayout(form)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(lambda: self.validate_and_save(dialog, pk_id, inputs))
        btns.rejected.connect(dialog.reject)
        layout.addWidget(btns)
        dialog.exec()

    def validate_and_save(self, dialog, pk_id, inputs):
        data = [inp.text().strip() for inp in inputs]
        input_map = { self.sql_columns[i]: data[i] for i in range(len(self.sql_columns)) }
        
        for col in ['Phone', 'contact']:
            if col in input_map:
                val = input_map[col]
                if val and (not val.isdigit() or len(val) != 10):
                    QMessageBox.warning(dialog, "Validation Error", f"{col} must be exactly 10 digits.")
                    return

        if 'gstin' in input_map:
            val = input_map['gstin']
            if val and (len(val) != 15 or not val.isalnum()):
                QMessageBox.warning(dialog, "Validation Error", "GSTIN must be exactly 15 alphanumeric characters.")
                return

        for col in ['Email', 'email']:
            if col in input_map:
                val = input_map[col]
                if val: 
                    regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
                    if not re.match(regex, val):
                        QMessageBox.warning(dialog, "Validation Error", "Invalid Email Format.")
                        return

        self.save_to_db(pk_id, data)
        dialog.accept()

    def save_to_db(self, pk_id, data):
        conn = database.get_connection()
        cursor = conn.cursor()
        
        if pk_id:
            set_clause = ", ".join([f"{col}=?" for col in self.sql_columns])
            sql = f"UPDATE {self.table_name} SET {set_clause} WHERE {self.pk_column}=?"
            cursor.execute(sql, data + [pk_id])
        else:
            placeholders = ", ".join(["?"] * len(data))
            cols_str = ", ".join(self.sql_columns)
            sql = f"INSERT INTO {self.table_name} ({cols_str}) VALUES ({placeholders})"
            cursor.execute(sql, data)
            
        conn.commit()
        conn.close()
        self.load_data()

class PartnerManagementInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {COLOR_BG}; font-family: 'Segoe UI', sans-serif;")
        
        main_layout = QVBoxLayout(self)
        
        lbl_title = QLabel("Partner Management")
        lbl_title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {COLOR_NAVBAR}; margin-bottom: 10px;")
        main_layout.addWidget(lbl_title)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #ccc; background: white; border-radius: 5px; }
            QTabBar::tab { background: #e0e0e0; color: #333; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: white; color: #0d47a1; border-bottom: 2px solid #0d47a1; font-weight: bold; }
        """)
        
        # 1. Customers
        cust_config = [
            ('Name', 'Name'),
            ('Phone', 'Phone'),
            ('Email', 'Email'),
            ('Address', 'Address'),
            ('Notes', 'Notes'),
            ('balance', 'Balance') 
        ]
        self.tab_customer = GenericPartnerTab("Customer", "Cust_id", cust_config)
        
        # 2. Doctors
        doc_config = [
            ('Name', 'Doctor Name'),
            ('Specialization', 'Specialization'),
            ('Hospital', 'Hospital/Clinic'),
            ('Phone', 'Contact'),
            ('Email', 'Email')
        ]
        self.tab_doctor = GenericPartnerTab("Doctor", "Doc_id", doc_config)
        
        # 3. Suppliers
        sup_config = [
            ('Sup_name', 'Supplier Name'),
            ('supplier_type', 'Type'),
            ('contact', 'Contact No'),
            ('email', 'Email'),
            ('gstin', 'GSTIN'),
            ('address', 'Address'),
            ('balance', 'Balance')
        ]
        self.tab_supplier = GenericPartnerTab("Supplier", "Supp_id", sup_config)
        
        self.tabs.addTab(self.tab_customer, "Customers")
        self.tabs.addTab(self.tab_doctor, "Doctors")
        self.tabs.addTab(self.tab_supplier, "Suppliers")
        
        main_layout.addWidget(self.tabs)