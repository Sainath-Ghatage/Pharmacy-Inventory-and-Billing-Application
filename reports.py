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
from PyQt6.QtGui import QColor, QFont, QBrush

# --- MATPLOTLIB ---
import matplotlib
matplotlib.use('QtAgg') 
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
import matplotlib.dates as mdates # NEW: For smart date formatting

import database

# --- COLORS ---
COLOR_BG = "#f8f9fa"
COLOR_WHITE = "#ffffff"
COLOR_NAVBAR = "#0d47a1"
COLOR_SIDEBAR = "#e9ecef"
COLOR_TEXT = "#212529"
COLOR_ACCENT = "#198754"
COLOR_TOTAL_ROW = "#e7f1ff"

class ReportsInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Reports & Analytics")
        self.setStyleSheet(f"""
            QWidget {{ background-color: {COLOR_BG}; font-family: 'Segoe UI', sans-serif; color: {COLOR_TEXT}; }}
            QTableWidget {{ background-color: white; border: 1px solid #ccc; gridline-color: #f0f0f0; color: {COLOR_TEXT}; }}
            QTableWidget::item {{ padding: 6px; }}
            QHeaderView::section {{ background-color: #f1f3f4; padding: 10px; border: none; border-bottom: 2px solid #ccc; font-weight: bold; font-size: 13px; color: {COLOR_TEXT}; }}
            QTreeWidget {{ border: 1px solid #ccc; background-color: {COLOR_WHITE}; border-radius: 4px; color: {COLOR_TEXT}; }}
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
        # 1. LEFT SIDEBAR
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
        
        self.add_tree_item("Sales Reports", [
            "Daily Sales Journal", "Customer/Patient Sales", 
            "Doctor Wise Sales", "Product Wise Sales"
        ])
        
        self.add_tree_item("Stock Reports", [
            "Current Stock Report", "Batch Wise Stock", "Rack Wise Stock", 
            "Supplier Stock Report", "Slow Moving Products", "Excess Stock (>100)", 
            "Fast Moving (Non-Stop)"
        ])
        
        self.add_tree_item("Procurement & Returns", [
            "Purchase Returns Details"
        ])

        self.add_tree_item("Financial Reports", [
            "Profit & Loss (Approx)"
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
        self.lbl_from.setStyleSheet(f"color: {COLOR_TEXT}; font-weight: bold;")
        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.setStyleSheet(self.input_style())
        self.date_from.dateChanged.connect(self.generate_report)
        
        self.lbl_to = QLabel("To:")
        self.lbl_to.setStyleSheet(f"color: {COLOR_TEXT}; font-weight: bold;")
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setStyleSheet(self.input_style())
        self.date_to.dateChanged.connect(self.generate_report)
        
        filter_layout.addWidget(self.lbl_from)
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(self.lbl_to)
        filter_layout.addWidget(self.date_to)

        content_layout.addWidget(filter_frame)

        # --- B. VIEW STACK ---
        self.stack = QStackedWidget()
        
        # 1. Table View
        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False) 
        self.stack.addWidget(self.table)
        
        # 2. Graph View
        self.canvas = MplCanvas(self, width=6, height=4, dpi=120) 
        self.stack.addWidget(self.canvas)
        
        content_layout.addWidget(self.stack)
        
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
        return f"border: 1px solid #ced4da; padding: 5px; border-radius: 4px; background: white; color: black; min-width: 110px;"

    def on_report_selected(self):
        item = self.tree.currentItem()
        if not item or item.childCount() > 0: return

        report_name = item.text(0)
        self.lbl_report_title.setText(report_name)
        
        is_date_relevant = report_name in [
            "Daily Sales Journal", "Customer/Patient Sales", 
            "Doctor Wise Sales", "Product Wise Sales", 
            "Slow Moving Products", "Purchase Returns Details",
            "Daily Sales Graph", "Monthly Sales Graph", "Profit & Loss (Approx)"
        ]
        
        self.lbl_from.setVisible(is_date_relevant)
        self.date_from.setVisible(is_date_relevant)
        self.lbl_to.setVisible(is_date_relevant)
        self.date_to.setVisible(is_date_relevant)
        
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
                    SELECT m.prod_name, SUM(bi.quantity), SUM(bi.total_price) 
                    FROM Bill_Item bi
                    JOIN Bill b ON bi.Bill_id = b.Bill_id
                    JOIN Product_Details m ON bi.Prod_id = m.prod_id
                    WHERE date(b.bill_date) BETWEEN ? AND ?
                    GROUP BY m.prod_name ORDER BY SUM(bi.quantity) DESC
                """
                self.run_table_query(cursor, query, (d_from, d_to), ["Product Name", "Qty Sold", "Revenue"])

            # === STOCK REPORTS ===
            elif report_name == "Current Stock Report":
                query = """
                    SELECT d.prod_name, d.type, d.rack_no, 
                           CASE WHEN d.tabs_per_strip > 1 THEN 
                               (CAST(IFNULL(SUM(s.quantity),0) AS INTEGER) / d.tabs_per_strip) || 's + ' || (CAST(IFNULL(SUM(s.quantity),0) AS INTEGER) % d.tabs_per_strip) || 't'
                           ELSE 
                               IFNULL(SUM(s.quantity), 0) || ' Units'
                           END
                    FROM Product_Details d 
                    LEFT JOIN Product_Stock s ON d.prod_id = s.prod_id 
                    GROUP BY d.prod_id ORDER BY d.prod_name
                """
                self.run_table_query(cursor, query, None, ["Product", "Type", "Rack", "Total Qty"])

            elif report_name == "Batch Wise Stock":
                query = """
                    SELECT d.prod_name, s.batch_no, s.exp_date, s.quantity, s.purchase_rate, s.sale_rate 
                    FROM Product_Stock s 
                    JOIN Product_Details d ON s.prod_id = d.prod_id 
                    ORDER BY s.exp_date ASC
                """
                self.run_table_query(cursor, query, None, ["Product", "Batch", "Expiry", "Total Units", "Buy Rate", "Sell Rate"])

            elif report_name == "Rack Wise Stock":
                query = """
                    SELECT d.rack_no, d.prod_name, 
                           CASE WHEN d.tabs_per_strip > 1 THEN 
                               (CAST(IFNULL(SUM(s.quantity),0) AS INTEGER) / d.tabs_per_strip) || 's + ' || (CAST(IFNULL(SUM(s.quantity),0) AS INTEGER) % d.tabs_per_strip) || 't'
                           ELSE 
                               IFNULL(SUM(s.quantity), 0) || ' Units'
                           END
                    FROM Product_Details d 
                    LEFT JOIN Product_Stock s ON d.prod_id = s.prod_id 
                    WHERE d.rack_no IS NOT NULL AND d.rack_no != '' 
                    GROUP BY d.prod_id ORDER BY d.rack_no
                """
                self.run_table_query(cursor, query, None, ["Rack No", "Product", "Qty"])

            elif report_name == "Supplier Stock Report":
                query = """
                    SELECT sup.Sup_name, m.prod_name, SUM(pi.quantity) as purchased
                    FROM Purchase_Invoice_Item pi
                    JOIN Purchase_Invoice p ON pi.invoice_id = p.invoice_id
                    JOIN Supplier sup ON p.supp_id = sup.Supp_id
                    JOIN Product_Details m ON pi.Prod_id = m.prod_id
                    GROUP BY sup.Sup_name, m.prod_name
                """
                self.run_table_query(cursor, query, None, ["Supplier", "Product", "Total Purchased Qty"])

            elif report_name == "Slow Moving Products":
                query = """
                    SELECT m.prod_name, m.type, IFNULL(SUM(bi.quantity), 0) as sold_qty
                    FROM Product_Details m
                    LEFT JOIN Bill_Item bi ON m.prod_id = bi.Prod_id
                    LEFT JOIN Bill b ON bi.Bill_id = b.Bill_id AND date(b.bill_date) BETWEEN ? AND ?
                    GROUP BY m.prod_id
                    HAVING sold_qty <= 10
                    ORDER BY sold_qty ASC
                """
                self.run_table_query(cursor, query, (d_from, d_to), ["Product", "Type", "Units Sold (Within Range)"])

            elif report_name == "Excess Stock (>100)":
                query = """
                    SELECT d.prod_name, 
                           CASE WHEN d.tabs_per_strip > 1 THEN 
                               (CAST(SUM(s.quantity) AS INTEGER) / d.tabs_per_strip) || 's + ' || (CAST(SUM(s.quantity) AS INTEGER) % d.tabs_per_strip) || 't'
                           ELSE 
                               SUM(s.quantity) || ' Units'
                           END
                    FROM Product_Stock s 
                    JOIN Product_Details d ON s.prod_id = d.prod_id 
                    GROUP BY d.prod_id HAVING SUM(s.quantity) > 100
                    ORDER BY SUM(s.quantity) DESC
                """
                self.run_table_query(cursor, query, None, ["Product", "Stock Qty (Strips + Loose)"], show_total=False)

            elif report_name == "Fast Moving (Non-Stop)":
                 query = """
                    SELECT m.prod_name, COUNT(bi.item_id) as freq 
                    FROM Bill_Item bi 
                    JOIN Product_Details m ON bi.Prod_id = m.prod_id 
                    GROUP BY m.prod_id ORDER BY freq DESC LIMIT 50
                """
                 self.run_table_query(cursor, query, None, ["Product", "Sales Frequency"])

            elif report_name == "Purchase Returns Details":
                 query = """
                    SELECT date(pr.return_date), pr.return_number, s.Sup_name, m.prod_name, pri.return_qty, pri.return_amount
                    FROM Purchase_Return_Item pri
                    JOIN Purchase_Return pr ON pri.return_id = pr.return_id
                    JOIN Supplier s ON pr.supp_id = s.Supp_id
                    JOIN Product_Details m ON pri.Prod_id = m.prod_id
                    WHERE date(pr.return_date) BETWEEN ? AND ?
                    ORDER BY pr.return_date DESC
                 """
                 self.run_table_query(cursor, query, (d_from, d_to), ["Return Date", "Debit Note #", "Supplier", "Returned Product", "Qty Returned", "Return Amount"])

            # === FINANCIALS ===
            elif report_name == "Profit & Loss (Approx)":
                cursor.execute("SELECT SUM(total_sum) FROM Bill WHERE date(bill_date) BETWEEN ? AND ?", (d_from, d_to))
                total_sales = cursor.fetchone()[0] or 0
                
                cursor.execute("""
                    SELECT SUM(bi.quantity * (
                        SELECT AVG(s.purchase_rate) 
                        FROM Product_Stock s 
                        WHERE s.prod_id = bi.Prod_id
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
                self.populate_table(["Category", "Description", "Amount"], data, show_total=False)

            # === GRAPHS ===
            elif report_name == "Daily Sales Graph":
                self.plot_daily_sales(cursor, d_from, d_to)
            
            elif report_name == "Monthly Sales Graph":
                self.plot_monthly_sales(cursor, d_from[:4])

        except Exception as e:
            QMessageBox.critical(self, "Report Error", str(e))
        finally:
            conn.close()

    def run_table_query(self, cursor, query, params, headers, show_total=True):
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        self.populate_table(headers, rows, show_total=show_total)

    def populate_table(self, headers, rows, show_total=True):
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(0)
        
        column_sums = [0.0] * len(headers)
        is_numeric_col = [False] * len(headers)
        sum_keywords = ['amount', 'total', 'revenue', 'spent', 'qty', 'purchased']

        for i, row in enumerate(rows):
            self.table.insertRow(i)
            for j, val in enumerate(row):
                str_val = str(val) if val is not None else ""
                item = QTableWidgetItem(str_val)
                
                if str_val.replace('.', '', 1).isdigit() or "₹" in str_val:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    clean_val = str_val.replace('₹', '').replace(',', '').replace('(', '-').replace(')', '').strip()
                    try:
                        column_sums[j] += float(clean_val)
                        is_numeric_col[j] = True
                    except ValueError:
                        pass
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                
                self.table.setItem(i, j, item)
        
        # APPEND 'TOTAL AMOUNT' ROW
        if rows and show_total:
            font_bold = QFont()
            font_bold.setBold(True)
            font_bold.setPointSize(10)
            
            total_row_idx = self.table.rowCount()
            self.table.insertRow(total_row_idx)
            
            for j, h_text in enumerate(headers):
                h_lower = h_text.lower()
                should_sum = any(k in h_lower for k in sum_keywords)
                
                if j == 0:
                    item = QTableWidgetItem("TOTAL :")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                elif should_sum and is_numeric_col[j]:
                    if "₹" in str(rows[0][j]) or any(c in h_lower for c in ['amount', 'total', 'revenue', 'spent']):
                        item = QTableWidgetItem(f"₹ {column_sums[j]:,.2f}")
                    else:
                        if column_sums[j].is_integer():
                            item = QTableWidgetItem(f"{int(column_sums[j])}")
                        else:
                            item = QTableWidgetItem(f"{column_sums[j]:.2f}")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item = QTableWidgetItem("")

                item.setFont(font_bold)
                item.setBackground(QBrush(QColor(COLOR_TOTAL_ROW)))
                self.table.setItem(total_row_idx, j, item)

        # SMART COLUMN RESIZING
        header = self.table.horizontalHeader()
        has_stretch = False
        
        for i, h_text in enumerate(headers):
            h_lower = h_text.lower()
            if any(x in h_lower for x in ['name', 'item', 'description', 'patient', 'doctor', 'product', 'supplier', 'category']):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
                has_stretch = True
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        if not has_stretch and self.table.columnCount() > 0:
            header.setSectionResizeMode(self.table.columnCount()-1, QHeaderView.ResizeMode.Stretch)

    # ==========================================
    # --- ENHANCED MODERN PLOTTING FUNCTIONS ---
    # ==========================================
    def plot_daily_sales(self, cursor, d_from, d_to):
        self.canvas.axes.clear()
        
        # Set background colors to match app perfectly
        self.canvas.figure.patch.set_facecolor(COLOR_WHITE)
        self.canvas.axes.set_facecolor(COLOR_WHITE)
        
        cursor.execute("""
            SELECT date(bill_date), SUM(total_sum) FROM Bill 
            WHERE date(bill_date) BETWEEN ? AND ? 
            GROUP BY date(bill_date) ORDER BY date(bill_date)
        """, (d_from, d_to))
        rows = cursor.fetchall()
        
        if not rows:
            self.canvas.axes.text(0.5, 0.5, "No Data Available in this date range", 
                                  ha='center', va='center', fontsize=12, color='#6c757d')
            self.canvas.draw()
            return

        # Convert string dates to actual datetime objects for smart spacing
        dates = [datetime.datetime.strptime(r[0], "%Y-%m-%d").date() for r in rows]
        values = [r[1] for r in rows]
        
        color_line = '#2563eb' # Modern Bootstrap Blue
        color_fill = '#bfdbfe'
        
        # Plot Line
        self.canvas.axes.plot(dates, values, marker='o', linestyle='-', color=color_line, 
                              linewidth=3, markersize=7, markerfacecolor='white', markeredgewidth=2)
        # Plot Fill Underneath
        self.canvas.axes.fill_between(dates, values, color=color_fill, alpha=0.4) 
        
        # Styling Titles & Labels
        self.canvas.axes.set_title("Daily Sales Trend", fontsize=15, fontweight='bold', color='#1f2937', pad=20)
        self.canvas.axes.set_ylabel("Sales Revenue", fontsize=10, fontweight='bold', color='#6b7280')
        
        # Clean up Axes
        self.canvas.axes.tick_params(axis='x', colors='#4b5563', labelsize=9)
        self.canvas.axes.tick_params(axis='y', colors='#4b5563', labelsize=9, length=0) # Hide Y ticks
        
        # Smart Date Formatter on X-Axis (E.g., "Feb 15")
        self.canvas.axes.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        self.canvas.figure.autofmt_xdate(rotation=30) # Auto rotate dates nicely
        
        # Format Y axis as currency
        self.canvas.axes.yaxis.set_major_formatter(ticker.StrMethodFormatter('₹ {x:,.0f}'))
        
        # Clean Grid and Spines (Remove all borders except bottom)
        self.canvas.axes.grid(axis='y', linestyle='-', alpha=0.3, color='#9ca3af')
        self.canvas.axes.spines['top'].set_visible(False)
        self.canvas.axes.spines['right'].set_visible(False)
        self.canvas.axes.spines['left'].set_visible(False)
        self.canvas.axes.spines['bottom'].set_color('#d1d5db')
        
        # Only show text labels if there aren't too many points (prevents clutter)
        if len(dates) <= 15:
            max_val = max(values) if values else 1
            for x, y in zip(dates, values):
                self.canvas.axes.text(x, y + (max_val*0.03), f"₹{int(y):,}", 
                                      ha='center', va='bottom', fontsize=9, color=color_line, fontweight='bold')
            
        self.canvas.figure.tight_layout()
        self.canvas.draw()

    def plot_monthly_sales(self, cursor, year):
        self.canvas.axes.clear()
        
        self.canvas.figure.patch.set_facecolor(COLOR_WHITE)
        self.canvas.axes.set_facecolor(COLOR_WHITE)
        
        cursor.execute("""
            SELECT strftime('%m', bill_date), SUM(total_sum) 
            FROM Bill WHERE strftime('%Y', bill_date) = ? 
            GROUP BY strftime('%m', bill_date)
        """, (year,))
        rows = cursor.fetchall()
        
        data = {int(r[0]): r[1] for r in rows}
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        values = [data.get(i+1, 0) for i in range(12)]
        
        color_bar = '#10b981' # Modern Emerald Green
        
        # Bar plotting 
        bars = self.canvas.axes.bar(months, values, color=color_bar, alpha=0.9, width=0.55)
        
        # Styling
        self.canvas.axes.set_title(f"Monthly Revenue - {year}", fontsize=15, fontweight='bold', color='#1f2937', pad=20)
        self.canvas.axes.set_ylabel("Sales Revenue", fontsize=10, fontweight='bold', color='#6b7280')
        
        # Clean up Axes
        self.canvas.axes.tick_params(axis='x', colors='#4b5563', labelsize=10)
        self.canvas.axes.tick_params(axis='y', colors='#4b5563', labelsize=9, length=0)
        
        # Format Y axis as currency
        self.canvas.axes.yaxis.set_major_formatter(ticker.StrMethodFormatter('₹ {x:,.0f}'))

        # Clean Grid and Spines
        self.canvas.axes.grid(axis='y', linestyle='-', alpha=0.3, color='#9ca3af')
        self.canvas.axes.spines['top'].set_visible(False)
        self.canvas.axes.spines['right'].set_visible(False)
        self.canvas.axes.spines['left'].set_visible(False)
        self.canvas.axes.spines['bottom'].set_color('#d1d5db')
        
        # Add text labels on bars
        max_val = max(values) if values else 1
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                self.canvas.axes.text(bar.get_x() + bar.get_width()/2, height + (max_val*0.015), f"₹{int(height):,}", 
                                      ha='center', va='bottom', fontsize=9, color='#047857', fontweight='bold')
                                      
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