import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QFrame, QMessageBox, QAbstractItemView, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

import database

# --- COLORS ---
COLOR_BG = "#f4f7f6"
COLOR_NAVBAR = "#0d47a1"
COLOR_TEXT = "#212529"
COLOR_BORDER = "#dee2e6"
COLOR_DELETE = "#dc3545"

class SalesInterface(QWidget):
    edit_bill_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sales History")
        self.setStyleSheet(f"background-color: {COLOR_BG}; font-family: 'Segoe UI', Arial, sans-serif;")
        self.current_bill_id = None
        self.init_ui()
        self.load_bills()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 1. Top Bar
        top_bar = QHBoxLayout()
        lbl_title = QLabel("Sales History")
        lbl_title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {COLOR_NAVBAR};")
        top_bar.addWidget(lbl_title)
        top_bar.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search by ID, Patient or Doctor...") # Updated Placeholder
        self.search_input.setFixedWidth(300)
        self.search_input.setFixedHeight(40)
        self.search_input.textChanged.connect(self.load_bills)
        self.search_input.setStyleSheet(f"border: 1px solid {COLOR_BORDER}; border-radius: 20px; padding-left: 15px; background: white; color: {COLOR_TEXT};")
        top_bar.addWidget(self.search_input)

        btn_refresh = QPushButton("⟳")
        btn_refresh.setFixedSize(40, 40)
        btn_refresh.clicked.connect(lambda: self.load_bills())
        btn_refresh.setStyleSheet(f"border: 1px solid {COLOR_BORDER}; border-radius: 20px; background: white; color: {COLOR_NAVBAR}; font-size: 18px;")
        top_bar.addWidget(btn_refresh)
        
        main_layout.addLayout(top_bar)

        # 2. Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {COLOR_BORDER}; }}")

        # --- LEFT: LIST ---
        self.bill_table = QTableWidget()
        # Changed column count to 5 to include Doctor
        self.bill_table.setColumnCount(5)
        self.bill_table.setHorizontalHeaderLabels(["Bill ID", "Patient", "Doctor", "Date", "Amount"])
        
        # Set both Patient and Doctor columns to stretch to fill space
        self.bill_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.bill_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        self.bill_table.verticalHeader().setVisible(False)
        self.bill_table.setShowGrid(False)
        self.bill_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.bill_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.bill_table.setStyleSheet("QTableWidget { border: none; background-color: white; color: #333; } QHeaderView::section { background-color: #f4f7f6; color: #333; border: none; padding: 8px; font-weight: bold; }")
        self.bill_table.cellClicked.connect(self.on_bill_selected)
        
        left_frame = QFrame()
        left_frame.setStyleSheet("background: white; border-radius: 8px;")
        left_layout = QVBoxLayout(left_frame)
        left_layout.addWidget(self.bill_table)
        splitter.addWidget(left_frame)

        # --- RIGHT: DETAILS ---
        self.details_frame = QFrame()
        self.details_frame.setStyleSheet("background: white; border-radius: 8px;")
        self.details_frame.setVisible(False)
        
        det_layout = QVBoxLayout(self.details_frame)
        self.lbl_det_id = QLabel("Bill #")
        self.lbl_det_id.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_NAVBAR};")
        det_layout.addWidget(self.lbl_det_id)

        self.lbl_det_info = QLabel("Details...")
        self.lbl_det_info.setStyleSheet("color: #666; font-size: 14px;")
        det_layout.addWidget(self.lbl_det_info)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(3)
        self.items_table.setHorizontalHeaderLabels(["Item", "Qty", "Total"])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setStyleSheet("QTableWidget { border: none; background: white; color: #333; }")
        det_layout.addWidget(self.items_table)

        btn_del = QPushButton("Delete Bill")
        btn_del.clicked.connect(self.delete_current_bill)
        btn_del.setStyleSheet(f"background-color: {COLOR_DELETE}; color: white; border-radius: 5px; padding: 8px; font-weight: bold;")
        det_layout.addWidget(btn_del)

        splitter.addWidget(self.details_frame)
        splitter.setSizes([700, 400])
        main_layout.addWidget(splitter)

    def load_bills(self):
        query_text = self.search_input.text().strip().lower()
        self.bill_table.setRowCount(0)
        self.details_frame.setVisible(False)
        
        conn = database.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        # --- Handle new column names (patient_name/doctor_name) vs old (patient/doctor) ---
        try:
            # Try fetching with new column names
            sql = "SELECT Bill_id, patient_name, doctor_name, bill_date, total_sum FROM Bill ORDER BY Bill_id DESC"
            cursor.execute(sql)
            rows = cursor.fetchall()
        except sqlite3.OperationalError:
            # Fallback for old DB schema
            sql = "SELECT Bill_id, patient, doctor, bill_date, total_sum FROM Bill ORDER BY Bill_id DESC"
            cursor.execute(sql)
            rows = cursor.fetchall()
        
        conn.close()

        filtered_rows = []
        for r in rows:
            bid = str(r[0])
            pat = str(r[1]).lower() if r[1] else "walk-in"
            doc = str(r[2]).lower() if r[2] else "-" # Get doctor name for search
            
            # Check if query matches ID, Patient OR Doctor
            if not query_text or query_text in bid or query_text in pat or query_text in doc:
                filtered_rows.append(r)

        self.bill_table.setRowCount(len(filtered_rows))
        for i, row in enumerate(filtered_rows):
            # Bill ID
            self.bill_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            # Patient
            self.bill_table.setItem(i, 1, QTableWidgetItem(str(row[1] if row[1] else "Walk-in")))
            # Doctor (New Column)
            self.bill_table.setItem(i, 2, QTableWidgetItem(str(row[2] if row[2] else "-")))
            # Date
            self.bill_table.setItem(i, 3, QTableWidgetItem(str(row[3])))
            # Amount
            self.bill_table.setItem(i, 4, QTableWidgetItem(f"₹{row[4]:.2f}"))

    def on_bill_selected(self, row, col):
        bill_id = self.bill_table.item(row, 0).text()
        # We need to find the bill ID from the first column regardless of which cell was clicked
        self.load_bill_details(int(bill_id))

    def load_bill_details(self, bill_id):
        self.current_bill_id = bill_id
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # Try new schema first
        try:
            cursor.execute("SELECT patient_name, doctor_name, bill_date, total_sum, payment_method FROM Bill WHERE Bill_id=?", (bill_id,))
        except:
            cursor.execute("SELECT patient, doctor, bill_date, total_sum, payment_method FROM Bill WHERE Bill_id=?", (bill_id,))
            
        header = cursor.fetchone()
        
        cursor.execute("""
            SELECT m.Med_name, bi.quantity, m.Sale_Price
            FROM Bill_Item bi
            JOIN Medicine m ON bi.Med_id = m.Med_id
            WHERE bi.Bill_id = ?
        """, (bill_id,))
        items = cursor.fetchall()
        conn.close()

        if header:
            pat = header[0] if header[0] else "Walk-in"
            doc = header[1] if header[1] else "-"
            self.lbl_det_id.setText(f"Bill #{bill_id}")
            self.lbl_det_info.setText(f"Patient: {pat}\nDoctor: {doc}\nDate: {header[2]}\nMethod: {header[4]}")

        self.items_table.setRowCount(len(items))
        for i, (name, qty, price) in enumerate(items):
            total = qty * price
            self.items_table.setItem(i, 0, QTableWidgetItem(str(name)))
            self.items_table.setItem(i, 1, QTableWidgetItem(str(qty)))
            self.items_table.setItem(i, 2, QTableWidgetItem(f"₹{total:.2f}"))
        
        self.details_frame.setVisible(True)

    def delete_current_bill(self):
        if not self.current_bill_id: return
        ret = QMessageBox.question(self, "Confirm", "Delete Bill?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ret == QMessageBox.StandardButton.Yes:
            conn = database.get_connection()
            cur = conn.cursor()
            # Restore stock
            cur.execute("SELECT Med_id, quantity FROM Bill_Item WHERE Bill_id=?", (self.current_bill_id,))
            for mid, qty in cur.fetchall():
                cur.execute("UPDATE Medicine SET Quantity = Quantity + ? WHERE Med_id=?", (qty, mid))
            cur.execute("DELETE FROM Bill_Item WHERE Bill_id=?", (self.current_bill_id,))
            cur.execute("DELETE FROM Bill WHERE Bill_id=?", (self.current_bill_id,))
            conn.commit()
            conn.close()
            self.load_bills()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = SalesInterface()
    w.show()
    sys.exit(app.exec())