import sys
import sqlite3
import re  # Added for validation
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QPushButton, QFrame, QMessageBox, QGridLayout,
    QTabWidget, QGroupBox, QScrollArea, QSizePolicy, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QAction

import database

# --- COLORS ---
COLOR_BG = "#f4f7f6"
COLOR_WHITE = "#ffffff"
COLOR_NAVBAR = "#0d47a1"
COLOR_TEXT_PRIMARY = "#000000"
COLOR_BORDER = "#dee2e6"
COLOR_READONLY = "#e9ecef"
COLOR_GREEN_BTN = "#198754"
COLOR_INFO = "#0dcaf0"

class PharmacyDetailsInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pharmacy Details & Settings")
        
        # --- UPDATED STYLESHEET TO FIX POPUP COLORS ---
        self.setStyleSheet(f"""
            QWidget {{ background-color: {COLOR_BG}; font-family: 'Segoe UI', Arial, sans-serif; }}
            
            /* Fix for QMessageBox text color */
            QMessageBox {{ background-color: white; color: black; }}
            QMessageBox QLabel {{ color: black; }}
            QMessageBox QPushButton {{ 
                background-color: #f0f0f0; 
                color: black; 
                border: 1px solid #ccc; 
                border-radius: 4px; 
                padding: 6px 15px;
            }}
            QMessageBox QPushButton:hover {{ background-color: #e0e0e0; }}
        """)
        
        # Ensure DB has new email, printer, and fssai columns
        self.check_schema()
        
        self.is_editing = False 
        self.init_ui()
        self.set_inputs_readonly(True)
        self.load_data()

    def check_schema(self):
        """Automatically adds missing columns if they don't exist."""
        conn = database.get_connection()
        if not conn: return
        cursor = conn.cursor()
        try:
            cursor.execute("PRAGMA table_info(Pharmacy)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "smtp_email" not in columns:
                cursor.execute("ALTER TABLE Pharmacy ADD COLUMN smtp_email TEXT")
            if "smtp_password" not in columns:
                cursor.execute("ALTER TABLE Pharmacy ADD COLUMN smtp_password TEXT")
            if "printer_type" not in columns:
                cursor.execute("ALTER TABLE Pharmacy ADD COLUMN printer_type TEXT DEFAULT 'Thermal Printer (80mm/58mm)'")
            # --- Added FSSAI Schema Check ---
            if "fssai_no" not in columns:
                cursor.execute("ALTER TABLE Pharmacy ADD COLUMN fssai_no TEXT")
            
            conn.commit()
        except Exception as e:
            print(f"Schema Check Error: {e}")
        finally:
            conn.close()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        lbl_main_title = QLabel("Pharmacy Configuration")
        lbl_main_title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLOR_NAVBAR}; margin-bottom: 10px;")
        main_layout.addWidget(lbl_main_title)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {COLOR_BORDER}; background: white; border-radius: 5px; }}
            QTabBar::tab {{ background: #e0e0e0; color: black; padding: 10px 20px; }}
            QTabBar::tab:selected {{ background: white; color: {COLOR_NAVBAR}; border-bottom: 2px solid {COLOR_NAVBAR}; font-weight: bold; }}
        """)

        self.tab_profile = QWidget()
        self.tab_email = QWidget()

        self.tabs.addTab(self.tab_profile, "General Profile")
        self.tabs.addTab(self.tab_email, "Email Integration")

        # --- TAB 1: GENERAL PROFILE ---
        self.init_profile_tab()
        
        # --- TAB 2: EMAIL INTEGRATION ---
        self.init_email_tab()

        main_layout.addWidget(self.tabs)

        # Action Buttons (Bottom)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_action = QPushButton("EDIT SETTINGS")
        self.btn_action.setFixedWidth(200)
        self.btn_action.setFixedHeight(45)
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.clicked.connect(self.toggle_edit_mode)
        self.btn_action.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_NAVBAR}; color: white; font-size: 14px; font-weight: bold; border-radius: 5px;
            }}
            QPushButton:hover {{ background-color: #0a3675; }}
        """)
        btn_layout.addWidget(self.btn_action)
        
        main_layout.addLayout(btn_layout)

    def init_profile_tab(self):
        layout = QVBoxLayout(self.tab_profile)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        form_grid = QGridLayout()
        form_grid.setSpacing(15)

        self.inp_name = self.create_input("Pharmacy Name")
        self.inp_phone = self.create_input("Phone Number")
        self.inp_email = self.create_input("Public Email Address")
        self.inp_gstin = self.create_input("15-digit GSTIN / Reg No.")
        self.inp_license = self.create_input("e.g., MH-MZ4-123456") 
        self.inp_fssai = self.create_input("14-digit FSSAI Number") # New FSSAI input
        
        self.cmb_printer = QComboBox()
        self.cmb_printer.addItems(["Thermal Printer (80mm/58mm)", "Laser/Inkjet Printer (A4)"])
        self.cmb_printer.setFixedHeight(40)
        self.cmb_printer.setStyleSheet(self.get_input_style())
        
        self.inp_address = QTextEdit()
        self.inp_address.setPlaceholderText("Full Address")
        self.inp_address.setFixedHeight(80)
        self.inp_address.setStyleSheet(self.get_input_style())

        self.add_form_row(form_grid, 0, "Pharmacy Name:", self.inp_name)
        self.add_form_row(form_grid, 1, "Phone:", self.inp_phone)
        self.add_form_row(form_grid, 2, "Public Email:", self.inp_email)
        self.add_form_row(form_grid, 3, "GSTIN:", self.inp_gstin)
        self.add_form_row(form_grid, 4, "Drug License No. (Form 20/21):", self.inp_license) # Updated label
        self.add_form_row(form_grid, 5, "FSSAI License No.:", self.inp_fssai) # Added FSSAI row
        self.add_form_row(form_grid, 6, "Default Printer:", self.cmb_printer) 
        
        lbl_addr = QLabel("Address:")
        lbl_addr.setStyleSheet(f"font-weight: bold; font-size: 14px; border: none; color: {COLOR_TEXT_PRIMARY};")
        form_grid.addWidget(lbl_addr, 7, 0, alignment=Qt.AlignmentFlag.AlignTop) # Shifted to row 7
        form_grid.addWidget(self.inp_address, 7, 1)

        layout.addLayout(form_grid)
        layout.addStretch()

    def init_email_tab(self):
        layout = QVBoxLayout(self.tab_email)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Info Box
        info_box = QFrame()
        info_box.setStyleSheet(f"background-color: #e3f2fd; border-left: 5px solid {COLOR_NAVBAR}; padding: 10px; border-radius: 4px;")
        info_layout = QVBoxLayout(info_box)
        lbl_info = QLabel("Configure the email account used to send Purchase Orders to suppliers.")
        lbl_info.setStyleSheet("color: #0d47a1; font-weight: bold;")
        info_layout.addWidget(lbl_info)
        layout.addWidget(info_box)

        # Form
        form_layout = QGridLayout()
        form_layout.setSpacing(15)

        self.inp_smtp_email = self.create_input("your_email@gmail.com")
        
        self.inp_smtp_pass = QLineEdit()
        self.inp_smtp_pass.setPlaceholderText("16-character App Password")
        self.inp_smtp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_smtp_pass.setFixedHeight(40)
        self.inp_smtp_pass.setStyleSheet(self.get_input_style())

        # Toggle Password Visibility
        self.btn_show_pass = QPushButton("👁")
        self.btn_show_pass.setFixedSize(40, 40)
        self.btn_show_pass.setStyleSheet("border: 1px solid #ccc; background: white; border-radius: 4px;")
        self.btn_show_pass.pressed.connect(lambda: self.inp_smtp_pass.setEchoMode(QLineEdit.EchoMode.Normal))
        self.btn_show_pass.released.connect(lambda: self.inp_smtp_pass.setEchoMode(QLineEdit.EchoMode.Password))

        pass_layout = QHBoxLayout()
        pass_layout.setContentsMargins(0,0,0,0)
        pass_layout.setSpacing(5)
        pass_layout.addWidget(self.inp_smtp_pass)
        pass_layout.addWidget(self.btn_show_pass)

        lbl_e = QLabel("Sender Email:")
        lbl_e.setStyleSheet(f"font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        form_layout.addWidget(lbl_e, 0, 0)
        form_layout.addWidget(self.inp_smtp_email, 0, 1)

        lbl_p = QLabel("App Password:")
        lbl_p.setStyleSheet(f"font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        form_layout.addWidget(lbl_p, 1, 0)
        form_layout.addLayout(pass_layout, 1, 1)

        layout.addLayout(form_layout)

        # --- INSTRUCTIONS ---
        grp_help = QGroupBox("How to get a Google App Password?")
        grp_help.setStyleSheet(f"QGroupBox {{ font-weight: bold; border: 1px solid #ccc; margin-top: 20px; padding-top: 15px; }} QGroupBox::title {{ color: {COLOR_NAVBAR}; }}")
        help_layout = QVBoxLayout(grp_help)
        
        steps = """
        <ol style='font-weight: normal; font-size: 13px; line-height: 1.6;'>
            <li>Go to your <b>Google Account</b> settings.</li>
            <li>Navigate to the <b>Security</b> tab.</li>
            <li>Enable <b>2-Step Verification</b> if it is not already on.</li>
            <li>In the search bar at the top, type <b>"App passwords"</b> and select it.</li>
            <li>Create a new app password (name it 'Pharmacy App').</li>
            <li>Google will generate a <b>16-character code</b>. Copy and paste it above.</li>
        </ol>
        <p style='color: #666; font-style: italic; font-size: 12px;'>Note: Do NOT use your regular Gmail login password.</p>
        """
        lbl_steps = QLabel(steps)
        lbl_steps.setTextFormat(Qt.TextFormat.RichText)
        lbl_steps.setWordWrap(True)
        lbl_steps.setStyleSheet("color: black;")
        
        help_layout.addWidget(lbl_steps)
        layout.addWidget(grp_help)
        
        layout.addStretch()

    def create_input(self, placeholder):
        le = QLineEdit()
        le.setPlaceholderText(placeholder)
        le.setFixedHeight(40)
        le.setStyleSheet(self.get_input_style())
        return le

    def get_input_style(self):
        return f"""
            QLineEdit, QTextEdit, QComboBox {{
                color: {COLOR_TEXT_PRIMARY}; border: 1px solid {COLOR_BORDER}; border-radius: 5px;
                padding: 8px; font-size: 14px; background-color: {COLOR_WHITE};
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{ border: 1px solid {COLOR_NAVBAR}; }}
            QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled {{ background-color: {COLOR_READONLY}; color: #555; }}
            
            /* Explicitly force the dropdown list items to be black on white */
            QComboBox QAbstractItemView {{
                color: #000000;
                background-color: {COLOR_WHITE};
                selection-background-color: #e3f2fd;
                selection-color: #000000;
            }}
        """

    def add_form_row(self, layout, row, label_text, widget):
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"font-weight: bold; font-size: 14px; border: none; color: {COLOR_TEXT_PRIMARY};")
        layout.addWidget(lbl, row, 0)
        layout.addWidget(widget, row, 1)

    def toggle_edit_mode(self):
        if not self.is_editing:
            self.is_editing = True
            self.set_inputs_readonly(False)
            self.btn_action.setText("SAVE SETTINGS")
            self.btn_action.setStyleSheet(f"background-color: {COLOR_GREEN_BTN}; color: white; font-size: 14px; font-weight: bold; border-radius: 5px;")
        else:
            if self.save_data():
                self.is_editing = False
                self.set_inputs_readonly(True)
                self.btn_action.setText("EDIT SETTINGS")
                self.btn_action.setStyleSheet(f"background-color: {COLOR_NAVBAR}; color: white; font-size: 14px; font-weight: bold; border-radius: 5px;")

    def set_inputs_readonly(self, readonly: bool):
        # Profile
        self.inp_name.setReadOnly(readonly); self.inp_name.setEnabled(not readonly)
        self.inp_phone.setReadOnly(readonly); self.inp_phone.setEnabled(not readonly)
        self.inp_email.setReadOnly(readonly); self.inp_email.setEnabled(not readonly)
        self.inp_gstin.setReadOnly(readonly); self.inp_gstin.setEnabled(not readonly)
        self.inp_license.setReadOnly(readonly); self.inp_license.setEnabled(not readonly)
        self.inp_fssai.setReadOnly(readonly); self.inp_fssai.setEnabled(not readonly) # New
        self.cmb_printer.setEnabled(not readonly)
        self.inp_address.setReadOnly(readonly); self.inp_address.setEnabled(not readonly)
        
        # Email Settings
        self.inp_smtp_email.setReadOnly(readonly); self.inp_smtp_email.setEnabled(not readonly)
        self.inp_smtp_pass.setReadOnly(readonly); self.inp_smtp_pass.setEnabled(not readonly)

    def load_data(self):
        conn = database.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        # Select including new columns
        try:
            # Added fssai_no to select statement
            cursor.execute("SELECT p_name, phone, email, GSTIN, license_no, location, smtp_email, smtp_password, printer_type, fssai_no FROM Pharmacy LIMIT 1")
            row = cursor.fetchone()
        except Exception:
            # Fallback if columns missing
            row = None
        
        conn.close()

        if row:
            self.inp_name.setText(row[0] or "")
            self.inp_phone.setText(row[1] or "")
            self.inp_email.setText(row[2] or "")
            self.inp_gstin.setText(row[3] or "")
            self.inp_license.setText(row[4] or "")
            self.inp_address.setPlainText(row[5] or "")
            
            # Email settings
            self.inp_smtp_email.setText(row[6] or "")
            self.inp_smtp_pass.setText(row[7] or "")
            
            # Printer Settings
            printer_val = row[8] if len(row) > 8 and row[8] else "Thermal Printer (80mm/58mm)"
            idx = self.cmb_printer.findText(printer_val)
            if idx >= 0:
                self.cmb_printer.setCurrentIndex(idx)
                
            # FSSAI Setting
            self.inp_fssai.setText(row[9] if len(row) > 9 and row[9] else "")
        else:
            if not self.is_editing: self.toggle_edit_mode()

    def save_data(self):
        name = self.inp_name.text().strip()
        gstin = self.inp_gstin.text().strip()
        license_no = self.inp_license.text().strip()
        fssai_no = self.inp_fssai.text().strip()
        smtp_email = self.inp_smtp_email.text().strip()
        smtp_pass = self.inp_smtp_pass.text().strip()
        printer_type = self.cmb_printer.currentText()

        # 1. Validate Pharmacy Name
        if not name:
            QMessageBox.warning(self, "Validation Error", "Pharmacy Name is required.")
            return False

        # 2. Validate GSTIN (Must be exactly 15 alphanumeric characters)
        if gstin and (len(gstin) != 15 or not gstin.isalnum()):
            QMessageBox.warning(self, "Validation Error", "GSTIN number must be exactly 15 alphanumeric characters.")
            self.inp_gstin.setFocus()
            return False

        # 3. Validate Drug License (Alphanumeric with hyphens/slashes, min 5 chars)
        if license_no and not re.match(r'^[A-Za-z0-9\-\/]{5,30}$', license_no):
            QMessageBox.warning(self, "Validation Error", "Please enter a valid Drug License Number.\n(Letters, numbers, hyphens, and slashes only).")
            self.inp_license.setFocus()
            return False

        # 4. Validate FSSAI (Must be exactly 14 digits)
        if fssai_no and (len(fssai_no) != 14 or not fssai_no.isdigit()):
            QMessageBox.warning(self, "Validation Error", "FSSAI License Number must be exactly 14 digits.")
            self.inp_fssai.setFocus()
            return False

        conn = database.get_connection()
        if not conn: return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM Pharmacy")
            count = cursor.fetchone()[0]

            # Added fssai_no to data tuple
            data = (
                name, self.inp_phone.text().strip(), self.inp_email.text().strip(),
                gstin, license_no, self.inp_address.toPlainText().strip(), 
                smtp_email, smtp_pass, printer_type, fssai_no
            )

            if count == 0:
                # Insert query updated to include fssai_no
                cursor.execute("""
                    INSERT INTO Pharmacy (p_name, phone, email, GSTIN, license_no, location, smtp_email, smtp_password, printer_type, fssai_no)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, data)
            else:
                # Update query updated to include fssai_no
                cursor.execute("""
                    UPDATE Pharmacy 
                    SET p_name=?, phone=?, email=?, GSTIN=?, license_no=?, location=?, smtp_email=?, smtp_password=?, printer_type=?, fssai_no=?
                """, data)

            conn.commit()
            QMessageBox.information(self, "Success", "Settings saved successfully!")
            return True
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", str(e))
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PharmacyDetailsInterface()
    window.resize(900, 700)
    window.show()
    sys.exit(app.exec())