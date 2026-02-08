import sys
import sqlite3
import datetime
from datetime import timedelta
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QStackedWidget, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont

import database
from billing import BillingInterface
from pharmacy_details import PharmacyDetailsInterface
from sales import SalesInterface
from reports import ReportsInterface
from stock_management import StockInterface
from orders import OrdersInterface


# ---------- COLORS ----------
COLOR_NAVBAR = "#0d47a1"   # Deep Blue
COLOR_SIDEBAR = "#0d47a1"  # MATCHED Navbar color
COLOR_BG = "#f4f7f6"       # Light Gray Background
COLOR_ACTIVE = "#1976d2"   # Lighter Blue for active state
COLOR_TEXT_NAV = "#ffffff" # White text for sidebar
COLOR_TEXT_BODY = "#212529"


# ==========================================
#  1. NOTIFICATION SYSTEM (Fixed Blue Background)
# ==========================================

# ==========================================
#  1. NOTIFICATION SYSTEM (Fixed Crash & Colors)
# ==========================================
class ToastNotification(QWidget):
    def __init__(self, parent, title, message, type="warning"):
        super().__init__(parent)
        
        # Window Flags (Frameless & Transparent parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.setFixedSize(350, 80)

        # --- MAIN LAYOUT (Transparent) ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # --- CONTAINER FRAME (The Visible Blue Box) ---
        self.container = QFrame()
        self.container.setObjectName("ToastContainer")
        self.container.setStyleSheet("""
            #ToastContainer {
                background-color: #0d47a1;
                border-radius: 10px;
                border: 1px solid #082e66;
            }
        """)
        self.main_layout.addWidget(self.container)

        # --- INNER LAYOUT (Inside the Blue Box) ---
        self.layout = QHBoxLayout(self.container)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(15)

        # Determine Icon Style
        if type == "success":
            icon_color, icon_symbol = "#2ecc71", "✔"
        elif type == "error":
            icon_color, icon_symbol = "#e74c3c", "✖"
        else: # Warning
            icon_color, icon_symbol = "#f1c40f", "!"

        # Icon (Colored Circle)
        self.lbl_icon = QLabel(icon_symbol)
        self.lbl_icon.setFixedSize(30, 30)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_icon.setStyleSheet(f"""
            QLabel {{ 
                background-color: {icon_color}; 
                color: black; 
                border-radius: 15px; 
                font-weight: bold; 
                font-size: 16px; 
                border: none;
            }}
        """)
        self.layout.addWidget(self.lbl_icon)

        # Text Section
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        # Title (White)
        self.lbl_title = QLabel(title.upper())
        self.lbl_title.setStyleSheet("color: white; font-weight: bold; font-size: 12px; border: none; background: transparent;")
        
        # Message (White)
        self.lbl_msg = QLabel(message)
        self.lbl_msg.setWordWrap(True)
        self.lbl_msg.setStyleSheet("color: white; font-size: 11px; border: none; background: transparent;")
        
        text_layout.addWidget(self.lbl_title)
        text_layout.addWidget(self.lbl_msg)
        self.layout.addLayout(text_layout)

        # Close Btn
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(20, 20)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.close_notification)
        self.btn_close.setStyleSheet("""
            QPushButton { color: white; background: transparent; border: none; font-weight: bold; }
            QPushButton:hover { color: #cccccc; }
        """)
        self.layout.addWidget(self.btn_close, alignment=Qt.AlignmentFlag.AlignTop)

        # Auto Close Timer (5 Seconds)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close_notification)
        self.timer.start(5000) 

    def show_animation(self):
        # Animate the Container, not the transparent window
        self.opacity_effect = QGraphicsOpacityEffect(self.container)
        self.container.setGraphicsEffect(self.opacity_effect)
        
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(500)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.start()
        self.show()

    def close_notification(self):
        self.timer.stop()
        self.anim_close = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_close.setDuration(500)
        self.anim_close.setStartValue(1)
        self.anim_close.setEndValue(0)
        self.anim_close.finished.connect(self.close)
        self.anim_close.start()

class NotificationManager:
    def __init__(self, parent):
        self.parent = parent
        self.active_notifications = []
    
    def show_toast(self, title, message, type="warning"):
        try:
            # If parent is hidden or deleted, stop
            if not self.parent or not self.parent.isVisible(): return
        except RuntimeError:
            return

        toast = ToastNotification(self.parent, title, message, type)
        
        # Clean up toast reference when it is destroyed
        toast.destroyed.connect(lambda: self.remove_toast(toast))
        
        self.active_notifications.append(toast)
        self.reposition() # Set initial position
        toast.show_animation()
            
    def remove_toast(self, toast):
        if toast in self.active_notifications:
            self.active_notifications.remove(toast)
            self.reposition()

    def reposition(self):
        try:
            # Safety check for App Closing
            if not self.parent or not self.parent.isVisible():
                return
            
            width = self.parent.width()
            
            for i, toast in enumerate(self.active_notifications):
                # Check if C++ object still exists before moving
                try:
                    target_y = 20 + (i * 90)
                    target_x = width - toast.width() - 20
                    toast.move(target_x, target_y)
                except RuntimeError:
                    continue # Skip this toast if it's already deleted
                    
        except RuntimeError:
            pass # Parent window destroyed
# ==========================================
#  2. MAIN APPLICATION
# ==========================================

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pharmacy Management System")
        self.setGeometry(100, 50, 1400, 850)
        self.setStyleSheet(f"background-color: {COLOR_BG};")

        database.init_db()

        self.sidebar_visible = True
        self.init_ui()

        # --- SETUP NOTIFICATIONS ---
        self.notify_manager = NotificationManager(self)
        
        # Trigger calculation 1.5 seconds after app load (gives UI time to render)
        QTimer.singleShot(1500, self.perform_calculations_and_notify)

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        right_layout.addWidget(self.create_navbar())

        self.stack = QStackedWidget()
        right_layout.addWidget(self.stack, 1)

        main_layout.addWidget(right_container, 1)

        self.load_pages()

    # --- CALCULATION & NOTIFICATION LOGIC ---
    def perform_calculations_and_notify(self):
        """
        Calculates Stock < 10 and Expiry < 120 days.
        Strictly checks conditions before showing ANY notification.
        """
        conn = database.get_connection()
        if not conn: return
        cursor = conn.cursor()

        # 1. CALCULATE LOW STOCK (Less than 10)
        try:
            cursor.execute("SELECT Med_name, Quantity FROM Medicine WHERE Quantity < 10")
            low_stock_items = cursor.fetchall()
            
            # STRICT CHECK: Only notify if list is not empty
            if low_stock_items:
                count = len(low_stock_items)
                name = low_stock_items[0][0]
                msg = f"{name} and {count-1} others are running low." if count > 1 else f"{name} is running low."
                
                self.notify_manager.show_toast(
                    title="Stock Alert",
                    message=f"Inventory Check: {msg} Please restock soon.",
                    type="warning" # Yellow Icon
                )
        except Exception as e:
            print(f"Stock Check Error: {e}")

        # 2. CALCULATE EXPIRY (Less than 120 Days)
        try:
            cursor.execute("SELECT Med_name, EXP_Date FROM Medicine")
            all_meds = cursor.fetchall()
            
            today = datetime.datetime.now()
            threshold_date = today + timedelta(days=120)
            expiring_count = 0
            expiring_name = ""

            for name, date_str in all_meds:
                if not date_str: continue
                try:
                    # Attempt to parse date (Handle YYYY-MM-DD or DD-MM-YYYY)
                    if "-" in date_str:
                        parts = date_str.split("-")
                        if len(parts[0]) == 4: # YYYY-MM-DD
                            exp_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                        else: # DD-MM-YYYY
                            exp_date = datetime.datetime.strptime(date_str, "%d-%m-%Y")
                    else:
                        continue

                    # STRICT CHECK: Is date between Today and Today+120?
                    if today <= exp_date <= threshold_date:
                        expiring_count += 1
                        if not expiring_name: expiring_name = name

                except ValueError:
                    continue 

            # STRICT CHECK: Only notify if count > 0
            if expiring_count > 0:
                msg = f"{expiring_name} and {expiring_count-1} others expiring soon." if expiring_count > 1 else f"{expiring_name} is expiring soon."
                
                self.notify_manager.show_toast(
                    title="Expiry Warning",
                    message=f"Shelf Life Alert: {msg} Check inventory.",
                    type="error" # Red Icon
                )

        except Exception as e:
            print(f"Expiry Check Error: {e}")
        finally:
            conn.close()

    # --- NAVBAR & SIDEBAR ---
    def create_navbar(self):
        navbar = QFrame()
        navbar.setFixedHeight(60)
        navbar.setStyleSheet(f"background-color: {COLOR_NAVBAR}; border-left: 1px solid #0a3d8f;")
        layout = QHBoxLayout(navbar)
        layout.setContentsMargins(20, 0, 20, 0)

        self.btn_toggle = QPushButton("☰")
        self.btn_toggle.setFixedSize(40, 40)
        self.btn_toggle.clicked.connect(self.toggle_sidebar)
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.setStyleSheet("color:white; font-size:22px; border:none; background:transparent;")
        layout.addWidget(self.btn_toggle)

        title = QLabel(" ✚ Pharmacy System")
        title.setStyleSheet("color:white; font-size:20px; font-weight:bold;")
        layout.addWidget(title)

        layout.addStretch()

        date_str = datetime.datetime.now().strftime("%b %d, %Y")
        user = QLabel(f"{date_str} | Admin")
        user.setStyleSheet("color:white; font-size:14px;")
        layout.addWidget(user)
        return navbar

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"background-color:{COLOR_SIDEBAR};")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 40, 0, 10) 
        layout.setSpacing(10)

        self.nav_buttons = {}
        for name in ["Billing", "Sales", "Stock Management", "Reports", "Orders", "Pharmacy Details"]:
            btn = QPushButton(name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(50)
            btn.clicked.connect(lambda _, n=name: self.switch_page(n))
            btn.setStyleSheet(f"QPushButton {{ border: none; text-align: left; padding-left: 25px; font-size: 15px; color: {COLOR_TEXT_NAV}; background-color: transparent; }} QPushButton:hover {{ background-color: {COLOR_ACTIVE}; }}")
            layout.addWidget(btn)
            self.nav_buttons[name] = btn

        layout.addStretch()
        ver = QLabel("v1.0.0")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet("color: #90caf9; font-size: 12px;")
        layout.addWidget(ver)
        return sidebar

    def load_pages(self):
        self.billing_page = BillingInterface()
        self.sales_page = SalesInterface()
        self.stock_page = StockInterface()
        self.reports_page = ReportsInterface()
        self.orders_page = OrdersInterface()

        self.sales_page.edit_bill_signal.connect(self.handle_edit_request)
        self.stock_page.stock_updated.connect(self.billing_page.refresh_cache)

        self.pages = {
            "Billing": self.billing_page,
            "Sales": self.sales_page,
            "Stock Management": self.stock_page,
            "Reports": self.reports_page,
            "Orders": self.orders_page,
            "Pharmacy Details": PharmacyDetailsInterface()
        }

        for page in self.pages.values():
            self.stack.addWidget(page)

        self.switch_page("Billing")

    def handle_edit_request(self, bill_id):
        self.switch_page("Billing")
        self.billing_page.load_bill_for_editing(bill_id)

    def switch_page(self, name):
        self.stack.setCurrentWidget(self.pages[name])
        for btn in self.nav_buttons.values():
            btn.setStyleSheet(f"QPushButton {{ border: none; text-align: left; padding-left: 25px; font-size: 15px; color: {COLOR_TEXT_NAV}; background-color: transparent; }} QPushButton:hover {{ background-color: {COLOR_ACTIVE}; }}")
        self.nav_buttons[name].setStyleSheet(f"QPushButton {{ border: none; text-align: left; padding-left: 25px; font-size: 15px; color: white; background-color: {COLOR_ACTIVE}; font-weight: bold; border-left: 5px solid white; }}")

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar.setFixedWidth(0)
        else:
            self.sidebar.setFixedWidth(220)
        self.sidebar_visible = not self.sidebar_visible
        
    def resizeEvent(self, event):
        if hasattr(self, 'notify_manager'):
            self.notify_manager.reposition()
        super().resizeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())