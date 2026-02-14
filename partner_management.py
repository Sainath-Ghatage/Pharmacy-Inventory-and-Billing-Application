import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QMessageBox, QTabWidget, QDialog, QFormLayout, 
    QDialogButtonBox, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

import database

# --- COLORS ---
COLOR_BG = "#f4f7f6"
COLOR_NAVBAR = "#0d47a1"
COLOR_ACCENT = "#1976d2"
COLOR_DELETE = "#dc3545"

class GenericPartnerTab(QWidget):
    """
    A reusable widget to manage CRUD for Customers, Doctors, and Suppliers.
    """
    def __init__(self, table_name, pk_column, columns_config):
        """
        table_name: SQL Table Name (e.g., 'Customer')
        pk_column: Primary Key Column Name (e.g., 'Cust_id')
        columns_config: List of tuples [('SQL_Col_Name', 'Display Header'), ...]
        """
        super().__init__()
        self.table_name = table_name
        self.pk_column = pk_column
        self.columns_config = columns_config
        self.sql_columns = [c[0] for c in columns_config]
        self.display_headers = [c[1] for c in columns_config]
        
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Top Bar (Search + Add)
        top_bar = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(f"Search {self.table_name}...")
        self.search_input.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px; color: #333; background: white;")
        self.search_input.textChanged.connect(self.load_data)
        top_bar.addWidget(self.search_input)

        btn_add = QPushButton(f"+ Add {self.table_name}")
        btn_add.setStyleSheet(f"background-color: {COLOR_ACCENT}; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
        btn_add.clicked.connect(self.add_entry)
        top_bar.addWidget(btn_add)
        
        layout.addLayout(top_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.display_headers) + 2) # +2 for ID and Actions
        self.table.setHorizontalHeaderLabels(["ID"] + self.display_headers + ["Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        self.table.setStyleSheet("""
            QTableWidget { border: none; background: white; color: #333; } 
            QHeaderView::section { background: #e0e0e0; color: #333; padding: 5px; font-weight: bold; }
            QTableWidget::item { padding: 5px; }
        """)
        
        self.table.cellClicked.connect(self.handle_cell_click)
        self.table.cellDoubleClicked.connect(self.edit_entry_by_row)
        
        layout.addWidget(self.table)

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
            # ID Column
            self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            
            # Data Columns
            for j, val in enumerate(row[1:]):
                self.table.setItem(i, j+1, QTableWidgetItem(str(val) if val else ""))
            
            # Action Column
            btn_del = QTableWidgetItem("Delete")
            btn_del.setForeground(QColor(COLOR_DELETE))
            btn_del.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            font = btn_del.font()
            font.setBold(True)
            font.setUnderline(True)
            btn_del.setFont(font)
            self.table.setItem(i, len(self.display_headers) + 1, btn_del)

    def handle_cell_click(self, row, col):
        actions_col_index = len(self.display_headers) + 1
        if col == actions_col_index:
            self.confirm_delete(row)

    def confirm_delete(self, row):
        pk_id = self.table.item(row, 0).text()
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Delete")
        msg_box.setText(f"Are you sure you want to delete ID {pk_id} from {self.table_name}?")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        # --- FIX: Apply Black Text Color to Message Box ---
        msg_box.setStyleSheet("QLabel { color: black; } QPushButton { color: black; background-color: white; border: 1px solid gray; padding: 5px; }")
        
        ret = msg_box.exec()
        
        if ret == QMessageBox.StandardButton.Yes:
            self.delete_entry(pk_id)

    def delete_entry(self, pk_id):
        conn = database.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f"DELETE FROM {self.table_name} WHERE {self.pk_column}=?", (pk_id,))
            conn.commit()
            
            # --- FIX: Apply Black Text Color to Success Box ---
            msg = QMessageBox(self)
            msg.setWindowTitle("Success")
            msg.setText("Entry deleted successfully.")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setStyleSheet("QLabel { color: black; } QPushButton { color: black; background-color: white; border: 1px solid gray; padding: 5px; }")
            msg.exec()
            
            self.load_data()
        except Exception as e:
            # --- FIX: Apply Black Text Color to Error Box ---
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText(f"Could not delete: {str(e)}")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setStyleSheet("QLabel { color: black; } QPushButton { color: black; background-color: white; border: 1px solid gray; padding: 5px; }")
            msg.exec()
        finally:
            conn.close()

    def add_entry(self):
        self.open_form()

    def edit_entry_by_row(self, row, col):
        actions_col_index = len(self.display_headers) + 1
        if col == actions_col_index:
            return

        pk_id = self.table.item(row, 0).text()
        
        current_data = []
        for i in range(len(self.sql_columns)):
            item = self.table.item(row, i+1)
            current_data.append(item.text() if item else "")
            
        self.open_form(pk_id, current_data)

    def open_form(self, pk_id=None, current_data=None):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{'Edit' if pk_id else 'Add'} {self.table_name}")
        dialog.setFixedSize(400, 350)
        
        dialog.setStyleSheet("""
            QDialog { background-color: white; }
            QLabel { color: #333333; font-weight: bold; font-size: 14px; }
            QLineEdit { color: #333333; background-color: #f9f9f9; border: 1px solid #cccccc; border-radius: 5px; padding: 6px; }
            QLineEdit:focus { border: 1px solid #0d47a1; background-color: #ffffff; }
            QPushButton { background-color: #0d47a1; color: white; border-radius: 5px; padding: 8px 16px; font-weight: bold; }
            QPushButton:hover { background-color: #1976d2; }
        """)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        form.setSpacing(15)

        inputs = []
        for i, (col_sql, col_header) in enumerate(self.columns_config):
            le = QLineEdit()
            if current_data:
                le.setText(current_data[i])
            form.addRow(f"{col_header}:", le)
            inputs.append(le)
        
        layout.addLayout(form)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addWidget(btns)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = [inp.text() for inp in inputs]
            self.save_to_db(pk_id, data)

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
        
        # 1. Customers Config
        cust_config = [
            ('Name', 'Name'),
            ('Phone', 'Phone'),
            ('Email', 'Email'),
            ('Address', 'Address'),
            ('Notes', 'Notes')
        ]
        self.tab_customer = GenericPartnerTab("Customer", "Cust_id", cust_config)
        
        # 2. Doctors Config
        doc_config = [
            ('Name', 'Doctor Name'),
            ('Specialization', 'Specialization'),
            ('Hospital', 'Hospital/Clinic'),
            ('Phone', 'Contact'),
            ('Email', 'Email')
        ]
        self.tab_doctor = GenericPartnerTab("Doctor", "Doc_id", doc_config)
        
        # 3. Suppliers Config
        sup_config = [
            ('Sup_name', 'Supplier Name'),
            ('supplier_type', 'Type'),
            ('contact', 'Contact No'),
            ('email', 'Email'),
            ('gstin', 'GSTIN'),
            ('address', 'Address')
        ]
        self.tab_supplier = GenericPartnerTab("Supplier", "Supp_id", sup_config)
        
        self.tabs.addTab(self.tab_customer, "Customers")
        self.tabs.addTab(self.tab_doctor, "Doctors")
        self.tabs.addTab(self.tab_supplier, "Suppliers")
        
        main_layout.addWidget(self.tabs)