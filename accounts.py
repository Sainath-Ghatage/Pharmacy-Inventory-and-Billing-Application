import sys
import sqlite3
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QComboBox, QDateEdit, QDoubleSpinBox, QFrame, QMessageBox, 
    QTextEdit, QAbstractItemView, QSizePolicy, QSpinBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont

import database

# --- COLORS ---
COLOR_BG = "#f8f9fa"
COLOR_WHITE = "#ffffff"
COLOR_NAVBAR = "#0d47a1"
COLOR_TEXT = "#000000"    # Pure Black
COLOR_ACCENT = "#198754"  # Green
COLOR_DELETE = "#dc3545"  # Red
COLOR_BORDER = "#dee2e6"

class AccountsInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Accounts & Expenses")
        self.setStyleSheet(f"background-color: {COLOR_BG}; font-family: 'Segoe UI', sans-serif; color: {COLOR_TEXT};")
        
        self.init_ui()
        
        # Set default filter to current date
        today = datetime.date.today()
        self.cmb_filter_month.setCurrentIndex(today.month - 1)
        self.spin_filter_year.setValue(today.year)
        
        self.load_expenses()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Title
        lbl_title = QLabel("Expense Management")
        lbl_title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLOR_NAVBAR};")
        main_layout.addWidget(lbl_title)

        # Content Split: Left (Form) | Right (Table)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # --- LEFT: ADD EXPENSE FORM ---
        form_frame = QFrame()
        form_frame.setFixedWidth(450) # <-- INCREASED WIDTH HERE (Was 350)
        form_frame.setStyleSheet(f"background-color: {COLOR_WHITE}; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)

        lbl_add = QLabel("Add New Expense")
        lbl_add.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_NAVBAR}; margin-bottom: 5px;")
        form_layout.addWidget(lbl_add)

        # Expense Type
        form_layout.addWidget(QLabel("Expense Type:"))
        self.cmb_type = QComboBox()
        self.cmb_type.addItems([
            "Electricity Bill", "Water Bill", "Shop Rent", 
            "License Renewal", "Employee Salary", "Taxes", 
            "Maintenance", "Internet/Wi-Fi", "Stationery", "Other"
        ])
        self.cmb_type.currentTextChanged.connect(self.toggle_other_field)
        self.cmb_type.setStyleSheet(self.input_style())
        form_layout.addWidget(self.cmb_type)

        # Custom Description
        self.txt_other = QLineEdit()
        self.txt_other.setPlaceholderText("Specify other expense...")
        self.txt_other.setStyleSheet(self.input_style())
        self.txt_other.setVisible(False)
        form_layout.addWidget(self.txt_other)

        # Amount
        form_layout.addWidget(QLabel("Amount (₹):"))
        self.spin_amount = QDoubleSpinBox()
        self.spin_amount.setRange(0, 9999999)
        self.spin_amount.setPrefix("₹ ")
        self.spin_amount.setStyleSheet(self.input_style())
        form_layout.addWidget(self.spin_amount)

        # Date
        form_layout.addWidget(QLabel("Date:"))
        self.date_expense = QDateEdit(QDate.currentDate())
        self.date_expense.setCalendarPopup(True)
        self.date_expense.setStyleSheet(self.input_style())
        form_layout.addWidget(self.date_expense)

        # Payment Mode
        form_layout.addWidget(QLabel("Payment Mode:"))
        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["Cash", "UPI", "Bank Transfer", "Cheque", "Card"])
        self.cmb_mode.setStyleSheet(self.input_style())
        form_layout.addWidget(self.cmb_mode)

        # Notes
        form_layout.addWidget(QLabel("Notes / Description:"))
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("Optional details...")
        self.txt_notes.setFixedHeight(80) # Slightly taller for better typing
        self.txt_notes.setStyleSheet(self.input_style())
        form_layout.addWidget(self.txt_notes)

        # Save Button
        self.btn_save = QPushButton("Save Expense")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self.save_expense)
        self.btn_save.setFixedHeight(45) # Increased button height
        self.btn_save.setStyleSheet(f"""
            QPushButton {{ background-color: {COLOR_ACCENT}; color: white; font-weight: bold; border-radius: 5px; font-size: 15px; }}
            QPushButton:hover {{ background-color: #146c43; }}
        """)
        form_layout.addWidget(self.btn_save)
        
        form_layout.addStretch()
        content_layout.addWidget(form_frame)

        # --- RIGHT: EXPENSE HISTORY TABLE ---
        table_frame = QFrame()
        table_frame.setStyleSheet(f"background-color: {COLOR_WHITE}; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)

        # --- NEW FILTER BAR ---
        filter_bar = QHBoxLayout()
        filter_bar.setContentsMargins(15, 15, 15, 5)
        filter_bar.setSpacing(10)

        filter_bar.addWidget(QLabel("<b>Filter:</b>"))

        # Month Selector
        self.cmb_filter_month = QComboBox()
        self.cmb_filter_month.addItems([
            "January", "February", "March", "April", "May", "June", 
            "July", "August", "September", "October", "November", "December"
        ])
        self.cmb_filter_month.setFixedWidth(140) # <-- INCREASED WIDTH (Was 120)
        self.cmb_filter_month.setStyleSheet(self.input_style())
        filter_bar.addWidget(self.cmb_filter_month)

        # Year Selector
        self.spin_filter_year = QSpinBox()
        self.spin_filter_year.setRange(2000, 2100)
        self.spin_filter_year.setFixedWidth(100) # <-- INCREASED WIDTH (Was 80)
        self.spin_filter_year.setStyleSheet(self.input_style())
        filter_bar.addWidget(self.spin_filter_year)

        # View Button
        btn_view = QPushButton("Show Expenses")
        btn_view.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_view.setFixedHeight(35)
        btn_view.clicked.connect(self.load_expenses)
        btn_view.setStyleSheet(f"""
            QPushButton {{ background-color: {COLOR_NAVBAR}; color: white; border-radius: 4px; padding: 5px 15px; font-weight: bold; }}
        """)
        filter_bar.addWidget(btn_view)

        filter_bar.addStretch()

        # Total Label
        self.lbl_total_period = QLabel("Total: ₹0.00")
        self.lbl_total_period.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLOR_DELETE};")
        filter_bar.addWidget(self.lbl_total_period)

        table_layout.addLayout(filter_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Date", "Category", "Description", "Amount", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 80)
        
        self.table.verticalHeader().setDefaultSectionSize(45)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        self.table.setStyleSheet(f"""
            QTableWidget {{ border: none; gridline-color: #eee; color: {COLOR_TEXT}; background-color: {COLOR_WHITE}; }}
            QHeaderView::section {{ background-color: #f1f3f4; padding: 8px; border: none; font-weight: bold; color: {COLOR_TEXT}; border-bottom: 1px solid #ccc; }}
            QTableWidget::item {{ color: {COLOR_TEXT}; padding: 5px; }}
            QTableWidget::item:selected {{ background-color: #d0e1f5; color: {COLOR_TEXT}; }}
        """)
        
        table_layout.addWidget(self.table)
        content_layout.addWidget(table_frame)

        main_layout.addLayout(content_layout)

    def input_style(self):
        return f"""
            QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox, QTextEdit {{
                border: 1px solid {COLOR_BORDER}; 
                border-radius: 4px; 
                padding: 8px; /* Increased padding */
                min-height: 25px; /* Taller input fields */
                background: {COLOR_WHITE}; 
                color: {COLOR_TEXT}; 
            }}
            QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QSpinBox:focus, QTextEdit:focus {{ 
                border: 1px solid {COLOR_NAVBAR}; 
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLOR_WHITE};
                color: {COLOR_TEXT};
                selection-background-color: #d0e1f5;
                selection-color: {COLOR_TEXT};
            }}
        """

    def toggle_other_field(self, text):
        self.txt_other.setVisible(text == "Other")

    def save_expense(self):
        exp_type = self.cmb_type.currentText()
        if exp_type == "Other":
            custom_type = self.txt_other.text().strip()
            if not custom_type:
                QMessageBox.warning(self, "Input Error", "Please specify the expense name.")
                return
            description = f"{custom_type} - {self.txt_notes.toPlainText().strip()}"
        else:
            description = self.txt_notes.toPlainText().strip()

        amount = self.spin_amount.value()
        date = self.date_expense.date().toString("yyyy-MM-dd")
        mode = self.cmb_mode.currentText()

        if amount <= 0:
            QMessageBox.warning(self, "Input Error", "Amount must be greater than 0.")
            return

        conn = database.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO Expenses (expense_type, description, amount, expense_date, payment_mode)
                VALUES (?, ?, ?, ?, ?)
            """, (exp_type, description, amount, date, mode))
            conn.commit()
            
            # Using the customized message box to ensure black text
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Success")
            msg_box.setText("Expense added successfully.")
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setStyleSheet("QLabel { color: black; } QPushButton { color: black; background-color: white; border: 1px solid gray; padding: 5px; }")
            msg_box.exec()
            
            self.clear_form()
            
            # Update filter to the date of the added expense so the user sees it immediately
            exp_date_obj = self.date_expense.date()
            self.cmb_filter_month.setCurrentIndex(exp_date_obj.month() - 1)
            self.spin_filter_year.setValue(exp_date_obj.year())
            
            self.load_expenses()
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", str(e))
        finally:
            conn.close()

    def clear_form(self):
        self.cmb_type.setCurrentIndex(0)
        self.txt_other.clear()
        self.spin_amount.setValue(0)
        self.txt_notes.clear()
        self.date_expense.setDate(QDate.currentDate())

    def load_expenses(self):
        # 1. Get Filter Values
        selected_month_idx = self.cmb_filter_month.currentIndex() + 1
        selected_year = self.spin_filter_year.value()
        
        # SQLite format: YYYY-MM
        filter_str = f"{selected_year}-{selected_month_idx:02d}"
        
        conn = database.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        # 2. Filter Query
        try:
            cursor.execute("""
                SELECT expense_id, expense_date, expense_type, description, amount 
                FROM Expenses 
                WHERE strftime('%Y-%m', expense_date) = ?
                ORDER BY expense_date DESC
            """, (filter_str,))
            rows = cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Query Error: {e}")
            rows = []

        self.table.setRowCount(0)
        total_period = 0.0
        
        for i, (eid, date, etype, desc, amt) in enumerate(rows):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(eid)))
            self.table.setItem(i, 1, QTableWidgetItem(date))
            self.table.setItem(i, 2, QTableWidgetItem(etype))
            self.table.setItem(i, 3, QTableWidgetItem(desc))
            
            # Format Amount Item
            amt_item = QTableWidgetItem(f"₹{amt:.2f}")
            amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 4, amt_item)
            
            # Delete Button
            btn_del = QPushButton("Delete")
            btn_del.setStyleSheet(f"QPushButton {{ background-color: {COLOR_DELETE}; color: white; font-weight: bold; border: none; border-radius: 4px; padding: 5px; }} QPushButton:hover {{ background-color: #c82333; }}")
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.clicked.connect(lambda _, x=eid: self.delete_expense(x))
            self.table.setCellWidget(i, 5, btn_del)

            total_period += amt

        # 3. Update Label
        month_name = self.cmb_filter_month.currentText()
        self.lbl_total_period.setText(f"Total ({month_name} {selected_year}): ₹{total_period:,.2f}")
        
        conn.close()

    def delete_expense(self, exp_id):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Delete")
        msg_box.setText("Are you sure you want to delete this expense entry?")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setStyleSheet("QLabel { color: black; } QPushButton { color: black; background-color: white; border: 1px solid gray; padding: 5px; }")
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            conn = database.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM Expenses WHERE expense_id = ?", (exp_id,))
                conn.commit()
                self.load_expenses()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
            finally:
                conn.close()

if __name__ == "__main__":
    app = sys.modules['__main__'].QApplication(sys.argv)
    window = AccountsInterface()
    window.show()
    sys.exit(app.exec())