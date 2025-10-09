from django.db import models
from bikeshop.models import GameSession
from django.core.validators import MinValueValidator, MaxValueValidator


class Credit(models.Model):
    """Kredit"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    credit_type = models.CharField(max_length=20, choices=[
        ('instant', 'Sofortkredit'),
        ('short', 'Kurzfristig'),
        ('medium', 'Mittelfristig'),
        ('long', 'Langfristig')
    ])
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.FloatField()  # Zinssatz in %
    duration_months = models.IntegerField()
    remaining_months = models.IntegerField()
    monthly_payment = models.DecimalField(max_digits=8, decimal_places=2)
    taken_month = models.IntegerField()
    taken_year = models.IntegerField()
    is_active = models.BooleanField(default=True)


class Transaction(models.Model):
    """Transaktion für Finanzen"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=[
        ('income', 'Einnahme'),
        ('expense', 'Ausgabe')
    ])
    category = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    month = models.IntegerField()
    year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class MonthlyReport(models.Model):
    """Monatsbericht"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2)
    total_income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Production data
    bikes_produced_count = models.IntegerField(default=0)
    total_production_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    production_summary = models.JSONField(default=dict, blank=True)  # {'bike_type': {'count': 5, 'cost': 1000}}
    
    # Sales data  
    bikes_sold_count = models.IntegerField(default=0)
    total_sales_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sales_summary = models.JSONField(default=dict, blank=True)  # {'bike_type': {'count': 3, 'revenue': 1500}}
    
    # Procurement data
    total_procurement_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    procurement_summary = models.JSONField(default=dict, blank=True)  # {'component': {'quantity': 10, 'cost': 500}}
    
    # Profit/Loss calculation
    profit_loss = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Report data (serialized for detailed breakdown)
    detailed_transactions = models.JSONField(default=list, blank=True)  # Top transactions
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ['session', 'month', 'year']


class ProfitLossStatement(models.Model):
    """Comprehensive Profit & Loss Statement"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    
    # Revenue
    gross_sales_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    returns_and_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_sales_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Cost of Goods Sold
    beginning_inventory = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    purchases = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    direct_labor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    manufacturing_overhead = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ending_inventory = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cost_of_goods_sold = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Gross Profit
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit_margin = models.FloatField(default=0.0)  # Percentage
    
    # Operating Expenses
    salaries_and_wages = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rent_and_utilities = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    marketing_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    research_development = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    administrative_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_operating_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_operating_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Operating Income
    operating_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    operating_margin = models.FloatField(default=0.0)  # Percentage
    
    # Non-Operating Items
    interest_income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    interest_expense = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Net Income
    income_before_taxes = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    taxes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_profit_margin = models.FloatField(default=0.0)  # Percentage
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['session', 'month', 'year']


class CashFlowStatement(models.Model):
    """Cash Flow Statement"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    
    # Operating Activities
    net_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    depreciation = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    accounts_receivable_change = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    inventory_change = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    accounts_payable_change = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_working_capital_changes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cash_from_operations = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Investing Activities
    equipment_purchases = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    facility_investments = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    research_investments = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_investments = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cash_from_investing = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Financing Activities
    loan_proceeds = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    loan_payments = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    owner_contributions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    owner_withdrawals = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cash_from_financing = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Net Change in Cash
    net_change_in_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    beginning_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ending_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['session', 'month', 'year']


class BalanceSheet(models.Model):
    """Balance Sheet"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    
    # Current Assets
    cash_and_equivalents = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    accounts_receivable = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    inventory_raw_materials = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    inventory_finished_goods = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prepaid_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_current_assets = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_current_assets = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Fixed Assets
    land_and_buildings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    machinery_and_equipment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    accumulated_depreciation = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_fixed_assets = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Other Assets
    intangible_assets = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    investments = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_assets = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_other_assets = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Total Assets
    total_assets = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Current Liabilities
    accounts_payable = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    short_term_debt = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    accrued_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxes_payable = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_current_liabilities = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_current_liabilities = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Long-term Liabilities
    long_term_debt = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_long_term_liabilities = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_long_term_liabilities = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Total Liabilities
    total_liabilities = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Equity
    owner_equity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    retained_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_equity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Total Liabilities and Equity
    total_liabilities_and_equity = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['session', 'month', 'year']


class LiquidityAnalysis(models.Model):
    """Liquidity Analysis and Financial Ratios"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    
    # Liquidity Ratios
    current_ratio = models.FloatField(default=0.0)  # Current Assets / Current Liabilities
    quick_ratio = models.FloatField(default=0.0)    # (Current Assets - Inventory) / Current Liabilities
    cash_ratio = models.FloatField(default=0.0)     # Cash / Current Liabilities
    
    # Working Capital
    working_capital = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    working_capital_ratio = models.FloatField(default=0.0)
    
    # Cash Management
    days_sales_outstanding = models.FloatField(default=0.0)  # DSO
    days_inventory_outstanding = models.FloatField(default=0.0)  # DIO
    days_payable_outstanding = models.FloatField(default=0.0)  # DPO
    cash_conversion_cycle = models.FloatField(default=0.0)  # DSO + DIO - DPO
    
    # Debt Ratios
    debt_to_equity = models.FloatField(default=0.0)
    debt_to_assets = models.FloatField(default=0.0)
    times_interest_earned = models.FloatField(default=0.0)
    
    # Profitability Ratios
    return_on_assets = models.FloatField(default=0.0)  # ROA
    return_on_equity = models.FloatField(default=0.0)  # ROE
    
    # Efficiency Ratios
    asset_turnover = models.FloatField(default=0.0)
    inventory_turnover = models.FloatField(default=0.0)
    
    # Status Indicators
    liquidity_status = models.CharField(max_length=20, choices=[
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('adequate', 'Adequate'),
        ('poor', 'Poor'),
        ('critical', 'Critical')
    ], default='adequate')
    
    cash_runway_months = models.FloatField(default=0.0)  # Months of operation with current cash
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['session', 'month', 'year']


class SalesReport(models.Model):
    """Detailed Sales Report"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    
    # Overall Sales Performance
    total_units_sold = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_selling_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Sales by Product Line (JSON for flexibility)
    product_line_breakdown = models.JSONField(default=dict, blank=True)
    # Format: {'bike_type': {'units': 10, 'revenue': 5000, 'avg_price': 500}}
    
    # Sales by Customer Segment
    segment_breakdown = models.JSONField(default=dict, blank=True)
    # Format: {'cheap': {'units': 5, 'revenue': 1000}, 'premium': {'units': 3, 'revenue': 2000}}
    
    # Regional Performance
    regional_breakdown = models.JSONField(default=dict, blank=True)
    # Format: {'market_name': {'units': 8, 'revenue': 3000, 'market_share': 15.5}}
    
    # Market Analysis
    market_share_total = models.FloatField(default=0.0)  # Overall market share percentage
    market_growth_rate = models.FloatField(default=0.0)  # Market growth vs previous period
    competitive_position = models.JSONField(default=dict, blank=True)
    # Format: {'rank': 2, 'share_change': +2.5, 'top_competitor': 'CompanyX'}
    
    # Performance Metrics
    revenue_growth_rate = models.FloatField(default=0.0)  # vs previous month
    units_growth_rate = models.FloatField(default=0.0)   # vs previous month
    price_realization_rate = models.FloatField(default=0.0)  # Actual vs target prices
    
    # Customer Analytics
    new_customers_acquired = models.IntegerField(default=0)
    customer_retention_rate = models.FloatField(default=0.0)
    average_order_value = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Inventory Impact
    inventory_turnover_rate = models.FloatField(default=0.0)
    stockout_incidents = models.IntegerField(default=0)
    excess_inventory_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['session', 'month', 'year']