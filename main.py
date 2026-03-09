import os
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"
import sys
import datetime
from datetime import timedelta
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QStackedWidget, QGraphicsOpacityEffect, 
    QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon

import database

# --- Import Interfaces ---
from dashboard import DashboardInterface
from billing import BillingInterface
from pharmacy_details import PharmacyDetailsInterface
from sales import SalesInterface
from reports import ReportsInterface
from stock_management import StockInterface
from orders import OrdersInterface
from purchase_entry import PurchaseEntryInterface 
from partner_management import PartnerManagementInterface
from accounts import AccountsInterface
from purchase_return import PurchaseReturnInterface

# ---------- COLORS ----------
COLOR_NAVBAR = "#0d47a1"   # Deep Blue
COLOR_SIDEBAR = "#0d47a1"  # MATCHED Navbar color
COLOR_BG = "#f4f7f6"       # Light Gray Background
COLOR_ACTIVE = "#1976d2"   # Lighter Blue for active state
COLOR_TEXT_NAV = "#ffffff" # White text for sidebar
COLOR_TEXT_HEADER = "#90caf9" # Light blue for sidebar headers

# ==========================================
#  1. NOTIFICATION SYSTEM
# ==========================================
class ToastNotification(QWidget):
    def __init__(self, parent, title, message, type="warning"):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFixedSize(350, 80)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

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

        self.layout = QHBoxLayout(self.container)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(15)

        if type == "success":
            icon_color, icon_symbol = "#2ecc71", "✔"
        elif type == "error":
            icon_color, icon_symbol = "#e74c3c", "✖"
        else:
            icon_color, icon_symbol = "#f1c40f", "!"

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

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        self.lbl_title = QLabel(title.upper())
        self.lbl_title.setStyleSheet("color: white; font-weight: bold; font-size: 12px; border: none; background: transparent;")
        
        self.lbl_msg = QLabel(message)
        self.lbl_msg.setWordWrap(True)
        self.lbl_msg.setStyleSheet("color: white; font-size: 11px; border: none; background: transparent;")
        
        text_layout.addWidget(self.lbl_title)
        text_layout.addWidget(self.lbl_msg)
        self.layout.addLayout(text_layout)

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(20, 20)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.close_notification)
        self.btn_close.setStyleSheet("""
            QPushButton { color: white; background: transparent; border: none; font-weight: bold; }
            QPushButton:hover { color: #cccccc; }
        """)
        self.layout.addWidget(self.btn_close, alignment=Qt.AlignmentFlag.AlignTop)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close_notification)
        self.timer.start(6000) # Increased duration slightly to 6 seconds

    def show_animation(self):
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
        if not self.parent or not self.parent.isVisible(): return
        toast = ToastNotification(self.parent, title, message, type)
        toast.destroyed.connect(lambda: self.remove_toast(toast))
        self.active_notifications.append(toast)
        self.reposition()
        toast.show_animation()
            
    def remove_toast(self, toast):
        if toast in self.active_notifications:
            self.active_notifications.remove(toast)
            self.reposition()

    def reposition(self):
        try:
            if not self.parent or not self.parent.isVisible(): return
            width = self.parent.width()
            for i, toast in enumerate(self.active_notifications):
                try:
                    target_y = 20 + (i * 90)
                    target_x = width - toast.width() - 20
                    toast.move(target_x, target_y)
                except RuntimeError: continue
        except RuntimeError: pass

# ==========================================
#  2. MAIN APPLICATION
# ==========================================
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pharmacy Management System")
        self.setGeometry(100, 50, 1400, 850)
        self.setStyleSheet(f"background-color: {COLOR_BG}; font-family: 'Segoe UI', sans-serif;")

        # Ensure DB is ready
        database.init_db()

        self.sidebar_visible = True
        self.init_ui()

        # --- SETUP NOTIFICATIONS ---
        self.notify_manager = NotificationManager(self)
        # Increased initial delay to 3500ms to guarantee window is fully painted and visible before querying
        QTimer.singleShot(3500, self.perform_calculations_and_notify) 

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)

        # 2. Main Content
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        right_layout.addWidget(self.create_navbar())
        
        self.stack = QStackedWidget()
        right_layout.addWidget(self.stack, 1)

        main_layout.addWidget(right_container, 1)

        self.load_pages()

    # --- SIDEBAR STRUCTURE ---
    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"background-color:{COLOR_SIDEBAR}; border-right: 1px solid #082e66;")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 20, 0, 10) 
        layout.setSpacing(5)

        self.nav_buttons = {}

        # --- Helper to create section headers ---
        def add_header(text):
            lbl = QLabel(text.upper())
            lbl.setStyleSheet(f"color: {COLOR_TEXT_HEADER}; font-size: 11px; font-weight: bold; padding-left: 15px; margin-top: 15px; margin-bottom: 5px;")
            layout.addWidget(lbl)

        # --- Helper to create buttons ---
        def add_nav_btn(name, label):
            btn = QPushButton(f"  {label}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(45)
            btn.clicked.connect(lambda _, n=name: self.switch_page(n))
            # Initial Style
            btn.setStyleSheet(self.get_btn_style(False))
            layout.addWidget(btn)
            self.nav_buttons[name] = btn

        # 1. CORE
        add_header("Main")
        add_nav_btn("Dashboard", "Dashboard")
        add_nav_btn("Billing", "Billing / POS")

        # 2. INVENTORY
        add_header("Inventory & Procurement")
        add_nav_btn("Inventory", "Product Stock")
        add_nav_btn("Purchase Entry", "Purchase Invoice") 
        add_nav_btn("Purchase Returns", "Purchase Returns")
        add_nav_btn("Orders", "Purchase Orders")
        
        # 3. RECORDS
        add_header("Records")
        add_nav_btn("Sales", "Sales History")
        add_nav_btn("Reports", "Reports && Analytics")
        add_nav_btn("Accounts", "Expenses && Accounts")

        # 4. ADMIN
        add_header("Admin")
        add_nav_btn("Partners", "Partner Management")
        add_nav_btn("Pharmacy", "Pharmacy Profile")

        layout.addStretch()
        
        # Version Info
        ver = QLabel("v2.3.0")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet("color: #64b5f6; font-size: 11px;")
        layout.addWidget(ver)
        
        return sidebar

    def get_btn_style(self, is_active):
        if is_active:
            return f"""
                QPushButton {{ 
                    border: none; text-align: left; padding-left: 20px; 
                    font-size: 14px; color: white; 
                    background-color: {COLOR_ACTIVE}; 
                    font-weight: bold; 
                    border-left: 4px solid white; 
                }}
            """
        else:
            return f"""
                QPushButton {{ 
                    border: none; text-align: left; padding-left: 20px; 
                    font-size: 14px; color: {COLOR_TEXT_NAV}; 
                    background-color: transparent; 
                }} 
                QPushButton:hover {{ background-color: {COLOR_ACTIVE}; }}
            """

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

    # --- PAGE LOGIC ---
    def load_pages(self):
        # Instantiate Pages
        self.dashboard_page = DashboardInterface()
        self.billing_page = BillingInterface()
        self.sales_page = SalesInterface()
        self.stock_page = StockInterface()
        self.reports_page = ReportsInterface()
        self.orders_page = OrdersInterface()
        self.pharma_page = PharmacyDetailsInterface()
        self.purchase_page = PurchaseEntryInterface() 
        self.purchase_return_page = PurchaseReturnInterface() 
        self.partner_page = PartnerManagementInterface()
        self.accounts_page = AccountsInterface() 

        # Connect Signals
        self.sales_page.edit_bill_signal.connect(self.handle_edit_request)
        self.stock_page.stock_updated.connect(self.billing_page.refresh_cache)
        
        # When stock changes (from manual edit OR purchase entry OR return), refresh other views
        self.stock_page.stock_updated.connect(self.dashboard_page.refresh_data)
        
        # Connect the return page signal to refresh the dashboard and billing cache
        self.purchase_return_page.return_processed.connect(self.dashboard_page.refresh_data)
        self.purchase_return_page.return_processed.connect(self.billing_page.refresh_cache)

        # Mapping names to instances
        self.pages = {
            "Dashboard": self.dashboard_page,
            "Billing": self.billing_page,
            "Sales": self.sales_page,
            "Inventory": self.stock_page,
            "Reports": self.reports_page,
            "Orders": self.orders_page,
            "Pharmacy": self.pharma_page,
            "Purchase Entry": self.purchase_page,
            "Purchase Returns": self.purchase_return_page, 
            "Partners": self.partner_page,
            "Accounts": self.accounts_page 
        }

        # Add to Stack
        for page in self.pages.values():
             self.stack.addWidget(page)

        # Default Page
        self.switch_page("Dashboard")

    def handle_edit_request(self, bill_id):
        self.switch_page("Billing")
        self.billing_page.load_bill_for_editing(bill_id)

    def switch_page(self, name):
        if name in self.pages:
            current_page = self.pages[name]
            self.stack.setCurrentWidget(current_page)
            
            # ==========================================
            # SMART LAZY REFRESH LOGIC
            # ==========================================
            try:
                if name == "Dashboard":
                    self.dashboard_page.refresh_data()
                    
                elif name == "Billing":
                    if hasattr(self.billing_page, 'refresh_cache'):
                        self.billing_page.refresh_cache()
                        
                elif name == "Inventory":
                    if hasattr(self.stock_page, 'load_data'):
                        self.stock_page.load_data()
                        
                elif name == "Purchase Entry":
                    if hasattr(self.purchase_page, 'load_history'):
                        self.purchase_page.load_history()
                        
                elif name == "Purchase Returns":
                    if hasattr(self.purchase_return_page, 'load_initial_data'):
                        self.purchase_return_page.load_initial_data() 
                        
                elif name == "Sales":
                    if hasattr(self.sales_page, 'load_sales_data'):
                        self.sales_page.load_sales_data()
                    elif hasattr(self.sales_page, 'load_data'):
                        self.sales_page.load_data()
                        
                elif name == "Reports":
                    if hasattr(self.reports_page, 'generate_report'):
                        self.reports_page.generate_report()
                        
                elif name == "Orders":
                    if hasattr(self.orders_page, 'load_history'):
                        self.orders_page.load_history()
                        
                elif name == "Partners":
                    if hasattr(self.partner_page, 'tab_customer'):
                        self.partner_page.tab_customer.load_data()
                        self.partner_page.tab_doctor.load_data()
                        self.partner_page.tab_supplier.load_data()
                        
                elif name == "Accounts":
                    if hasattr(self.accounts_page, 'load_expenses'):
                        self.accounts_page.load_expenses()
            except Exception as e:
                print(f"Error refreshing page '{name}': {e}")
            
            # Update visual state of sidebar buttons
            for btn_name, btn in self.nav_buttons.items():
                is_active = (btn_name == name)
                btn.setStyleSheet(self.get_btn_style(is_active))

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar.setFixedWidth(0)
        else:
            self.sidebar.setFixedWidth(240)
        self.sidebar_visible = not self.sidebar_visible
        
    def resizeEvent(self, event):
        if hasattr(self, 'notify_manager'):
            self.notify_manager.reposition()
        super().resizeEvent(event)

    # --- NOTIFICATIONS ---
    def perform_calculations_and_notify(self):
        conn = database.get_connection()
        if not conn: return
        cursor = conn.cursor()

        try:
            # 1. Low Stock Check (Dynamically checks min_qty)
            cursor.execute("PRAGMA table_info(Product_Stock)")
            cols = [c[1] for c in cursor.fetchall()]
            
            if "min_qty" in cols:
                cursor.execute("""
                    SELECT d.prod_name 
                    FROM Product_Details d
                    JOIN Product_Stock s ON d.prod_id = s.prod_id
                    WHERE s.quantity <= s.min_qty
                """)
            else:
                cursor.execute("""
                    SELECT d.prod_name 
                    FROM Product_Details d
                    JOIN Product_Stock s ON d.prod_id = s.prod_id
                    WHERE s.quantity < 10
                """)
                
            low_rows = cursor.fetchall()
            if low_rows:
                count = len(low_rows)
                name = low_rows[0][0]
                msg = f"{name} and {count-1} others are running low." if count > 1 else f"{name} is running low."
                self.notify_manager.show_toast("Stock Alert", msg, "warning")

            # 2. Expiry Alert (Robust Check for MM/YY and YYYY-MM-DD)
            today = datetime.datetime.now().date()

            cursor.execute("""
                SELECT d.prod_name, s.exp_date 
                FROM Product_Details d
                JOIN Product_Stock s ON d.prod_id = s.prod_id
            """)
            all_stock = cursor.fetchall()
            
            exp_count = 0
            exp_name = ""

            for name, exp_str in all_stock:
                if not exp_str: continue # Skip if no expiry given
                
                days_left = 9999
                try:
                    if "/" in exp_str:
                        m_str, y_str = exp_str.split("/")
                        # Convert YY to YYYY
                        y_int = int(y_str)
                        if y_int < 100: y_int += 2000
                        exp_dt = datetime.date(y_int, int(m_str), 1)
                        days_left = (exp_dt - today).days
                    elif "-" in exp_str:
                        # Parse YYYY-MM-DD
                        exp_dt = datetime.datetime.strptime(exp_str, "%Y-%m-%d").date()
                        days_left = (exp_dt - today).days
                except Exception as parse_err:
                    print(f"Date Parse Error on {exp_str}: {parse_err}")
                    continue

                # 60 Days Threshold for "Expiring Soon"
                if days_left <= 60:
                    exp_count += 1
                    if not exp_name: exp_name = name

            if exp_count > 0:
                msg = f"{exp_name} and {exp_count-1} others expiring soon (or expired)." if exp_count > 1 else f"{exp_name} is expiring soon."
                self.notify_manager.show_toast("Expiry Alert", msg, "error")

        except Exception as e:
            print(f"Notification Error: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())