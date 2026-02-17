import sys
import sqlite3
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QDateEdit, QPushButton, QFrame, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QTreeWidget, QTreeWidgetItem, QStackedWidget, 
    QMessageBox, QFileDialog, QAbstractItemView, QSizePolicy
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont

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
COLOR_SIDEBAR = "#e9ecef"
COLOR_TEXT = "#212529"
COLOR_ACCENT = "#198754"

class ReportsInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Reports & Analytics")
        self.setStyleSheet(f"""
            QWidget {{ background-color: {COLOR_BG}; font-family: 'Segoe UI', sans-serif; color: {COLOR_TEXT}; }}
            QTableWidget {{ background-color: white; border: 1px solid #ccc; gridline-color: #f0f0f0; }}
            QTableWidget::item {{ padding: 5px; }}
            QHeaderView::section {{ background-color: #f1f3f4; padding: 8px; border: none; border-bottom: 1px solid #ccc; font-weight: bold; font-size: 12px; }}
            QTreeWidget {{ border: 1px solid #ccc; background-color: {COLOR_WHITE}; border-radius: 4px; }}
            QTreeWidget::item {{ padding: 6px; }}
            QTreeWidget::item:selected {{ background-color: {COLOR_NAVBAR}; color: white; }}
        """)
        
        self.init_ui()
        
        # Select first report by default
        top_item = self.tree.topLevelItem(0)
        if top_item:
            top_item.setExpanded(True)
            self.tree.setCurrentItem(top_item.child(0))
            self.on_report_selected()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ==========================================
        # 1. LEFT SIDEBAR (REPORT NAVIGATION)
        # ==========================================
        sidebar_frame = QFrame()
        sidebar_frame.setFixedWidth(260)
        sidebar_frame.setStyleSheet(f"background-color: {COLOR_SIDEBAR}; border-right: 1px solid #dee2e6;")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        
        lbl_nav = QLabel("Report Categories")
        lbl_nav.setStyleSheet(f"font-weight: bold; font-size: 15px; color: {COLOR_NAVBAR}; margin-bottom: 10px;")
        sidebar_layout.addWidget(lbl_nav)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        
        # --- POPULATE TREE ---
        self.add_tree_item("Sales Reports", [
            "Daily Sales Journal", "Sundry Sales Details", "Customer/Patient Sales", 
            "Doctor Wise Sales", "Product Wise Sales"
        ])
        
        self.add_tree_item("Stock Reports", [
            "Current Stock Report", "Batch Wise Stock", "Rack Wise Stock", 
            "Supplier Stock Report", "Slow Moving Products", "Excess Stock (>100)", 
            "Fast Moving (Non-Stop)"
        ])
        
        self.add_tree_item("Financial Reports", [
            "Profit & Loss (Approx)", "Balance Sheet (Approx)"
        ])
        
        self.add_tree_item("Visual Analytics", [
            "Daily Sales Graph", "Monthly Sales Graph"
        ])

        sidebar_layout.addWidget(self.tree)
        self.tree.itemSelectionChanged.connect(self.on_report_selected)
        
        main_layout.addWidget(sidebar_frame)

        # ==========================================
        # 2. RIGHT CONTENT AREA
        # ==========================================
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- A. FILTER BAR ---
        filter_frame = QFrame()
        filter_frame.setFixedHeight(60)
        filter_frame.setStyleSheet(f"background-color: {COLOR_WHITE}; border-bottom: 1px solid #dee2e6;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(20, 10, 20, 10)
        filter_layout.setSpacing(15)
        
        self.lbl_report_title = QLabel("Select a Report")
        self.lbl_report_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_NAVBAR};")
        filter_layout.addWidget(self.lbl_report_title)
        
        filter_layout.addStretch()
        
        # Date Filters
        self.lbl_from = QLabel("From:")
        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.setStyleSheet(self.input_style())
        self.date_from.dateChanged.connect(self.generate_report)
        
        self.lbl_to = QLabel("To:")
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setStyleSheet(self.input_style())
        self.date_to.dateChanged.connect(self.generate_report)
        
        filter_layout.addWidget(self.lbl_from)
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(self.lbl_to)
        filter_layout.addWidget(self.date_to)

        content_layout.addWidget(filter_frame)

        # --- B. VIEW STACK (Table vs Graph) ---
        self.stack = QStackedWidget()
        
        # 1. Table View
        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False) 
        self.stack.addWidget(self.table)
        
        # 2. Graph View
        self.canvas = MplCanvas(self, width=5, height=4, dpi=120) # Higher DPI
        self.stack.addWidget(self.canvas)
        
        content_layout.addWidget(self.stack)
        
        # Wrap content
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget)

    def add_tree_item(self, parent_name, children):
        parent = QTreeWidgetItem([parent_name])
        parent.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))
        for child_name in children:
            child = QTreeWidgetItem([child_name])
            child.setFont(0, QFont("Segoe UI", 10))
            parent.addChild(child)
        self.tree.addTopLevelItem(parent)

    def input_style(self):
        return f"border: 1px solid #ced4da; padding: 5px; border-radius: 4px; background: white; min-width: 100px;"

    def on_report_selected(self):
        item = self.tree.currentItem()
        if not item or item.childCount() > 0: return

        report_name = item.text(0)
        self.lbl_report_title.setText(report_name)
        
        # Show/Hide Date Filters
        is_date_relevant = report_name in [
            "Daily Sales Journal", "Sundry Sales Details", "Customer/Patient Sales", 
            "Doctor Wise Sales", "Product Wise Sales", 
            "Daily Sales Graph", "Monthly Sales Graph", "Profit & Loss (Approx)"
        ]
        
        self.lbl_from.setVisible(is_date_relevant)
        self.date_from.setVisible(is_date_relevant)
        self.lbl_to.setVisible(is_date_relevant)
        self.date_to.setVisible(is_date_relevant)
        
        # Switch View
        if "Graph" in report_name:
            self.stack.setCurrentWidget(self.canvas)
        else:
            self.stack.setCurrentWidget(self.table)
            self.table.setRowCount(0)
            self.table.setColumnCount(0)

        self.generate_report()

    def generate_report(self):
        item = self.tree.currentItem()
        if not item: return
        report_name = item.text(0)
        
        d_from = self.date_from.date().toString("yyyy-MM-dd")
        d_to = self.date_to.date().toString("yyyy-MM-dd")
        
        conn = database.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        try:
            # === SALES REPORTS ===
            if report_name == "Daily Sales Journal":
                query = """
                    SELECT bill_date, Bill_id, patient_name, doctor_name, payment_method, total_sum 
                    FROM Bill WHERE date(bill_date) BETWEEN ? AND ? ORDER BY bill_date DESC
                """
                self.run_table_query(cursor, query, (d_from, d_to), 
                                     ["Date", "Bill #", "Patient", "Doctor", "Pay Mode", "Amount"])

            elif report_name == "Sundry Sales Details":
                query = """
                    SELECT b.bill_date, b.Bill_id, m.med_name, bi.quantity, bi.unit_price, bi.total_price 
                    FROM Bill_Item bi 
                    JOIN Bill b ON bi.Bill_id = b.Bill_id
                    JOIN Medicine_Details m ON bi.Med_id = m.med_id
                    WHERE date(b.bill_date) BETWEEN ? AND ?
                """
                self.run_table_query(cursor, query, (d_from, d_to), 
                                     ["Date", "Bill #", "Item", "Qty", "Rate", "Total"])

            elif report_name == "Customer/Patient Sales":
                query = """
                    SELECT patient_name, COUNT(Bill_id), SUM(total_sum) 
                    FROM Bill WHERE date(bill_date) BETWEEN ? AND ? 
                    GROUP BY patient_name ORDER BY SUM(total_sum) DESC
                """
                self.run_table_query(cursor, query, (d_from, d_to), ["Patient Name", "Total Bills", "Total Spent"])

            elif report_name == "Doctor Wise Sales":
                query = """
                    SELECT doctor_name, COUNT(Bill_id), SUM(total_sum) 
                    FROM Bill WHERE date(bill_date) BETWEEN ? AND ? 
                    GROUP BY doctor_name ORDER BY SUM(total_sum) DESC
                """
                self.run_table_query(cursor, query, (d_from, d_to), ["Doctor Name", "Prescriptions", "Revenue Generated"])

            elif report_name == "Product Wise Sales":
                query = """
                    SELECT m.med_name, SUM(bi.quantity), SUM(bi.total_price) 
                    FROM Bill_Item bi
                    JOIN Bill b ON bi.Bill_id = b.Bill_id
                    JOIN Medicine_Details m ON bi.Med_id = m.med_id
                    WHERE date(b.bill_date) BETWEEN ? AND ?
                    GROUP BY m.med_name ORDER BY SUM(bi.quantity) DESC
                """
                self.run_table_query(cursor, query, (d_from, d_to), ["Medicine Name", "Qty Sold", "Revenue"])

            # === STOCK REPORTS ===
            elif report_name == "Current Stock Report":
                # Converts total units to "X Strips + Y Tabs" for display
                query = """
                    SELECT d.med_name, d.type, d.rack_no, 
                           CASE WHEN d.tabs_per_strip > 1 THEN 
                               (CAST(IFNULL(SUM(s.quantity),0) AS INTEGER) / d.tabs_per_strip) || 's + ' || (CAST(IFNULL(SUM(s.quantity),0) AS INTEGER) % d.tabs_per_strip) || 't'
                           ELSE 
                               IFNULL(SUM(s.quantity), 0) || ' Units'
                           END
                    FROM Medicine_Details d 
                    LEFT JOIN Medicine_Stock s ON d.med_id = s.med_id 
                    GROUP BY d.med_id ORDER BY d.med_name
                """
                self.run_table_query(cursor, query, None, ["Medicine", "Type", "Rack", "Total Qty"])

            elif report_name == "Batch Wise Stock":
                # Shows raw quantity because batch wise might be easier to read as total tabs for auditing
                query = """
                    SELECT d.med_name, s.batch_no, s.exp_date, s.quantity, s.purchase_rate, s.sale_rate 
                    FROM Medicine_Stock s 
                    JOIN Medicine_Details d ON s.med_id = d.med_id 
                    ORDER BY s.exp_date ASC
                """
                self.run_table_query(cursor, query, None, ["Medicine", "Batch", "Expiry", "Total Tabs", "Buy Rate", "Sell Rate"])

            elif report_name == "Rack Wise Stock":
                query = """
                    SELECT d.rack_no, d.med_name, 
                           CASE WHEN d.tabs_per_strip > 1 THEN 
                               (CAST(IFNULL(SUM(s.quantity),0) AS INTEGER) / d.tabs_per_strip) || 's + ' || (CAST(IFNULL(SUM(s.quantity),0) AS INTEGER) % d.tabs_per_strip) || 't'
                           ELSE 
                               IFNULL(SUM(s.quantity), 0) || ' Units'
                           END
                    FROM Medicine_Details d 
                    LEFT JOIN Medicine_Stock s ON d.med_id = s.med_id 
                    WHERE d.rack_no IS NOT NULL AND d.rack_no != '' 
                    GROUP BY d.med_id ORDER BY d.rack_no
                """
                self.run_table_query(cursor, query, None, ["Rack No", "Medicine", "Qty"])

            elif report_name == "Supplier Stock Report":
                query = """
                    SELECT sup.Sup_name, m.med_name, SUM(pi.quantity) as purchased
                    FROM Purchase_Invoice_Item pi
                    JOIN Purchase_Invoice p ON pi.invoice_id = p.invoice_id
                    JOIN Supplier sup ON p.supp_id = sup.Supp_id
                    JOIN Medicine_Details m ON pi.Med_id = m.med_id
                    GROUP BY sup.Sup_name, m.med_name
                """
                self.run_table_query(cursor, query, None, ["Supplier", "Medicine", "Total Purchased Qty"])

            elif report_name == "Slow Moving Products":
                query = """
                    SELECT med_name, type, manufacturer FROM Medicine_Details 
                    WHERE med_id NOT IN (
                        SELECT DISTINCT Med_id FROM Bill_Item 
                        JOIN Bill ON Bill_Item.Bill_id = Bill.Bill_id 
                        WHERE date(Bill.bill_date) >= date('now', '-30 days')
                    )
                """
                self.run_table_query(cursor, query, None, ["Medicine", "Type", "Manufacturer"])

            elif report_name == "Excess Stock (>100)":
                # Adjusted to show Strips/Tabs logic
                query = """
                    SELECT d.med_name, 
                           CASE WHEN d.tabs_per_strip > 1 THEN 
                               (CAST(SUM(s.quantity) AS INTEGER) / d.tabs_per_strip) || 's + ' || (CAST(SUM(s.quantity) AS INTEGER) % d.tabs_per_strip) || 't'
                           ELSE 
                               SUM(s.quantity) || ' Units'
                           END
                    FROM Medicine_Stock s 
                    JOIN Medicine_Details d ON s.med_id = d.med_id 
                    GROUP BY d.med_id HAVING SUM(s.quantity) > 100
                """
                self.run_table_query(cursor, query, None, ["Medicine", "Total Quantity"])

            elif report_name == "Fast Moving (Non-Stop)":
                 query = """
                    SELECT m.med_name, COUNT(bi.item_id) as freq 
                    FROM Bill_Item bi 
                    JOIN Medicine_Details m ON bi.Med_id = m.med_id 
                    GROUP BY m.med_id ORDER BY freq DESC LIMIT 50
                """
                 self.run_table_query(cursor, query, None, ["Medicine", "Sales Frequency"])

            # === FINANCIALS ===
            elif report_name == "Profit & Loss (Approx)":
                cursor.execute("SELECT SUM(total_sum) FROM Bill WHERE date(bill_date) BETWEEN ? AND ?", (d_from, d_to))
                total_sales = cursor.fetchone()[0] or 0
                
                cursor.execute("""
                    SELECT SUM(bi.quantity * (
                        SELECT AVG(s.purchase_rate) 
                        FROM Medicine_Stock s 
                        WHERE s.med_id = bi.Med_id
                    )) 
                    FROM Bill_Item bi 
                    JOIN Bill b ON bi.Bill_id = b.Bill_id
                    WHERE date(b.bill_date) BETWEEN ? AND ?
                """, (d_from, d_to))
                cogs = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT SUM(amount) FROM Expenses WHERE date(expense_date) BETWEEN ? AND ?", (d_from, d_to))
                expenses = cursor.fetchone()[0] or 0
                
                gross = total_sales - cogs
                net = gross - expenses
                
                data = [
                    ["Revenue", "Total Sales", f"₹{total_sales:.2f}"],
                    ["Cost", "Cost of Goods Sold", f"(₹{cogs:.2f})"],
                    ["Result", "Gross Profit", f"₹{gross:.2f}"],
                    ["Expense", "Operational Expenses", f"(₹{expenses:.2f})"],
                    ["Result", "NET PROFIT", f"₹{net:.2f}"]
                ]
                self.populate_table(["Category", "Description", "Amount"], data)

            elif report_name == "Balance Sheet (Approx)":
                cursor.execute("SELECT SUM(quantity * purchase_rate) FROM Medicine_Stock")
                stock_val = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT SUM(balance) FROM Supplier")
                supp_dues = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT SUM(balance) FROM Customer")
                cust_dues = cursor.fetchone()[0] or 0
                
                data = [
                    ["Asset", "Closing Stock Value", f"₹{stock_val:.2f}"],
                    ["Asset", "Customer Receivables", f"₹{cust_dues:.2f}"],
                    ["Liability", "Supplier Payables", f"₹{supp_dues:.2f}"],
                    ["Equity", "Estimated Equity", f"₹{stock_val + cust_dues - supp_dues:.2f}"]
                ]
                self.populate_table(["Type", "Account", "Amount"], data)

            # === GRAPHS ===
            elif report_name == "Daily Sales Graph":
                self.plot_daily_sales(cursor, d_from, d_to)
            
            elif report_name == "Monthly Sales Graph":
                self.plot_monthly_sales(cursor, d_from[:4])

        except Exception as e:
            QMessageBox.critical(self, "Report Error", str(e))
        finally:
            conn.close()

    def run_table_query(self, cursor, query, params, headers):
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        self.populate_table(headers, rows)

    def populate_table(self, headers, rows):
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(0)
        
        for i, row in enumerate(rows):
            self.table.insertRow(i)
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val is not None else "")
                
                # Align numbers right, text left
                if str(val).replace('.', '', 1).isdigit() or "₹" in str(val):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                
                self.table.setItem(i, j, item)
        
        # SMART COLUMN RESIZING
        header = self.table.horizontalHeader()
        
        has_stretch = False
        for i, h_text in enumerate(headers):
            h_text_lower = h_text.lower()
            # If column is descriptive, Stretch it
            if any(x in h_text_lower for x in ['name', 'item', 'description', 'patient', 'doctor', 'medicine']):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
                has_stretch = True
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        # Ensure at least one column stretches if none found
        if not has_stretch and self.table.columnCount() > 0:
            header.setSectionResizeMode(self.table.columnCount()-1, QHeaderView.ResizeMode.Stretch)

    # --- PLOTTING FUNCTIONS ---
    def plot_daily_sales(self, cursor, d_from, d_to):
        self.canvas.axes.clear()
        cursor.execute("""
            SELECT date(bill_date), SUM(total_sum) FROM Bill 
            WHERE date(bill_date) BETWEEN ? AND ? 
            GROUP BY date(bill_date) ORDER BY date(bill_date)
        """, (d_from, d_to))
        rows = cursor.fetchall()
        
        dates = [r[0] for r in rows]
        values = [r[1] for r in rows]
        
        self.canvas.axes.plot(dates, values, marker='o', linestyle='-', color='#0d47a1', linewidth=2)
        self.canvas.axes.set_title("Daily Sales Trend", fontsize=12, fontweight='bold')
        self.canvas.axes.set_ylabel("Sales (₹)")
        self.canvas.axes.tick_params(axis='x', rotation=30)
        self.canvas.axes.grid(True, linestyle='--', alpha=0.5)
        
        # Add values on top of points
        for x, y in zip(dates, values):
            self.canvas.axes.text(x, y, f"{int(y)}", ha='center', va='bottom', fontsize=9)
            
        self.canvas.figure.tight_layout()
        self.canvas.draw()

    def plot_monthly_sales(self, cursor, year):
        self.canvas.axes.clear()
        cursor.execute("""
            SELECT strftime('%m', bill_date), SUM(total_sum) 
            FROM Bill WHERE strftime('%Y', bill_date) = ? 
            GROUP BY strftime('%m', bill_date)
        """, (year,))
        rows = cursor.fetchall()
        
        data = {int(r[0]): r[1] for r in rows}
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        values = [data.get(i+1, 0) for i in range(12)]
        
        bars = self.canvas.axes.bar(months, values, color='#198754', alpha=0.8)
        self.canvas.axes.set_title(f"Monthly Sales - {year}", fontsize=12, fontweight='bold')
        self.canvas.axes.set_ylabel("Sales (₹)")
        self.canvas.axes.grid(axis='y', linestyle='--', alpha=0.5)
        
        # Add values on bars
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                self.canvas.axes.text(bar.get_x() + bar.get_width()/2, height, f"{int(height)}", 
                                      ha='center', va='bottom', fontsize=9)
                                      
        self.canvas.figure.tight_layout()
        self.canvas.draw()

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

if __name__ == "__main__":
    app = sys.modules['__main__'].QApplication(sys.argv)
    window = ReportsInterface()
    window.show() 
    sys.exit(app.exec())