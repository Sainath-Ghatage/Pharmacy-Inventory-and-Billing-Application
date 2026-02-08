import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QPushButton, QFrame, QMessageBox, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import database

# --- COLORS ---
COLOR_BG = "#f4f7f6"
COLOR_WHITE = "#ffffff"
COLOR_NAVBAR = "#0d47a1"
COLOR_TEXT_PRIMARY = "#212529"   # Dark Grey
COLOR_BORDER = "#dee2e6"
COLOR_READONLY = "#e9ecef"       # Light grey for disabled state
COLOR_GREEN_BTN = "#198754"      # Success Green

class PharmacyDetailsInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pharmacy Details")
        self.setStyleSheet(f"background-color: {COLOR_BG}; font-family: 'Segoe UI', Arial, sans-serif;")
        
        # State variable to track mode
        self.is_editing = False 
        
        self.init_ui()
        
        # Default to Read-Only initially
        self.set_inputs_readonly(True)
        
        # Load data (If empty, this will auto-trigger Edit Mode)
        self.load_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- CARD CONTAINER ---
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_WHITE};
                border-radius: 10px;
                border: 1px solid {COLOR_BORDER};
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)

        # 1. Header
        lbl_title = QLabel("Pharmacy Profile")
        lbl_title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLOR_NAVBAR}; border: none;")
        card_layout.addWidget(lbl_title)
        
        lbl_subtitle = QLabel("Manage your pharmacy's billing information here.")
        lbl_subtitle.setStyleSheet(f"font-size: 14px; color: #6c757d; border: none; margin-bottom: 10px;")
        card_layout.addWidget(lbl_subtitle)

        # 2. Form Grid
        form_grid = QGridLayout()
        form_grid.setSpacing(15)
        form_grid.setColumnStretch(1, 1)

        # -- Inputs --
        self.inp_name = self.create_input("Pharmacy Name")
        self.inp_phone = self.create_input("Phone Number")
        self.inp_email = self.create_input("Email Address")
        self.inp_gstin = self.create_input("GSTIN / Reg No.")
        
        self.inp_address = QTextEdit()
        self.inp_address.setPlaceholderText("Full Address")
        self.inp_address.setFixedHeight(80)
        self.inp_address.setStyleSheet(self.get_input_style())

        # -- Add to Grid --
        self.add_form_row(form_grid, 0, "Pharmacy Name:", self.inp_name)
        self.add_form_row(form_grid, 1, "Phone:", self.inp_phone)
        self.add_form_row(form_grid, 2, "Email:", self.inp_email)
        self.add_form_row(form_grid, 3, "GSTIN:", self.inp_gstin)
        
        # Address Label
        lbl_addr = QLabel("Address:")
        lbl_addr.setStyleSheet(f"font-weight: bold; font-size: 14px; border: none; color: {COLOR_TEXT_PRIMARY};")
        form_grid.addWidget(lbl_addr, 4, 0, alignment=Qt.AlignmentFlag.AlignTop)
        form_grid.addWidget(self.inp_address, 4, 1)

        card_layout.addLayout(form_grid)
        card_layout.addSpacing(20)

        # 3. Action Button (Edit/Save)
        self.btn_action = QPushButton("EDIT DETAILS")
        self.btn_action.setFixedWidth(200)
        self.btn_action.setFixedHeight(45)
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.clicked.connect(self.toggle_edit_mode)
        self.btn_action.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_NAVBAR};
                color: white;
                font-size: 15px;
                font-weight: bold;
                border-radius: 5px;
                border: none;
            }}
            QPushButton:hover {{ background-color: #0a3675; }}
        """)
        
        btn_container = QHBoxLayout()
        btn_container.addStretch()
        btn_container.addWidget(self.btn_action)
        card_layout.addLayout(btn_container)

        main_layout.addWidget(card)

    def create_input(self, placeholder):
        le = QLineEdit()
        le.setPlaceholderText(placeholder)
        le.setFixedHeight(40)
        le.setStyleSheet(self.get_input_style())
        return le

    def get_input_style(self):
        return f"""
            QLineEdit, QTextEdit {{
                color: {COLOR_TEXT_PRIMARY}; 
                border: 1px solid {COLOR_BORDER};
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
                background-color: {COLOR_WHITE};
                selection-background-color: {COLOR_NAVBAR};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 1px solid {COLOR_NAVBAR};
            }}
            QLineEdit:disabled, QTextEdit:disabled {{
                background-color: {COLOR_READONLY};
                color: #495057; 
            }}
        """

    def add_form_row(self, layout, row, label_text, widget):
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"font-weight: bold; font-size: 14px; border: none; color: {COLOR_TEXT_PRIMARY};")
        layout.addWidget(lbl, row, 0)
        layout.addWidget(widget, row, 1)

    # --- LOGIC: VIEW VS EDIT MODE ---
    def toggle_edit_mode(self):
        if not self.is_editing:
            # Switch to EDIT mode
            self.is_editing = True
            self.set_inputs_readonly(False)
            self.btn_action.setText("SAVE DETAILS")
            self.btn_action.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_GREEN_BTN}; 
                    color: white; font-size: 15px; font-weight: bold; border-radius: 5px;
                }}
                QPushButton:hover {{ background-color: #146c43; }}
            """)
        else:
            # User clicked SAVE
            success = self.save_data()
            if success:
                # Switch back to VIEW mode
                self.is_editing = False
                self.set_inputs_readonly(True)
                self.btn_action.setText("EDIT DETAILS")
                self.btn_action.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLOR_NAVBAR}; 
                        color: white; font-size: 15px; font-weight: bold; border-radius: 5px;
                    }}
                    QPushButton:hover {{ background-color: #0a3675; }}
                """)

    def set_inputs_readonly(self, readonly: bool):
        self.inp_name.setReadOnly(readonly)
        self.inp_phone.setReadOnly(readonly)
        self.inp_email.setReadOnly(readonly)
        self.inp_gstin.setReadOnly(readonly)
        self.inp_address.setReadOnly(readonly)
        
        self.inp_name.setEnabled(not readonly)
        self.inp_phone.setEnabled(not readonly)
        self.inp_email.setEnabled(not readonly)
        self.inp_gstin.setEnabled(not readonly)
        self.inp_address.setEnabled(not readonly)

    # --- HELPER: CUSTOM MESSAGE BOX (FIXES WHITE TEXT ISSUE) ---
    def show_message(self, title, text, icon_type):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(icon_type)
        # Force styles: White background, Black text
        msg.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: black; font-size: 13px; }
            QPushButton { 
                color: black; 
                background-color: #e0e0e0; 
                border: 1px solid #999; 
                border-radius: 3px;
                padding: 5px 15px;
                min-width: 60px;
            }
            QPushButton:hover { background-color: #d0d0d0; }
        """)
        msg.exec()

    # --- DATABASE LOGIC ---
    def load_data(self):
        conn = database.get_connection()
        if not conn: return
        
        cursor = conn.cursor()
        cursor.execute("SELECT p_name, phone, email, GSTIN, location FROM Pharmacy LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        if row:
            # Data exists: Populate and stay in View Mode
            self.inp_name.setText(row[0] if row[0] else "")
            self.inp_phone.setText(row[1] if row[1] else "")
            self.inp_email.setText(row[2] if row[2] else "")
            self.inp_gstin.setText(row[3] if row[3] else "")
            self.inp_address.setPlainText(row[4] if row[4] else "")
        else:
            # No data: Switch to Edit Mode automatically
            if not self.is_editing:
                self.toggle_edit_mode()

    def save_data(self):
        name = self.inp_name.text().strip()
        phone = self.inp_phone.text().strip()
        email = self.inp_email.text().strip()
        gstin = self.inp_gstin.text().strip()
        addr = self.inp_address.toPlainText().strip()

        if not name:
            self.show_message("Validation", "Pharmacy Name is required.", QMessageBox.Icon.Warning)
            return False

        conn = database.get_connection()
        if not conn: return False
        
        try:
            cursor = conn.cursor()
            
            # Check if a row exists
            cursor.execute("SELECT count(*) FROM Pharmacy")
            count = cursor.fetchone()[0]

            if count == 0:
                # Insert
                cursor.execute("""
                    INSERT INTO Pharmacy (p_name, phone, email, GSTIN, location)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, phone, email, gstin, addr))
            else:
                # Update
                cursor.execute("""
                    UPDATE Pharmacy 
                    SET p_name=?, phone=?, email=?, GSTIN=?, location=?
                """, (name, phone, email, gstin, addr))

            conn.commit()
            self.show_message("Success", "Pharmacy details saved successfully!", QMessageBox.Icon.Information)
            return True
            
        except sqlite3.Error as e:
            self.show_message("Database Error", str(e), QMessageBox.Icon.Critical)
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PharmacyDetailsInterface()
    window.show()
    sys.exit(app.exec())