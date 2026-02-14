import sys
import datetime
import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QPushButton, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

# --- MATPLOTLIB FOR CHARTS ---
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates

import database

# --- COLORS ---
COLOR_BG = "#f4f7f6"
COLOR_CARD = "#ffffff"
COLOR_PRIMARY = "#0d47a1"
COLOR_TEXT = "#212529"
COLOR_ACCENT = "#198754"  # Green
COLOR_WARNING = "#ffc107" # Yellow
COLOR_DANGER = "#dc3545"  # Red

class DashboardInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {COLOR_BG}; font-family: 'Segoe UI', sans-serif;")
        
        self.init_ui()
        self.refresh_data()
        
        # Auto-refresh dashboard every 60 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(60000)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 1. Header with Welcome & Date
        header_layout = QHBoxLayout()
        
        self.lbl_welcome = QLabel("👋 Welcome, Admin")
        self.lbl_welcome.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLOR_PRIMARY};")
        
        self.lbl_date = QLabel(datetime.datetime.now().strftime("%A, %d %B %Y"))
        self.lbl_date.setStyleSheet("font-size: 16px; color: #6c757d;")
        
        header_layout.addWidget(self.lbl_welcome)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_date)
        
        main_layout.addLayout(header_layout)

        # 2. Key Metrics Cards (Sales, Expenses, Profit)
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(20)
        
        self.card_sales = self.create_metric_card("Today's Sales", "₹0.00", "▲ 0%", COLOR_ACCENT)
        self.card_expenses = self.create_metric_card("Today's Expenses", "₹0.00", "▼ 0%", COLOR_DANGER)
        self.card_stock = self.create_metric_card("Low Stock Items", "0", "Alert", COLOR_WARNING)
        self.card_expiry = self.create_metric_card("Expiring (30 Days)", "0", "Warning", COLOR_DANGER)
        
        self.cards_layout.addWidget(self.card_sales)
        self.cards_layout.addWidget(self.card_expenses)
        self.cards_layout.addWidget(self.card_stock)
        self.cards_layout.addWidget(self.card_expiry)
        
        main_layout.addLayout(self.cards_layout)

        # 3. Middle Section: Chart (Left) + Recent Activity (Right)
        middle_layout = QHBoxLayout()
        
        # Chart Container
        chart_frame = QFrame()
        chart_frame.setStyleSheet(f"background-color: {COLOR_CARD}; border-radius: 10px;")
        chart_layout = QVBoxLayout(chart_frame)
        
        lbl_chart = QLabel("Sales Trend (Last 7 Days)")
        lbl_chart.setStyleSheet(f"font-weight: bold; font-size: 16px; color: {COLOR_TEXT};")
        chart_layout.addWidget(lbl_chart)
        
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        chart_layout.addWidget(self.canvas)
        
        middle_layout.addWidget(chart_frame, 65) # 65% width

        # Recent Activity Feed
        activity_frame = QFrame()
        activity_frame.setStyleSheet(f"background-color: {COLOR_CARD}; border-radius: 10px;")
        activity_layout = QVBoxLayout(activity_frame)
        
        lbl_act = QLabel("Recent Bills")
        lbl_act.setStyleSheet(f"font-weight: bold; font-size: 16px; color: {COLOR_TEXT};")
        activity_layout.addWidget(lbl_act)
        
        self.activity_list_widget = QWidget()
        self.activity_list_layout = QVBoxLayout(self.activity_list_widget)
        self.activity_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.activity_list_widget)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        activity_layout.addWidget(scroll)
        
        middle_layout.addWidget(activity_frame, 35) # 35% width
        
        main_layout.addLayout(middle_layout, 1) # Expandable

    def create_metric_card(self, title, value, subtext, color_code):
        card = QFrame()
        card.setFixedHeight(120)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_CARD};
                border-radius: 10px;
                border-left: 5px solid {color_code};
            }}
        """)
        layout = QVBoxLayout(card)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #6c757d; font-size: 14px;")
        
        lbl_value = QLabel(value)
        lbl_value.setObjectName("ValueLabel") # For easy finding later
        lbl_value.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 26px; font-weight: bold;")
        
        lbl_sub = QLabel(subtext)
        lbl_sub.setObjectName("SubLabel")
        lbl_sub.setStyleSheet(f"color: {color_code}; font-size: 12px; font-weight: bold;")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        layout.addWidget(lbl_sub)
        return card

    def refresh_data(self):
        conn = database.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        today = datetime.date.today()
        today_str = today.strftime("%Y-%m-%d")

        # 1. Today's Sales
        try:
            cursor.execute("SELECT SUM(total_sum) FROM Bill WHERE date(bill_date) = ?", (today_str,))
            sales = cursor.fetchone()[0] or 0.0
            self.update_card(self.card_sales, f"₹{sales:,.2f}", "Daily Revenue")
        except: pass

        # 2. Today's Expenses
        try:
            cursor.execute("SELECT SUM(amount) FROM Expenses WHERE date(expense_date) = ?", (today_str,))
            exp = cursor.fetchone()[0] or 0.0
            self.update_card(self.card_expenses, f"₹{exp:,.2f}", "Daily Overhead")
        except: pass

        # 3. Low Stock
        try:
            cursor.execute("SELECT Count(*) FROM Medicine WHERE Quantity < 10")
            low_count = cursor.fetchone()[0]
            self.update_card(self.card_stock, str(low_count), "Items to Order")
        except: pass

        # 4. Expiry
        try:
            threshold = (today + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
            cursor.execute("SELECT Count(*) FROM Medicine WHERE EXP_Date <= ? AND EXP_Date >= ?", (threshold, today_str))
            exp_count = cursor.fetchone()[0]
            self.update_card(self.card_expiry, str(exp_count), "Critical Items")
        except: pass

        # 5. Chart Data (Last 7 Days)
        dates = []
        values = []
        for i in range(6, -1, -1):
            d = today - datetime.timedelta(days=i)
            d_str = d.strftime("%Y-%m-%d")
            cursor.execute("SELECT SUM(total_sum) FROM Bill WHERE date(bill_date) = ?", (d_str,))
            val = cursor.fetchone()[0] or 0.0
            dates.append(d.strftime("%d %b"))
            values.append(val)
        
        self.plot_chart(dates, values)

        # 6. Recent Activity
        self.populate_activity(cursor)

        conn.close()

    def update_card(self, card, value, subtext):
        card.findChild(QLabel, "ValueLabel").setText(value)
        card.findChild(QLabel, "SubLabel").setText(subtext)

    def plot_chart(self, x_data, y_data):
        self.canvas.axes.clear()
        self.canvas.axes.plot(x_data, y_data, marker='o', color=COLOR_PRIMARY, linewidth=2)
        self.canvas.axes.fill_between(x_data, y_data, color=COLOR_PRIMARY, alpha=0.1)
        self.canvas.axes.set_title("Sales Performance", fontsize=10)
        self.canvas.axes.grid(True, linestyle='--', alpha=0.5)
        self.canvas.draw()

    def populate_activity(self, cursor):
        # Clear old items
        for i in reversed(range(self.activity_list_layout.count())): 
            self.activity_list_layout.itemAt(i).widget().setParent(None)

        # --- FIX: Changed 'patient' to 'patient_name' to match new DB schema ---
        try:
            cursor.execute("SELECT Bill_id, patient_name, total_sum, bill_date FROM Bill ORDER BY Bill_id DESC LIMIT 10")
            rows = cursor.fetchall()
        except sqlite3.OperationalError:
            # Fallback if running on old database schema (just in case)
            try:
                cursor.execute("SELECT Bill_id, patient, total_sum, bill_date FROM Bill ORDER BY Bill_id DESC LIMIT 10")
                rows = cursor.fetchall()
            except:
                rows = []
        
        for bid, pat, amt, date in rows:
            row_widget = QFrame()
            row_widget.setStyleSheet(f"border-bottom: 1px solid #eee; padding: 5px;")
            rl = QHBoxLayout(row_widget)
            
            lbl_id = QLabel(f"#{bid}")
            lbl_id.setStyleSheet("font-weight: bold; color: #0d47a1; width: 40px;")
            
            # Ensure pat is not None
            display_name = pat if pat else "Walk-in"
            lbl_info = QLabel(display_name)
            
            lbl_amt = QLabel(f"₹{amt:.2f}")
            lbl_amt.setStyleSheet("font-weight: bold; color: #198754;")
            
            rl.addWidget(lbl_id)
            rl.addWidget(lbl_info)
            rl.addStretch()
            rl.addWidget(lbl_amt)
            
            self.activity_list_layout.addWidget(row_widget)

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.15)
        super(MplCanvas, self).__init__(fig)

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = DashboardInterface()
    w.show()
    sys.exit(app.exec())