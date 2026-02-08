import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QFrame, QMessageBox, QAbstractItemView, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QFont

import database

# --- COLORS ---
COLOR_BG = "#f4f7f6"
COLOR_WHITE = "#ffffff"
COLOR_NAVBAR = "#0d47a1"
COLOR_TEXT = "#212529"
COLOR_BORDER = "#dee2e6"
COLOR_DELETE = "#dc3545"
COLOR_EDIT = "#ffc107"

class SalesInterface(QWidget):
    # Signal to tell Main Window to switch to Billing tab with specific ID
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

        # 1. Top Bar (Title + Search)
        top_bar = QHBoxLayout()
        
        lbl_title = QLabel("Sales History")
        lbl_title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {COLOR_NAVBAR};")
        top_bar.addWidget(lbl_title)
        
        top_bar.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search by Bill ID or Patient...")
        self.search_input.setFixedWidth(300)
        self.search_input.setFixedHeight(40)
        self.search_input.textChanged.connect(self.load_bills)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 20px;
                padding-left: 15px;
                background: white;
                color: {COLOR_TEXT};
            }}
            QLineEdit:focus {{ border: 1px solid {COLOR_NAVBAR}; }}
        """)
        top_bar.addWidget(self.search_input)

        btn_refresh = QPushButton("⟳")
        btn_refresh.setFixedSize(40, 40)
        btn_refresh.clicked.connect(lambda: self.load_bills())
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 20px;
                background: white;
                color: {COLOR_NAVBAR};
                font-size: 18px;
            }}
            QPushButton:hover {{ background-color: #e9ecef; }}
        """)
        top_bar.addWidget(btn_refresh)
        
        main_layout.addLayout(top_bar)

        # 2. Splitter (Left: List, Right: Details)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {COLOR_BORDER}; }}")

        # --- LEFT: BILL LIST ---
        self.bill_table = QTableWidget()
        self.bill_table.setColumnCount(4)
        self.bill_table.setHorizontalHeaderLabels(["Bill ID", "Patient", "Date", "Amount"])
        
        # --- DYNAMIC COLUMN SIZING ---
        header = self.bill_table.horizontalHeader()
        
        # 0: Bill ID - Fit to content (keep it small)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        # 1: Patient - STRETCH to fill available space
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # 2: Date - Fit to content
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        # 3: Amount - Fit to content
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.bill_table.verticalHeader().setVisible(False)
        self.bill_table.setShowGrid(False)
        self.bill_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.bill_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.bill_table.setStyleSheet(self.get_table_style())
        self.bill_table.cellClicked.connect(self.on_bill_selected)
        
        left_frame = QFrame()
        left_frame.setStyleSheet("background: white; border-radius: 8px;")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.bill_table)
        
        splitter.addWidget(left_frame)

        # --- RIGHT: DETAILS PANEL ---
        self.details_frame = QFrame()
        self.details_frame.setStyleSheet("background: white; border-radius: 8px;")
        self.details_frame.setVisible(False) # Hidden initially
        
        det_layout = QVBoxLayout(self.details_frame)
        det_layout.setContentsMargins(20, 20, 20, 20)
        det_layout.setSpacing(10)

        # Header Details
        self.lbl_det_id = QLabel("Bill #")
        self.lbl_det_id.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_NAVBAR};")
        det_layout.addWidget(self.lbl_det_id)

        self.lbl_det_info = QLabel("Patient: -\nDate: -")
        self.lbl_det_info.setStyleSheet("color: #666; font-size: 14px;")
        det_layout.addWidget(self.lbl_det_info)

        det_layout.addWidget(self.create_h_line())

        # Items Table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(3)
        self.items_table.setHorizontalHeaderLabels(["Item", "Qty", "Total"])
        
        # --- DYNAMIC ITEMS TABLE ---
        i_header = self.items_table.horizontalHeader()
        # Item Name stretches, others fit content
        i_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        i_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        i_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setShowGrid(False)
        self.items_table.setStyleSheet(self.get_table_style())
        self.items_table.setFixedHeight(250) # Fixed height for items list
        det_layout.addWidget(self.items_table)

        det_layout.addStretch()
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_delete = QPushButton("Delete Bill")
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.clicked.connect(self.delete_current_bill)
        self.btn_delete.setStyleSheet(f"""
            QPushButton {{ background-color: {COLOR_DELETE}; color: white; border-radius: 5px; padding: 8px; font-weight: bold; }}
            QPushButton:hover {{ background-color: #b02a37; }}
        """)
        
        self.btn_edit = QPushButton("Edit Bill")
        self.btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_edit.clicked.connect(self.edit_current_bill)
        self.btn_edit.setStyleSheet(f"""
            QPushButton {{ background-color: {COLOR_NAVBAR}; color: white; border-radius: 5px; padding: 8px; font-weight: bold; }}
            QPushButton:hover {{ background-color: #0a3675; }}
        """)

        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_edit)
        det_layout.addLayout(btn_layout)

        splitter.addWidget(self.details_frame)
        
        # Set splitter proportions (60% list, 40% details)
        splitter.setSizes([700, 400])
        
        main_layout.addWidget(splitter)

    # --- DATA LOADING ---
    def load_bills(self):
        query = self.search_input.text().strip().lower()
        self.bill_table.setRowCount(0)
        self.details_frame.setVisible(False)
        
        conn = database.get_connection()
        if not conn: return
        
        cursor = conn.cursor()
        
        sql = "SELECT Bill_id, patient, bill_date, total_sum FROM Bill ORDER BY Bill_id DESC"
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()

        filtered_rows = []
        for r in rows:
            bid = str(r[0])
            pat = str(r[1]).lower() if r[1] else ""
            if not query or query in bid or query in pat:
                filtered_rows.append(r)

        self.bill_table.setRowCount(len(filtered_rows))
        for i, row in enumerate(filtered_rows):
            # Bill ID
            self.bill_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            
            # --- PATIENT NAME LOGIC ---
            raw_name = str(row[1]) if row[1] and str(row[1]).strip() != "" else "Unknown"
            pat_item = QTableWidgetItem(raw_name)
            # Make BOLD
            pat_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.bill_table.setItem(i, 1, pat_item)
            
            # Date (Clean up format)
            self.bill_table.setItem(i, 2, QTableWidgetItem(str(row[2])))
            
            # Amount
            amt_item = QTableWidgetItem(f"₹{row[3]:.2f}")
            amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.bill_table.setItem(i, 3, amt_item)

    def on_bill_selected(self, row, col):
        bill_id = self.bill_table.item(row, 0).text()
        self.load_bill_details(int(bill_id))

    def load_bill_details(self, bill_id):
        self.current_bill_id = bill_id
        
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # 1. Get Header Info
        cursor.execute("SELECT patient, doctor, bill_date, total_sum, payment_method FROM Bill WHERE Bill_id=?", (bill_id,))
        header = cursor.fetchone()
        
        if not header:
            conn.close()
            return

        # 2. Get Items (Join with Medicine to get Name)
        cursor.execute("""
            SELECT m.Med_name, bi.quantity, m.Sale_Price
            FROM Bill_Item bi
            JOIN Medicine m ON bi.Med_id = m.Med_id
            WHERE bi.Bill_id = ?
        """, (bill_id,))
        items = cursor.fetchall()
        conn.close()

        # Update UI
        pat_name = header[0] if header[0] else "Unknown"
        self.lbl_det_id.setText(f"Bill #{bill_id}")
        self.lbl_det_info.setText(f"Patient: {pat_name}\nDoctor: {header[1]}\nDate: {header[2]}\nPayment: {header[4]}")
        
        self.items_table.setRowCount(0)
        self.items_table.setRowCount(len(items))
        
        for i, (name, qty, price) in enumerate(items):
            total = qty * price
            self.items_table.setItem(i, 0, QTableWidgetItem(str(name)))
            self.items_table.setItem(i, 1, QTableWidgetItem(str(qty)))
            
            t_item = QTableWidgetItem(f"₹{total:.2f}")
            t_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.items_table.setItem(i, 2, t_item)

        self.details_frame.setVisible(True)

    # --- ACTIONS ---
    def delete_current_bill(self):
        if not self.current_bill_id: return
        
        qm = QMessageBox
        ret = qm.question(self, "Confirm Delete", 
                          f"Are you sure you want to delete Bill #{self.current_bill_id}?\nStock will be restored.",
                          qm.StandardButton.Yes | qm.StandardButton.No)
        
        if ret == qm.StandardButton.Yes:
            conn = database.get_connection()
            try:
                cur = conn.cursor()
                
                # 1. Restore Stock
                cur.execute("SELECT Med_id, quantity FROM Bill_Item WHERE Bill_id=?", (self.current_bill_id,))
                items = cur.fetchall()
                for mid, qty in items:
                    cur.execute("UPDATE Medicine SET Quantity = Quantity + ? WHERE Med_id=?", (qty, mid))
                
                # 2. Delete Items
                cur.execute("DELETE FROM Bill_Item WHERE Bill_id=?", (self.current_bill_id,))
                
                # 3. Delete Bill
                cur.execute("DELETE FROM Bill WHERE Bill_id=?", (self.current_bill_id,))
                
                conn.commit()
                self.load_bills() # Refresh list
                qm.information(self, "Success", "Bill deleted and stock restored.")
                
            except Exception as e:
                qm.critical(self, "Error", str(e))
            finally:
                conn.close()

    def edit_current_bill(self):
        if self.current_bill_id:
            # Emit signal so Main Window can handle page switching
            self.edit_bill_signal.emit(self.current_bill_id)

    # --- STYLES ---
    def get_table_style(self):
        return f"""
            QTableWidget {{ border: none; background-color: white; }}
            QHeaderView::section {{
                background-color: {COLOR_BG};
                color: {COLOR_TEXT};
                border: none;
                padding: 8px;
                font-weight: bold;
            }}
            QTableWidget::item {{ 
                padding: 5px; 
                border-bottom: 1px solid {COLOR_BG}; 
                color: {COLOR_TEXT};
            }}
            QTableWidget::item:selected {{
                background-color: #e3f2fd;
                color: black;
            }}
        """

    def create_h_line(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet(f"border: none; background-color: {COLOR_BORDER}; max-height: 1px;")
        return line

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SalesInterface()
    window.show()
    sys.exit(app.exec())