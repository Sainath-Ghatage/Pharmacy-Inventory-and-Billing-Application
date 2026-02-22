import sys
import sqlite3
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QDateEdit, QPushButton, QFrame, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QTreeWidget, QTreeWidgetItem, QStackedWidget, 
    QMessageBox, QFileDialog, QAbstractItemView, QSizePolicy, QTabWidget, QGridLayout
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont, QBrush

# --- MATPLOTLIB ---
import matplotlib
matplotlib.use('QtAgg') 
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
import matplotlib.dates as mdates

import database

# --- COLORS ---
COLOR_BG = "#f8f9fa"
COLOR_WHITE = "#ffffff"
COLOR_NAVBAR = "#0d47a1"
COLOR_SIDEBAR = "#e9ecef"
COLOR_TEXT = "#212529"
COLOR_TOTAL_ROW = "#e7f1ff"
COLOR_HIGHLIGHT = "#fff3cd"

# --- FINANCIAL COLORS ---
C_REV = "#198754"      # Green
C_COST = "#fd7e14"     # Orange
C_EXP = "#dc3545"      # Red
C_PROFIT = "#198754"   # Bold Green
C_LOSS = "#dc3545"     # Bold Red
C_HEAD = "#0d47a1"     # Navy Blue for Headers

class FinancialDashboard(QWidget):
    """Custom Widget for the Multi-Tabbed Financial Report with Summary Cards"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # --- TOP CARDS PANEL ---
        self.cards_layout = QHBoxLayout()
        self.lbl_net_profit = self.create_card("Net Profit", "₹0.00", C_PROFIT)
        self.lbl_margin = self.create_card("Gross Margin %", "0.0%", C_REV)
        self.lbl_exp_ratio = self.create_card("Expense Ratio", "0.0%", C_EXP)
        self.lbl_receivables = self.create_card("Receivables", "₹0.00", C_COST)
        self.lbl_cash = self.create_card("Cash Balance", "₹0.00", COLOR_NAVBAR) 
        
        layout.addLayout(self.cards_layout)

        # --- MULTI-TAB PANEL ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid #ccc; background: white; border-radius: 4px; }}
            QTabBar::tab {{ background: #f1f3f5; color: #495057; padding: 10px 20px; font-weight: bold; border-right: 1px solid #ccc; }}
            QTabBar::tab:selected {{ background: white; color: {COLOR_NAVBAR}; border-top: 3px solid {COLOR_NAVBAR}; }}
        """)
        
        # TAB 1: Profit & Loss
        self.tab_pl = QTableWidget()
        self.setup_fin_table(self.tab_pl, ["Category", "Description", "Amount"])
        self.tabs.addTab(self.tab_pl, "📈 Profit & Loss")

        # TAB 2: Cash Flow
        self.tab_cash = QTableWidget()
        self.setup_fin_table(self.tab_cash, ["Type", "Description", "Amount"])
        self.tabs.addTab(self.tab_cash, "💸 Cash Flow")

        # TAB 3: Receivables & Payables
        self.tab_dues = QTableWidget()
        self.setup_fin_table(self.tab_dues, ["Type", "Party / Description", "Pending Balance"])
        self.tabs.addTab(self.tab_dues, "🧾 Receivables & Payables")

        # TAB 4: Stock Valuation
        self.tab_stock = QTableWidget()
        self.setup_fin_table(self.tab_stock, ["Category", "Metric", "Valuation"])
        self.tabs.addTab(self.tab_stock, "📦 Stock Valuation")

        layout.addWidget(self.tabs)

    def create_card(self, title, value, color):
        frame = QFrame()
        frame.setStyleSheet(f"background-color: white; border-radius: 6px; border-left: 4px solid {color}; border-top: 1px solid #ddd; border-right: 1px solid #ddd; border-bottom: 1px solid #ddd;")
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(15, 10, 15, 10)
        
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #6c757d; font-size: 12px; font-weight: bold; border: none;")
        v_lbl = QLabel(value)
        v_lbl.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold; border: none;")
        
        vl.addWidget(t_lbl)
        vl.addWidget(v_lbl)
        self.cards_layout.addWidget(frame)
        return v_lbl

    def setup_fin_table(self, table, headers):
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setStyleSheet("QTableWidget { background-color: white; border: none; } QTableWidget::item { padding: 8px; border-bottom: 1px solid #eee; }")

    def add_row(self, table, category, desc, amount, format_type="normal"):
        """Formats the row beautifully based on accounting logic"""
        r = table.rowCount()
        table.insertRow(r)
        
        # Amount formatting
        amt_val = float(amount) if amount else 0.0
        amt_str = f"₹{abs(amt_val):,.2f}"
        
        font_main = QFont("Segoe UI", 10)
        color = QColor(COLOR_TEXT)
        
        if format_type == "header":
            font_main.setBold(True)
            color = QColor(C_HEAD)
            amt_str = ""
            desc = desc.upper()
        elif format_type == "revenue":
            color = QColor(C_REV)
        elif format_type == "cost":
            color = QColor(C_COST)
            if amt_val > 0: amt_str = f"(₹{amt_val:,.2f})"
        elif format_type == "expense":
            color = QColor(C_EXP)
            if amt_val > 0: amt_str = f"(₹{amt_val:,.2f})"
        elif format_type == "profit":
            font_main.setBold(True)
            font_main.setPointSize(11)
            color = QColor(C_PROFIT) if amt_val >= 0 else QColor(C_LOSS)
            amt_str = f"₹{amt_val:,.2f}" if amt_val >= 0 else f"(₹{abs(amt_val):,.2f})"
            for i in range(3): table.setItem(r, i, QTableWidgetItem("")) # Spacer effect
            
        elif format_type == "subtotal":
            font_main.setBold(True)
        
        # Force red/bracket formatting for actual negative values passed directly
        if amt_val < 0 and format_type not in ["cost", "expense"]:
            amt_str = f"(₹{abs(amt_val):,.2f})"
            color = QColor(C_LOSS)

        item_cat = QTableWidgetItem(category)
        item_cat.setFont(font_main)
        item_cat.setForeground(QBrush(color))
        
        item_desc = QTableWidgetItem(desc)
        item_desc.setFont(font_main)
        item_desc.setForeground(QBrush(color))
        
        item_amt = QTableWidgetItem(amt_str)
        item_amt.setFont(font_main)
        item_amt.setForeground(QBrush(color))
        item_amt.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        if format_type in ["profit", "subtotal", "header"]:
            bg_brush = QBrush(QColor("#f8f9fa"))
            item_cat.setBackground(bg_brush); item_desc.setBackground(bg_brush); item_amt.setBackground(bg_brush)

        table.setItem(r, 0, item_cat)
        table.setItem(r, 1, item_desc)
        table.setItem(r, 2, item_amt)


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
        
        top_item = self.tree.topLevelItem(0)
        if top_item:
            top_item.setExpanded(True)
            self.tree.setCurrentItem(top_item.child(0))
            self.on_report_selected()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. LEFT SIDEBAR
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
        
        self.add_tree_item("Sales Reports", ["Daily Sales Journal", "Customer/Patient Sales", "Doctor Wise Sales", "Product Wise Sales"])
        self.add_tree_item("Stock Reports", ["Current Stock Report", "Batch Wise Stock", "Rack Wise Stock", "Supplier Stock Report", "Slow Moving Products", "Excess Stock (>100)", "Fast Moving (Non-Stop)"])
        self.add_tree_item("Procurement & Returns", ["Purchase Returns Details"])
        self.add_tree_item("Financial Reports", ["Financial Dashboard (P&L)"])
        self.add_tree_item("Visual Analytics", ["Daily Sales Graph", "Monthly Sales Graph"])

        sidebar_layout.addWidget(self.tree)
        self.tree.itemSelectionChanged.connect(self.on_report_selected)
        main_layout.addWidget(sidebar_frame)

        # 2. RIGHT CONTENT AREA
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- FILTER BAR ---
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
        
        self.lbl_from = QLabel("From:"); self.lbl_from.setStyleSheet(f"color: {COLOR_TEXT}; font-weight: bold;")
        self.date_from = QDateEdit(QDate.currentDate().addDays(-30)); self.date_from.setCalendarPopup(True); self.date_from.setStyleSheet(self.input_style()); self.date_from.dateChanged.connect(self.generate_report)
        
        self.lbl_to = QLabel("To:"); self.lbl_to.setStyleSheet(f"color: {COLOR_TEXT}; font-weight: bold;")
        self.date_to = QDateEdit(QDate.currentDate()); self.date_to.setCalendarPopup(True); self.date_to.setStyleSheet(self.input_style()); self.date_to.dateChanged.connect(self.generate_report)
        
        filter_layout.addWidget(self.lbl_from); filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(self.lbl_to); filter_layout.addWidget(self.date_to)

        content_layout.addWidget(filter_frame)

        # --- VIEW STACK ---
        self.stack = QStackedWidget()
        
        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False) 
        self.stack.addWidget(self.table)
        
        self.canvas = MplCanvas(self, width=6, height=4, dpi=120) 
        self.stack.addWidget(self.canvas)

        self.fin_dash = FinancialDashboard(self)
        self.stack.addWidget(self.fin_dash)
        
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
        return "border: 1px solid #ced4da; padding: 5px; border-radius: 4px; background: white; color: black; min-width: 110px;"

    def on_report_selected(self):
        item = self.tree.currentItem()
        if not item or item.childCount() > 0: return

        report_name = item.text(0)
        self.lbl_report_title.setText(report_name)
        
        is_date_relevant = report_name in [
            "Daily Sales Journal", "Customer/Patient Sales", "Doctor Wise Sales", "Product Wise Sales", 
            "Slow Moving Products", "Purchase Returns Details", "Daily Sales Graph", "Monthly Sales Graph", "Financial Dashboard (P&L)"
        ]
        
        self.lbl_from.setVisible(is_date_relevant); self.date_from.setVisible(is_date_relevant)
        self.lbl_to.setVisible(is_date_relevant); self.date_to.setVisible(is_date_relevant)
        
        if "Graph" in report_name:
            self.stack.setCurrentWidget(self.canvas)
        elif report_name == "Financial Dashboard (P&L)":
            self.stack.setCurrentWidget(self.fin_dash)
        else:
            self.stack.setCurrentWidget(self.table)
            self.table.setRowCount(0); self.table.setColumnCount(0)

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
            # === ADVANCED FINANCIAL DASHBOARD LOGIC ===
            if report_name == "Financial Dashboard (P&L)":
                self.populate_financial_dashboard(cursor, d_from, d_to)
                
            # === STANDARD TABLE REPORTS ===
            elif report_name == "Daily Sales Journal":
                self.run_table_query(cursor, "SELECT bill_date, Bill_id, patient_name, doctor_name, payment_method, total_sum FROM Bill WHERE date(bill_date) BETWEEN ? AND ? ORDER BY bill_date DESC", (d_from, d_to), ["Date", "Bill #", "Patient", "Doctor", "Pay Mode", "Amount"])
            elif report_name == "Customer/Patient Sales":
                self.run_table_query(cursor, "SELECT patient_name, COUNT(Bill_id), SUM(total_sum) FROM Bill WHERE date(bill_date) BETWEEN ? AND ? GROUP BY patient_name ORDER BY SUM(total_sum) DESC", (d_from, d_to), ["Patient Name", "Total Bills", "Total Spent"])
            elif report_name == "Doctor Wise Sales":
                self.run_table_query(cursor, "SELECT doctor_name, COUNT(Bill_id), SUM(total_sum) FROM Bill WHERE date(bill_date) BETWEEN ? AND ? GROUP BY doctor_name ORDER BY SUM(total_sum) DESC", (d_from, d_to), ["Doctor Name", "Prescriptions", "Revenue Generated"])
            elif report_name == "Product Wise Sales":
                self.run_table_query(cursor, "SELECT m.prod_name, SUM(bi.quantity), SUM(bi.total_price) FROM Bill_Item bi JOIN Bill b ON bi.Bill_id = b.Bill_id JOIN Product_Details m ON bi.Prod_id = m.prod_id WHERE date(b.bill_date) BETWEEN ? AND ? GROUP BY m.prod_name ORDER BY SUM(bi.quantity) DESC", (d_from, d_to), ["Product Name", "Qty Sold", "Revenue"])
            
            # === STOCK REPORTS ===
            elif report_name == "Current Stock Report":
                q = "SELECT d.prod_name, d.type, d.rack_no, CASE WHEN d.tabs_per_strip > 1 THEN (CAST(IFNULL(SUM(s.quantity),0) AS INTEGER) / d.tabs_per_strip) || 's + ' || (CAST(IFNULL(SUM(s.quantity),0) AS INTEGER) % d.tabs_per_strip) || 't' ELSE IFNULL(SUM(s.quantity), 0) || ' Units' END FROM Product_Details d LEFT JOIN Product_Stock s ON d.prod_id = s.prod_id GROUP BY d.prod_id ORDER BY d.prod_name"
                self.run_table_query(cursor, q, None, ["Product", "Type", "Rack", "Total Qty"])
            elif report_name == "Batch Wise Stock":
                self.run_table_query(cursor, "SELECT d.prod_name, s.batch_no, s.exp_date, s.quantity, s.purchase_rate, s.sale_rate FROM Product_Stock s JOIN Product_Details d ON s.prod_id = d.prod_id ORDER BY s.exp_date ASC", None, ["Product", "Batch", "Expiry", "Total Units", "Buy Rate", "Sell Rate"])
            elif report_name == "Rack Wise Stock":
                q = "SELECT d.rack_no, d.prod_name, CASE WHEN d.tabs_per_strip > 1 THEN (CAST(IFNULL(SUM(s.quantity),0) AS INTEGER) / d.tabs_per_strip) || 's + ' || (CAST(IFNULL(SUM(s.quantity),0) AS INTEGER) % d.tabs_per_strip) || 't' ELSE IFNULL(SUM(s.quantity), 0) || ' Units' END FROM Product_Details d LEFT JOIN Product_Stock s ON d.prod_id = s.prod_id WHERE d.rack_no IS NOT NULL AND d.rack_no != '' GROUP BY d.prod_id ORDER BY d.rack_no"
                self.run_table_query(cursor, q, None, ["Rack No", "Product", "Qty"])
            elif report_name == "Supplier Stock Report":
                self.run_table_query(cursor, "SELECT sup.Sup_name, m.prod_name, SUM(pi.quantity) as purchased FROM Purchase_Invoice_Item pi JOIN Purchase_Invoice p ON pi.invoice_id = p.invoice_id JOIN Supplier sup ON p.supp_id = sup.Supp_id JOIN Product_Details m ON pi.Prod_id = m.prod_id GROUP BY sup.Sup_name, m.prod_name", None, ["Supplier", "Product", "Total Purchased Qty"])
            elif report_name == "Slow Moving Products":
                q = "SELECT m.prod_name, m.type, IFNULL(SUM(bi.quantity), 0) as sold_qty FROM Product_Details m LEFT JOIN Bill_Item bi ON m.prod_id = bi.Prod_id LEFT JOIN Bill b ON bi.Bill_id = b.Bill_id AND date(b.bill_date) BETWEEN ? AND ? GROUP BY m.prod_id HAVING sold_qty <= 10 ORDER BY sold_qty ASC"
                self.run_table_query(cursor, q, (d_from, d_to), ["Product", "Type", "Units Sold (Within Range)"])
            elif report_name == "Excess Stock (>100)":
                q = "SELECT d.prod_name, CASE WHEN d.tabs_per_strip > 1 THEN (CAST(SUM(s.quantity) AS INTEGER) / d.tabs_per_strip) || 's + ' || (CAST(SUM(s.quantity) AS INTEGER) % d.tabs_per_strip) || 't' ELSE SUM(s.quantity) || ' Units' END FROM Product_Stock s JOIN Product_Details d ON s.prod_id = d.prod_id GROUP BY d.prod_id HAVING SUM(s.quantity) > 100 ORDER BY SUM(s.quantity) DESC"
                self.run_table_query(cursor, q, None, ["Product", "Stock Qty (Strips + Loose)"], show_total=False)
            elif report_name == "Fast Moving (Non-Stop)":
                self.run_table_query(cursor, "SELECT m.prod_name, COUNT(bi.item_id) as freq FROM Bill_Item bi JOIN Product_Details m ON bi.Prod_id = m.prod_id GROUP BY m.prod_id ORDER BY freq DESC LIMIT 50", None, ["Product", "Sales Frequency"])
            elif report_name == "Purchase Returns Details":
                q = "SELECT date(pr.return_date), pr.return_number, s.Sup_name, m.prod_name, pri.return_qty, pri.return_amount FROM Purchase_Return_Item pri JOIN Purchase_Return pr ON pri.return_id = pr.return_id JOIN Supplier s ON pr.supp_id = s.Supp_id JOIN Product_Details m ON pri.Prod_id = m.prod_id WHERE date(pr.return_date) BETWEEN ? AND ? ORDER BY pr.return_date DESC"
                self.run_table_query(cursor, q, (d_from, d_to), ["Return Date", "Debit Note #", "Supplier", "Returned Product", "Qty Returned", "Return Amount"])

            # === GRAPHS ===
            elif report_name == "Daily Sales Graph":
                self.plot_daily_sales(cursor, d_from, d_to)
            elif report_name == "Monthly Sales Graph":
                self.plot_monthly_sales(cursor, d_from[:4])

        except Exception as e:
            QMessageBox.critical(self, "Report Error", str(e))
        finally:
            conn.close()

    # ==========================================
    # --- FINANCIAL DASHBOARD LOGIC ---
    # ==========================================
    def populate_financial_dashboard(self, cursor, d_from, d_to):
        fd = self.fin_dash
        fd.tab_pl.setRowCount(0); fd.tab_cash.setRowCount(0)
        fd.tab_dues.setRowCount(0); fd.tab_stock.setRowCount(0)

        # --- 1. CORE DATA EXTRACTION (Selected Period) ---
        cursor.execute("SELECT SUM(total_sum), SUM(discount) FROM Bill WHERE date(bill_date) BETWEEN ? AND ?", (d_from, d_to))
        row = cursor.fetchone(); gross_sales = row[0] or 0; discounts = row[1] or 0
        
        cursor.execute("SELECT SUM(total_amount), SUM(amount_received) FROM Purchase_Return WHERE date(return_date) BETWEEN ? AND ?", (d_from, d_to))
        row = cursor.fetchone(); pr_returns = row[0] or 0; pr_cash_rcv = row[1] or 0

        cursor.execute("""
            SELECT SUM(bi.quantity * (SELECT AVG(s.purchase_rate) FROM Product_Stock s WHERE s.prod_id = bi.Prod_id)) 
            FROM Bill_Item bi JOIN Bill b ON bi.Bill_id = b.Bill_id WHERE date(b.bill_date) BETWEEN ? AND ?
        """, (d_from, d_to))
        cogs = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT SUM(bi.total_price - (bi.total_price / (1.0 + (p.gst / 100.0))))
            FROM Bill_Item bi JOIN Product_Details p ON bi.Prod_id = p.prod_id JOIN Bill b ON bi.Bill_id = b.Bill_id
            WHERE date(b.bill_date) BETWEEN ? AND ?
        """, (d_from, d_to))
        gst_collected = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT SUM(pii.total_amount - (pii.total_amount / (1.0 + (p.gst / 100.0))))
            FROM Purchase_Invoice_Item pii JOIN Product_Details p ON pii.Prod_id = p.prod_id JOIN Purchase_Invoice pi ON pii.invoice_id = pi.invoice_id
            WHERE date(pi.invoice_date) BETWEEN ? AND ?
        """, (d_from, d_to))
        gst_paid = cursor.fetchone()[0] or 0

        cursor.execute("SELECT exp_date, quantity, purchase_rate FROM Product_Stock")
        expired_loss = 0.0
        today = datetime.date.today()
        for exp, qty, rate in cursor.fetchall():
            try:
                if exp and "/" in exp:
                    m, y = map(int, exp.split('/'))
                    exp_dt = datetime.date(2000+y, m, 1)
                    if exp_dt < today: expired_loss += float(qty * rate)
            except: pass

        cursor.execute("SELECT expense_type, SUM(amount) FROM Expenses WHERE date(expense_date) BETWEEN ? AND ? GROUP BY expense_type", (d_from, d_to))
        expenses_data = cursor.fetchall()
        total_expenses = sum([e[1] for e in expenses_data])

        net_revenue = gross_sales 
        gross_profit = net_revenue - cogs
        net_profit = gross_profit - total_expenses - expired_loss + pr_returns

        # --- 2. TAB 1: PROFIT & LOSS POPULATION ---
        fd.add_row(fd.tab_pl, "REVENUE", "Income Generation", 0, "header")
        fd.add_row(fd.tab_pl, "Revenue", "   Total Gross Sales", gross_sales, "revenue")
        fd.add_row(fd.tab_pl, "Revenue", "   Less: Discounts Given", -discounts, "cost")
        fd.add_row(fd.tab_pl, "Revenue", "Net Revenue", net_revenue, "subtotal")
        
        fd.add_row(fd.tab_pl, "COGS", "Cost of Goods", 0, "header")
        fd.add_row(fd.tab_pl, "COGS", "   Product Purchase Costs (Sold items)", cogs, "cost")
        fd.add_row(fd.tab_pl, "Profit", "Gross Profit", gross_profit, "subtotal")
        
        fd.add_row(fd.tab_pl, "PHARMACY OPS", "Operational Adjustments", 0, "header")
        fd.add_row(fd.tab_pl, "Tax", "   GST Collected (Estimated)", gst_collected, "normal")
        fd.add_row(fd.tab_pl, "Tax", "   GST Paid (Estimated)", -gst_paid, "cost")
        fd.add_row(fd.tab_pl, "Loss", "   Expired Medicines Written Off", expired_loss, "cost")
        fd.add_row(fd.tab_pl, "Income", "   Supplier Purchase Returns", pr_returns, "revenue")

        fd.add_row(fd.tab_pl, "EXPENSES", "Operating Expenses", 0, "header")
        for e_type, e_amt in expenses_data:
            fd.add_row(fd.tab_pl, "Expense", f"   {e_type}", e_amt, "expense")
        fd.add_row(fd.tab_pl, "Expense", "Total Operating Expenses", total_expenses, "subtotal")
        
        fd.add_row(fd.tab_pl, "RESULT", "NET PROFIT / (LOSS)", net_profit, "profit")

        # --- 3. TAB 2: CASH FLOW ---
        cursor.execute("SELECT SUM(paid_amount) FROM Bill WHERE date(bill_date) BETWEEN ? AND ?", (d_from, d_to)); sales_cash_in = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(paid_amount) FROM Purchase_Invoice WHERE date(invoice_date) BETWEEN ? AND ?", (d_from, d_to)); purch_cash_out = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(paid_amount) FROM Bill"); all_time_sales_in = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount_received) FROM Purchase_Return"); all_time_ret_in = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(paid_amount) FROM Purchase_Invoice"); all_time_purch_out = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM Expenses"); all_time_exp_out = cursor.fetchone()[0] or 0
        
        total_cash_in = all_time_sales_in + all_time_ret_in
        total_cash_out = all_time_purch_out + all_time_exp_out
        cash_in_hand = total_cash_in - total_cash_out

        fd.add_row(fd.tab_cash, "PERIOD CASH IN", f"From {d_from} to {d_to}", 0, "header")
        fd.add_row(fd.tab_cash, "Inflow", "   Cash/Bank received from Sales", sales_cash_in, "revenue")
        fd.add_row(fd.tab_cash, "Inflow", "   Refunds received from Returns", pr_cash_rcv, "revenue")
        
        fd.add_row(fd.tab_cash, "PERIOD CASH OUT", f"From {d_from} to {d_to}", 0, "header")
        fd.add_row(fd.tab_cash, "Outflow", "   Payments made for Purchases", purch_cash_out, "expense")
        fd.add_row(fd.tab_cash, "Outflow", "   Payments made for Expenses", total_expenses, "expense")
        
        period_net_cash = (sales_cash_in + pr_cash_rcv) - (purch_cash_out + total_expenses)
        fd.add_row(fd.tab_cash, "NET", "Period Net Cash Flow", period_net_cash, "subtotal")

        fd.add_row(fd.tab_cash, "ALL TIME LIQUIDITY", "Lifetime Cash Position", 0, "header")
        fd.add_row(fd.tab_cash, "Lifetime", "Total Money Collected (Sales + Refunds)", total_cash_in, "revenue")
        fd.add_row(fd.tab_cash, "Lifetime", "Total Money Spent (Purchases + Expenses)", total_cash_out, "expense")
        fd.add_row(fd.tab_cash, "BALANCE", "CURRENT CASH IN HAND", cash_in_hand, "profit")

        # --- 4. TAB 3: RECEIVABLES & PAYABLES ---
        cursor.execute("SELECT SUM(balance) FROM Bill WHERE date(bill_date) BETWEEN ? AND ?", (d_from, d_to)); period_recv = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(balance) FROM Purchase_Invoice WHERE date(invoice_date) BETWEEN ? AND ?", (d_from, d_to)); period_pay = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(balance) FROM Customer"); all_recv = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(balance) FROM Supplier"); all_pay = cursor.fetchone()[0] or 0

        fd.add_row(fd.tab_dues, "RECEIVABLES (Asset)", "Money owed TO YOU", 0, "header")
        fd.add_row(fd.tab_dues, "Customers", "   Unpaid Customer Bills (Selected Period)", period_recv, "revenue")
        fd.add_row(fd.tab_dues, "Customers", "   TOTAL OUTSTANDING RECEIVABLES (All Time)", all_recv, "subtotal")
        
        fd.add_row(fd.tab_dues, "PAYABLES (Liability)", "Money YOU Owe", 0, "header")
        fd.add_row(fd.tab_dues, "Suppliers", "   Unpaid Supplier Invoices (Selected Period)", period_pay, "expense")
        fd.add_row(fd.tab_dues, "Suppliers", "   TOTAL OUTSTANDING PAYABLES (All Time)", all_pay, "subtotal")

        # --- 5. TAB 4: STOCK VALUATION ---
        cursor.execute("SELECT SUM(quantity * purchase_rate), SUM(quantity) FROM Product_Stock")
        row = cursor.fetchone()
        stock_val = row[0] or 0; stock_qty = row[1] or 0

        cursor.execute("""
            SELECT d.type, SUM(s.quantity * s.purchase_rate) 
            FROM Product_Stock s JOIN Product_Details d ON s.prod_id = d.prod_id GROUP BY d.type ORDER BY SUM(s.quantity * s.purchase_rate) DESC
        """)
        type_vals = cursor.fetchall()

        fd.add_row(fd.tab_stock, "OVERALL STOCK", "Current Inventory Snapshot", 0, "header")
        fd.add_row(fd.tab_stock, "Inventory", "   Total Units/Tabs in Pharmacy", stock_qty, "normal")
        fd.add_row(fd.tab_stock, "Inventory", "   TOTAL INVENTORY PURCHASE VALUE", stock_val, "subtotal")
        
        fd.add_row(fd.tab_stock, "CATEGORY VALUATION", "Capital locked in stock types", 0, "header")
        for t_name, t_val in type_vals:
            fd.add_row(fd.tab_stock, "Category", f"   {t_name}", t_val, "normal")

        # --- UPDATE CARDS ---
        margin_pct = (gross_profit / net_revenue * 100) if net_revenue > 0 else 0
        exp_pct = (total_expenses / net_revenue * 100) if net_revenue > 0 else 0
        
        fd.lbl_net_profit.setText(f"₹{net_profit:,.2f}")
        fd.lbl_net_profit.setStyleSheet(f"color: {C_PROFIT if net_profit>=0 else C_LOSS}; font-size: 18px; font-weight: bold; border: none;")
        
        fd.lbl_margin.setText(f"{margin_pct:.1f}%")
        fd.lbl_exp_ratio.setText(f"{exp_pct:.1f}%")
        fd.lbl_receivables.setText(f"₹{all_recv:,.2f}")
        fd.lbl_cash.setText(f"₹{cash_in_hand:,.2f}")

    # ==========================================
    # --- TABLE HELPERS ---
    # ==========================================
    def run_table_query(self, cursor, query, params, headers, show_total=True):
        if params: cursor.execute(query, params)
        else: cursor.execute(query)
        self.populate_table(headers, cursor.fetchall(), show_total=show_total)

    def populate_table(self, headers, rows, show_total=True):
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(0)
        
        col_sums = [0.0] * len(headers)
        is_num = [False] * len(headers)
        keywords = ['amount', 'total', 'revenue', 'spent', 'qty', 'purchased']

        for i, row in enumerate(rows):
            self.table.insertRow(i)
            
            # Check if this is a header/divider row in the P&L array
            is_divider = False
            if len(row) > 0 and str(row[0]).startswith("---"):
                is_divider = True

            # Check if this is the final "Total Amount I Have" row
            is_final_total = False
            if len(row) > 0 and str(row[0]) == "THE BOTTOM LINE":
                is_final_total = True

            for j, val in enumerate(row):
                # --- FIX: Format floating point numbers to max 2 decimal places ---
                if isinstance(val, float):
                    val = round(val, 2)  # Safely rounds the internal float
                # ------------------------------------------------------------------
                
                str_val = str(val) if val is not None else ""
                item = QTableWidgetItem(str_val)
                
                # Apply styling for dividers and total rows
                if is_divider:
                    font_bold = QFont()
                    font_bold.setBold(True)
                    item.setFont(font_bold)
                    item.setBackground(QBrush(QColor("#e9ecef")))
                elif is_final_total:
                    item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
                    item.setBackground(QBrush(QColor(COLOR_HIGHLIGHT)))
                
                if str_val.replace('.', '', 1).isdigit() or "₹" in str_val:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    c_val = str_val.replace('₹', '').replace(',', '').replace('(', '-').replace(')', '').strip()
                    try:
                        col_sums[j] += float(c_val)
                        is_num[j] = True
                    except: pass
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(i, j, item)
        
        if rows and show_total:
            fb = QFont(); fb.setBold(True); fb.setPointSize(10)
            r = self.table.rowCount()
            self.table.insertRow(r)
            
            for j, h in enumerate(headers):
                if j == 0:
                    it = QTableWidgetItem("TOTAL :")
                    it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                elif any(k in h.lower() for k in keywords) and is_num[j]:
                    it = QTableWidgetItem(f"₹ {col_sums[j]:,.2f}" if "₹" in str(rows[0][j]) or 'amount' in h.lower() else f"{col_sums[j]:.2f}")
                    it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    it = QTableWidgetItem("")
                it.setFont(fb); it.setBackground(QBrush(QColor(COLOR_TOTAL_ROW)))
                self.table.setItem(r, j, it)

        hdr = self.table.horizontalHeader()
        for i, h in enumerate(headers):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch if any(x in h.lower() for x in ['name', 'item', 'description', 'patient', 'doctor', 'product', 'supplier', 'category']) else QHeaderView.ResizeMode.ResizeToContents)

    # ==========================================
    # --- GRAPHS ---
    # ==========================================
    def plot_daily_sales(self, cursor, d_from, d_to):
        self.canvas.axes.clear()
        self.canvas.figure.patch.set_facecolor(COLOR_WHITE)
        self.canvas.axes.set_facecolor(COLOR_WHITE)
        
        cursor.execute("SELECT date(bill_date), SUM(total_sum) FROM Bill WHERE date(bill_date) BETWEEN ? AND ? GROUP BY date(bill_date) ORDER BY date(bill_date)", (d_from, d_to))
        rows = cursor.fetchall()
        
        if not rows:
            self.canvas.axes.text(0.5, 0.5, "No Data Available in this date range", ha='center', va='center', fontsize=12, color='#6c757d')
            self.canvas.draw()
            return

        dates = [datetime.datetime.strptime(r[0], "%Y-%m-%d").date() for r in rows]
        values = [r[1] for r in rows]
        
        self.canvas.axes.plot(dates, values, marker='o', linestyle='-', color='#2563eb', linewidth=3, markersize=7, markerfacecolor='white', markeredgewidth=2)
        self.canvas.axes.fill_between(dates, values, color='#bfdbfe', alpha=0.4) 
        
        self.canvas.axes.set_title("Daily Sales Trend", fontsize=15, fontweight='bold', color='#1f2937', pad=20)
        self.canvas.axes.tick_params(axis='x', colors='#4b5563', labelsize=9)
        self.canvas.axes.tick_params(axis='y', colors='#4b5563', labelsize=9, length=0)
        self.canvas.axes.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        self.canvas.figure.autofmt_xdate(rotation=30)
        self.canvas.axes.yaxis.set_major_formatter(ticker.StrMethodFormatter('₹ {x:,.0f}'))
        
        self.canvas.axes.grid(axis='y', linestyle='-', alpha=0.3, color='#9ca3af')
        for s in ['top', 'right', 'left']: self.canvas.axes.spines[s].set_visible(False)
        self.canvas.axes.spines['bottom'].set_color('#d1d5db')
        
        if len(dates) <= 15:
            m_val = max(values) if values else 1
            for x, y in zip(dates, values):
                self.canvas.axes.text(x, y + (m_val*0.03), f"₹{int(y):,}", ha='center', va='bottom', fontsize=9, color='#2563eb', fontweight='bold')
            
        self.canvas.figure.tight_layout(); self.canvas.draw()

    def plot_monthly_sales(self, cursor, year):
        self.canvas.axes.clear()
        self.canvas.figure.patch.set_facecolor(COLOR_WHITE)
        self.canvas.axes.set_facecolor(COLOR_WHITE)
        
        cursor.execute("SELECT strftime('%m', bill_date), SUM(total_sum) FROM Bill WHERE strftime('%Y', bill_date) = ? GROUP BY strftime('%m', bill_date)", (year,))
        data = {int(r[0]): r[1] for r in cursor.fetchall()}
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        values = [data.get(i+1, 0) for i in range(12)]
        
        bars = self.canvas.axes.bar(months, values, color='#10b981', alpha=0.9, width=0.55)
        
        self.canvas.axes.set_title(f"Monthly Revenue - {year}", fontsize=15, fontweight='bold', color='#1f2937', pad=20)
        self.canvas.axes.tick_params(axis='x', colors='#4b5563', labelsize=10)
        self.canvas.axes.tick_params(axis='y', colors='#4b5563', labelsize=9, length=0)
        self.canvas.axes.yaxis.set_major_formatter(ticker.StrMethodFormatter('₹ {x:,.0f}'))

        self.canvas.axes.grid(axis='y', linestyle='-', alpha=0.3, color='#9ca3af')
        for s in ['top', 'right', 'left']: self.canvas.axes.spines[s].set_visible(False)
        self.canvas.axes.spines['bottom'].set_color('#d1d5db')
        
        m_val = max(values) if values else 1
        for bar in bars:
            h = bar.get_height()
            if h > 0: self.canvas.axes.text(bar.get_x() + bar.get_width()/2, h + (m_val*0.015), f"₹{int(h):,}", ha='center', va='bottom', fontsize=9, color='#047857', fontweight='bold')
                                      
        self.canvas.figure.tight_layout(); self.canvas.draw()

# --- FIXED MplCanvas CLASS ---
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.updateGeometry()

if __name__ == "__main__":
    app = sys.modules['__main__'].QApplication(sys.argv)
    w = ReportsInterface(); w.show(); sys.exit(app.exec())