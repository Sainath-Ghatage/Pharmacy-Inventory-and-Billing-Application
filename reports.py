import sys
import sqlite3
import datetime
import numpy as np 
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QSpinBox, QRadioButton, QButtonGroup, 
    QFrame, QMessageBox, QSizePolicy, QListView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# --- MATPLOTLIB ---
import matplotlib
matplotlib.use('QtAgg') 
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import database

# --- COLORS ---
COLOR_BG = "#f8f9fa"       
COLOR_WHITE = "#ffffff"    
COLOR_NAVBAR = "#0d47a1"   
COLOR_TEXT = "#212529"     

class ReportsInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reports & Analytics")
        self.showMaximized()
        self.setStyleSheet(f"background-color: {COLOR_BG}; font-family: 'Segoe UI', Arial, sans-serif;")
        
        self.init_ui()
        self.on_report_type_changed() # Set initial state
        self.generate_report()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ==========================================
        # 1. TOP CONTROL BAR
        # ==========================================
        controls_frame = QFrame()
        
        # --- IMPROVED CSS ---
        controls_frame.setStyleSheet(f"""
            QFrame {{ 
                background-color: {COLOR_WHITE}; 
                border-bottom: 1px solid #dee2e6; 
            }}
            QLabel {{ 
                font-weight: bold; 
                color: {COLOR_TEXT}; 
                margin-right: 5px; 
            }}
            QRadioButton {{ 
                color: {COLOR_TEXT}; 
                font-size: 14px; 
            }}
            
            /* --- COMBOBOX STYLE --- */
            QComboBox {{
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px;
                padding-left: 10px;
                background-color: {COLOR_WHITE};
                color: {COLOR_TEXT};
                font-size: 14px;
                min-width: 100px;
            }}
            QComboBox:hover {{
                border: 1px solid {COLOR_NAVBAR};
            }}
            /* Removed ::down-arrow styling so the default visible system arrow is used */
            
            /* The Dropdown List Popup */
            QListView {{
                border: 1px solid #ced4da;
                background-color: {COLOR_WHITE};
                selection-background-color: {COLOR_NAVBAR};
                selection-color: white;
                color: {COLOR_TEXT};
                outline: none;
                padding: 5px;
            }}
            
            /* --- SPINBOX STYLE --- */
            QSpinBox {{
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px;
                background-color: {COLOR_WHITE};
                color: {COLOR_TEXT};
            }}
        """)

        bar_layout = QHBoxLayout(controls_frame)
        bar_layout.setContentsMargins(15, 10, 15, 10)
        bar_layout.setSpacing(15)

        # Title
        lbl_title = QLabel("Analytics")
        lbl_title.setStyleSheet(f"font-size: 20px; color: {COLOR_NAVBAR}; margin-right: 20px;")
        bar_layout.addWidget(lbl_title)

        # Report Type
        bar_layout.addWidget(QLabel("Type:"))
        self.combo_type = QComboBox()
        self.combo_type.setView(QListView()) 
        self.combo_type.addItems(["Sales Report", "Profit & Loss Report"])
        self.combo_type.setFixedWidth(180)
        self.combo_type.currentIndexChanged.connect(self.on_report_type_changed)
        bar_layout.addWidget(self.combo_type)

        # Month
        bar_layout.addWidget(QLabel("Month:"))
        self.combo_month = QComboBox()
        self.combo_month.setView(QListView())
        self.combo_month.addItems(["January", "February", "March", "April", "May", "June", 
                                   "July", "August", "September", "October", "November", "December"])
        self.combo_month.setCurrentIndex(datetime.date.today().month - 1)
        self.combo_month.setFixedWidth(130)
        self.combo_month.currentIndexChanged.connect(self.generate_report)
        bar_layout.addWidget(self.combo_month)

        # Year
        bar_layout.addWidget(QLabel("Year:"))
        self.spin_year = QSpinBox()
        self.spin_year.setRange(2000, 2100)
        self.spin_year.setValue(datetime.date.today().year)
        self.spin_year.setFixedWidth(80)
        self.spin_year.valueChanged.connect(self.generate_report)
        bar_layout.addWidget(self.spin_year)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        bar_layout.addWidget(line)

        # View By (Radio Buttons)
        bar_layout.addWidget(QLabel("View:"))
        self.radio_group = QButtonGroup(self)
        
        self.rb_daily = QRadioButton("Daily")
        self.rb_weekly = QRadioButton("Weekly")
        self.rb_monthly = QRadioButton("Monthly")
        self.rb_yearly = QRadioButton("Yearly")
        
        self.rb_daily.setChecked(True)

        self.radio_group.addButton(self.rb_daily)
        self.radio_group.addButton(self.rb_weekly)
        self.radio_group.addButton(self.rb_monthly)
        self.radio_group.addButton(self.rb_yearly)
        
        # Connect signals
        self.rb_daily.toggled.connect(self.generate_report)
        self.rb_weekly.toggled.connect(self.generate_report)
        self.rb_monthly.toggled.connect(self.generate_report)
        self.rb_yearly.toggled.connect(self.generate_report)

        bar_layout.addWidget(self.rb_daily)
        bar_layout.addWidget(self.rb_weekly)
        bar_layout.addWidget(self.rb_monthly)
        bar_layout.addWidget(self.rb_yearly)

        bar_layout.addStretch()
        main_layout.addWidget(controls_frame)

        # ==========================================
        # 2. CHART AREA
        # ==========================================
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.canvas, 1)

    def on_report_type_changed(self):
        """Show/Hide radio buttons based on Report Type"""
        report_type = self.combo_type.currentText()
        
        if report_type == "Profit & Loss Report":
            # HIDE Daily and Weekly
            self.rb_daily.setHidden(True)
            self.rb_weekly.setHidden(True)
            self.rb_monthly.setHidden(False)
            self.rb_yearly.setHidden(False)
            
            # If current selection is hidden, switch to Monthly
            if self.rb_daily.isChecked() or self.rb_weekly.isChecked():
                self.rb_monthly.setChecked(True)
        else: 
            # SHOW ALL
            self.rb_daily.setHidden(False)
            self.rb_weekly.setHidden(False)
            self.rb_monthly.setHidden(False)
            self.rb_yearly.setHidden(False)
            
        self.generate_report()

    def generate_report(self, *args):
        report_type = self.combo_type.currentText()
        month_idx = self.combo_month.currentIndex() + 1
        year = self.spin_year.value()
        
        frequency = "Daily"
        if self.rb_weekly.isChecked(): frequency = "Weekly"
        if self.rb_monthly.isChecked(): frequency = "Monthly"
        if self.rb_yearly.isChecked(): frequency = "Yearly"

        self.canvas.axes.clear()

        conn = database.get_connection()
        if not conn: return
        cursor = conn.cursor()

        try:
            if report_type == "Sales Report":
                self.plot_sales_report(cursor, frequency, month_idx, year)
            else:
                self.plot_profit_loss(cursor, frequency, year)
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"Plot Error: {e}")
            self.canvas.axes.text(0.5, 0.5, f"Error: {str(e)}", 
                                  ha='center', va='center', transform=self.canvas.axes.transAxes)
        finally:
            conn.close()

    # ============================================
    # SALES REPORT LOGIC
    # ============================================
    def plot_sales_report(self, cursor, frequency, month, year):
        data_x = []
        data_y = []
        title = ""
        xlabel = ""
        
        if frequency == "Daily":
            cursor.execute("""
                SELECT strftime('%d', bill_date), SUM(total_sum)
                FROM Bill WHERE strftime('%Y', bill_date) = ? AND strftime('%m', bill_date) = ?
                GROUP BY strftime('%d', bill_date)
            """, (str(year), str(month).zfill(2)))
            rows = cursor.fetchall()
            data_dict = {str(int(r[0])): r[1] for r in rows}
            
            for i in range(1, 32):
                data_x.append(str(i))
                data_y.append(data_dict.get(str(i), 0))
            
            title = f"Daily Sales - {self.get_month_names()[month-1]} {year}"
            xlabel = "Day of Month"

        elif frequency == "Weekly":
            cursor.execute("""
                SELECT strftime('%d', bill_date), total_sum
                FROM Bill WHERE strftime('%Y', bill_date) = ? AND strftime('%m', bill_date) = ?
            """, (str(year), str(month).zfill(2)))
            rows = cursor.fetchall()
            
            weeks = [0, 0, 0, 0, 0]
            for r in rows:
                day = int(r[0])
                week_idx = (day - 1) // 7
                if week_idx < 5:
                    weeks[week_idx] += r[1]
            
            data_x = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"]
            data_y = weeks
            title = f"Weekly Sales - {self.get_month_names()[month-1]} {year}"
            xlabel = "Week"

        elif frequency == "Monthly":
            cursor.execute("""
                SELECT strftime('%m', bill_date), SUM(total_sum)
                FROM Bill WHERE strftime('%Y', bill_date) = ?
                GROUP BY strftime('%m', bill_date)
            """, (str(year),))
            rows = cursor.fetchall()
            data_dict = {str(int(r[0])): r[1] for r in rows} 
            
            month_names = self.get_month_names()
            for i in range(1, 13):
                data_x.append(month_names[i-1][:3]) 
                data_y.append(data_dict.get(str(i), 0))
                
            title = f"Monthly Sales Trend - {year}"
            xlabel = "Month"

        elif frequency == "Yearly":
            cursor.execute("""
                SELECT strftime('%Y', bill_date), SUM(total_sum)
                FROM Bill
                GROUP BY strftime('%Y', bill_date)
                ORDER BY strftime('%Y', bill_date) ASC
            """)
            rows = cursor.fetchall()
            for r in rows:
                data_x.append(str(r[0]))
                data_y.append(r[1])
            
            title = "Yearly Sales Comparison"
            xlabel = "Year"

        # Plot Data
        self.canvas.axes.plot(data_x, data_y, marker='o', linestyle='-', color='#0d47a1', linewidth=2)
        self.canvas.axes.fill_between(data_x, data_y, color='#0d47a1', alpha=0.1) 
        
        if data_y:
            max_val = max(data_y)
            self.canvas.axes.set_ylim(0, max_val * 1.15) 

        self.canvas.axes.set_title(title, fontsize=12, fontweight='bold')
        self.canvas.axes.set_ylabel("Sales (₹)")
        self.canvas.axes.set_xlabel(xlabel)
        self.canvas.axes.grid(True, linestyle='--', alpha=0.6)

    # ============================================
    # PROFIT & LOSS REPORT LOGIC
    # ============================================
    def plot_profit_loss(self, cursor, frequency, year):
        labels = []
        purchase_data = []
        sales_data = []
        net_profit_data = []
        title = ""
        xlabel = ""

        base_query = """
            SELECT {}, 
                   SUM(bi.quantity * m.Purchase_Price) as total_purchase,
                   SUM(bi.quantity * m.Sale_Price) as total_sales
            FROM Bill_Item bi
            JOIN Bill b ON bi.Bill_id = b.Bill_id
            JOIN Medicine m ON bi.Med_id = m.Med_id
            WHERE {}
            GROUP BY {}
            ORDER BY {} ASC
        """

        if frequency == "Monthly":
            select_part = "strftime('%m', b.bill_date)"
            where_part = "strftime('%Y', b.bill_date) = ?"
            group_part = "strftime('%m', b.bill_date)"
            
            cursor.execute(base_query.format(select_part, where_part, group_part, group_part), (str(year),))
            rows = cursor.fetchall()
            
            p_dict = {int(r[0]): r[1] for r in rows}
            s_dict = {int(r[0]): r[2] for r in rows}
            
            month_names = self.get_month_names()
            for i in range(1, 13):
                labels.append(month_names[i-1][:3])
                p_val = p_dict.get(i, 0) or 0
                s_val = s_dict.get(i, 0) or 0
                purchase_data.append(p_val)
                sales_data.append(s_val)
                net_profit_data.append(s_val - p_val) 
                
            title = f"Profit & Loss Analysis - {year}"
            xlabel = "Month"

        elif frequency == "Yearly":
            select_part = "strftime('%Y', b.bill_date)"
            where_part = "1=1" 
            group_part = "strftime('%Y', b.bill_date)"
            
            cursor.execute(base_query.format(select_part, where_part, group_part, group_part))
            rows = cursor.fetchall()
            
            for r in rows:
                labels.append(str(r[0]))
                p_val = r[1] or 0
                s_val = r[2] or 0
                purchase_data.append(p_val)
                sales_data.append(s_val)
                net_profit_data.append(s_val - p_val)
                
            title = "Annual Profit & Loss Comparison"
            xlabel = "Year"

        # --- PLOTTING ---
        if not labels:
            self.canvas.axes.text(0.5, 0.5, "No Data Available", ha='center', fontsize=12)
            return

        x = np.arange(len(labels))
        width = 0.35 

        # 1. Bar Chart
        rects1 = self.canvas.axes.bar(x - width/2, purchase_data, width, label='Purchase Cost', color='#dc3545', alpha=0.8)
        rects2 = self.canvas.axes.bar(x + width/2, sales_data, width, label='Sales Revenue', color='#198754', alpha=0.8)

        # 2. Line Chart
        self.canvas.axes.plot(x, net_profit_data, color='blue', marker='o', linestyle='--', linewidth=2, label='Net Profit')

        # 3. Add Values
        def autolabel(rects):
            for rect in rects:
                height = rect.get_height()
                if height > 0:
                    self.canvas.axes.annotate(f'{int(height)}',
                                xy=(rect.get_x() + rect.get_width() / 2, height),
                                xytext=(0, 5),  
                                textcoords="offset points",
                                ha='center', va='bottom', fontsize=9, rotation=90)

        autolabel(rects1)
        autolabel(rects2)

        all_values = purchase_data + sales_data
        if all_values:
            max_height = max(all_values)
            self.canvas.axes.set_ylim(0, max_height * 1.25)

        # 4. Total Profit Summary Box
        total_profit = sum(net_profit_data)
        self.canvas.axes.text(0.02, 0.95, f"Total Profit: ₹{total_profit:,.2f}", 
                              transform=self.canvas.axes.transAxes, 
                              fontsize=12, fontweight='bold', 
                              bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="black", alpha=0.8))

        self.canvas.axes.set_title(title, fontsize=14, fontweight='bold')
        self.canvas.axes.set_ylabel('Amount (₹)')
        self.canvas.axes.set_xlabel(xlabel)
        self.canvas.axes.set_xticks(x)
        self.canvas.axes.set_xticklabels(labels)
        self.canvas.axes.legend(loc='upper right')
        self.canvas.axes.grid(axis='y', linestyle='--', alpha=0.4)

    def get_month_names(self):
        return ["January", "February", "March", "April", "May", "June", 
                "July", "August", "September", "October", "November", "December"]

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        fig.subplots_adjust(left=0.08, right=0.95, top=0.92, bottom=0.15)
        super(MplCanvas, self).__init__(fig)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ReportsInterface()
    window.show() 
    sys.exit(app.exec())