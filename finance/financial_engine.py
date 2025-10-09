from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Q, Count
from .models import (
    Transaction, Credit, MonthlyReport, ProfitLossStatement, 
    CashFlowStatement, BalanceSheet, LiquidityAnalysis, SalesReport
)
from bikeshop.models import GameSession
from production.models import ProducedBike
from sales.models import SalesOrder
from warehouse.models import ComponentStock
from procurement.models import ProcurementOrder
from business_strategy.models import MarketingCampaign, ResearchProject, SustainabilityInitiative


class FinancialReportingEngine:
    """Engine for generating comprehensive financial reports"""
    
    def __init__(self, session):
        self.session = session
    
    def generate_monthly_settlement(self):
        """Generate complete monthly financial settlement"""
        with transaction.atomic():
            # Generate all financial reports for the current month
            self.generate_profit_loss_statement()
            self.generate_cash_flow_statement()
            self.generate_balance_sheet()
            self.generate_liquidity_analysis()
            self.generate_sales_report()
            self.update_monthly_report()
    
    def generate_profit_loss_statement(self):
        """Generate comprehensive P&L statement"""
        month = self.session.current_month
        year = self.session.current_year
        
        # Get or create P&L statement
        pnl, created = ProfitLossStatement.objects.get_or_create(
            session=self.session,
            month=month,
            year=year
        )
        
        # Calculate Revenue
        sales_revenue = self._calculate_sales_revenue(month, year)
        pnl.gross_sales_revenue = sales_revenue
        pnl.returns_and_allowances = Decimal('0')  # Not implemented yet
        pnl.net_sales_revenue = pnl.gross_sales_revenue - pnl.returns_and_allowances
        
        # Calculate Cost of Goods Sold
        pnl.beginning_inventory = self._calculate_beginning_inventory(month, year)
        pnl.purchases = self._calculate_purchases(month, year)
        pnl.direct_labor = self._calculate_direct_labor(month, year)
        pnl.manufacturing_overhead = self._calculate_manufacturing_overhead(month, year)
        pnl.ending_inventory = self._calculate_ending_inventory(month, year)
        
        pnl.cost_of_goods_sold = (
            pnl.beginning_inventory + pnl.purchases + 
            pnl.direct_labor + pnl.manufacturing_overhead - pnl.ending_inventory
        )
        
        # Calculate Gross Profit
        pnl.gross_profit = pnl.net_sales_revenue - pnl.cost_of_goods_sold
        pnl.gross_profit_margin = (
            float(pnl.gross_profit / pnl.net_sales_revenue * 100) 
            if pnl.net_sales_revenue > 0 else 0.0
        )
        
        # Calculate Operating Expenses
        pnl.salaries_and_wages = self._calculate_salaries(month, year)
        pnl.rent_and_utilities = self._calculate_rent_utilities(month, year)
        pnl.marketing_expenses = self._calculate_marketing_expenses(month, year)
        pnl.research_development = self._calculate_rd_expenses(month, year)
        pnl.administrative_expenses = self._calculate_admin_expenses(month, year)
        pnl.other_operating_expenses = self._calculate_other_expenses(month, year)
        
        pnl.total_operating_expenses = (
            pnl.salaries_and_wages + pnl.rent_and_utilities + 
            pnl.marketing_expenses + pnl.research_development +
            pnl.administrative_expenses + pnl.other_operating_expenses
        )
        
        # Calculate Operating Income
        pnl.operating_income = pnl.gross_profit - pnl.total_operating_expenses
        pnl.operating_margin = (
            float(pnl.operating_income / pnl.net_sales_revenue * 100)
            if pnl.net_sales_revenue > 0 else 0.0
        )
        
        # Calculate Non-Operating Items
        pnl.interest_income = self._calculate_interest_income(month, year)
        pnl.interest_expense = self._calculate_interest_expense(month, year)
        pnl.other_income = self._calculate_other_income(month, year)
        pnl.other_expenses = self._calculate_other_expenses_nonop(month, year)
        
        # Calculate Net Income
        pnl.income_before_taxes = (
            pnl.operating_income + pnl.interest_income + pnl.other_income -
            pnl.interest_expense - pnl.other_expenses
        )
        pnl.taxes = pnl.income_before_taxes * Decimal('0.25')  # 25% tax rate
        pnl.net_income = pnl.income_before_taxes - pnl.taxes
        pnl.net_profit_margin = (
            float(pnl.net_income / pnl.net_sales_revenue * 100)
            if pnl.net_sales_revenue > 0 else 0.0
        )
        
        pnl.save()
        return pnl
    
    def generate_cash_flow_statement(self):
        """Generate cash flow statement"""
        month = self.session.current_month
        year = self.session.current_year
        
        # Get or create cash flow statement
        cf, created = CashFlowStatement.objects.get_or_create(
            session=self.session,
            month=month,
            year=year
        )
        
        # Get P&L for net income
        try:
            pnl = ProfitLossStatement.objects.get(
                session=self.session, month=month, year=year
            )
            cf.net_income = pnl.net_income
        except ProfitLossStatement.DoesNotExist:
            cf.net_income = Decimal('0')
        
        # Operating Activities
        cf.depreciation = self._calculate_depreciation(month, year)
        cf.accounts_receivable_change = self._calculate_ar_change(month, year)
        cf.inventory_change = self._calculate_inventory_change(month, year)
        cf.accounts_payable_change = self._calculate_ap_change(month, year)
        cf.other_working_capital_changes = Decimal('0')
        
        cf.cash_from_operations = (
            cf.net_income + cf.depreciation - cf.accounts_receivable_change -
            cf.inventory_change + cf.accounts_payable_change + cf.other_working_capital_changes
        )
        
        # Investing Activities
        cf.equipment_purchases = self._calculate_equipment_purchases(month, year)
        cf.facility_investments = self._calculate_facility_investments(month, year)
        cf.research_investments = self._calculate_research_investments(month, year)
        cf.other_investments = Decimal('0')
        
        cf.cash_from_investing = -(
            cf.equipment_purchases + cf.facility_investments + 
            cf.research_investments + cf.other_investments
        )
        
        # Financing Activities
        cf.loan_proceeds = self._calculate_loan_proceeds(month, year)
        cf.loan_payments = self._calculate_loan_payments(month, year)
        cf.owner_contributions = Decimal('0')
        cf.owner_withdrawals = Decimal('0')
        
        cf.cash_from_financing = (
            cf.loan_proceeds - cf.loan_payments + 
            cf.owner_contributions - cf.owner_withdrawals
        )
        
        # Net Change in Cash
        cf.net_change_in_cash = (
            cf.cash_from_operations + cf.cash_from_investing + cf.cash_from_financing
        )
        
        # Get previous month's ending cash
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        
        try:
            prev_cf = CashFlowStatement.objects.get(
                session=self.session, month=prev_month, year=prev_year
            )
            cf.beginning_cash = prev_cf.ending_cash
        except CashFlowStatement.DoesNotExist:
            cf.beginning_cash = Decimal(self.session.balance)
        
        cf.ending_cash = cf.beginning_cash + cf.net_change_in_cash
        
        cf.save()
        return cf
    
    def generate_balance_sheet(self):
        """Generate balance sheet"""
        month = self.session.current_month
        year = self.session.current_year
        
        # Get or create balance sheet
        bs, created = BalanceSheet.objects.get_or_create(
            session=self.session,
            month=month,
            year=year
        )
        
        # Current Assets
        bs.cash_and_equivalents = Decimal(self.session.balance)
        bs.accounts_receivable = self._calculate_accounts_receivable()
        bs.inventory_raw_materials = self._calculate_raw_materials_inventory()
        bs.inventory_finished_goods = self._calculate_finished_goods_inventory()
        bs.prepaid_expenses = self._calculate_prepaid_expenses()
        bs.other_current_assets = Decimal('0')
        
        bs.total_current_assets = (
            bs.cash_and_equivalents + bs.accounts_receivable +
            bs.inventory_raw_materials + bs.inventory_finished_goods +
            bs.prepaid_expenses + bs.other_current_assets
        )
        
        # Fixed Assets
        bs.land_and_buildings = self._calculate_land_buildings()
        bs.machinery_and_equipment = self._calculate_machinery_equipment()
        bs.accumulated_depreciation = self._calculate_accumulated_depreciation()
        bs.net_fixed_assets = (
            bs.land_and_buildings + bs.machinery_and_equipment - bs.accumulated_depreciation
        )
        
        # Other Assets
        bs.intangible_assets = self._calculate_intangible_assets()
        bs.investments = self._calculate_investments()
        bs.other_assets = Decimal('0')
        bs.total_other_assets = bs.intangible_assets + bs.investments + bs.other_assets
        
        # Total Assets
        bs.total_assets = bs.total_current_assets + bs.net_fixed_assets + bs.total_other_assets
        
        # Current Liabilities
        bs.accounts_payable = self._calculate_accounts_payable()
        bs.short_term_debt = self._calculate_short_term_debt()
        bs.accrued_expenses = self._calculate_accrued_expenses()
        bs.taxes_payable = self._calculate_taxes_payable()
        bs.other_current_liabilities = Decimal('0')
        
        bs.total_current_liabilities = (
            bs.accounts_payable + bs.short_term_debt + bs.accrued_expenses +
            bs.taxes_payable + bs.other_current_liabilities
        )
        
        # Long-term Liabilities
        bs.long_term_debt = self._calculate_long_term_debt()
        bs.other_long_term_liabilities = Decimal('0')
        bs.total_long_term_liabilities = bs.long_term_debt + bs.other_long_term_liabilities
        
        # Total Liabilities
        bs.total_liabilities = bs.total_current_liabilities + bs.total_long_term_liabilities
        
        # Equity
        bs.owner_equity = Decimal('50000')  # Initial investment
        bs.retained_earnings = self._calculate_retained_earnings()
        bs.total_equity = bs.owner_equity + bs.retained_earnings
        
        # Total Liabilities and Equity
        bs.total_liabilities_and_equity = bs.total_liabilities + bs.total_equity
        
        bs.save()
        return bs
    
    def generate_liquidity_analysis(self):
        """Generate liquidity analysis and financial ratios"""
        month = self.session.current_month
        year = self.session.current_year
        
        # Get or create liquidity analysis
        la, created = LiquidityAnalysis.objects.get_or_create(
            session=self.session,
            month=month,
            year=year
        )
        
        # Get balance sheet data
        try:
            bs = BalanceSheet.objects.get(
                session=self.session, month=month, year=year
            )
        except BalanceSheet.DoesNotExist:
            bs = self.generate_balance_sheet()
        
        # Liquidity Ratios
        if bs.total_current_liabilities > 0:
            la.current_ratio = float(bs.total_current_assets / bs.total_current_liabilities)
            
            quick_assets = (
                bs.cash_and_equivalents + bs.accounts_receivable + bs.other_current_assets
            )
            la.quick_ratio = float(quick_assets / bs.total_current_liabilities)
            la.cash_ratio = float(bs.cash_and_equivalents / bs.total_current_liabilities)
        else:
            la.current_ratio = 999.99  # Infinite ratio
            la.quick_ratio = 999.99
            la.cash_ratio = 999.99
        
        # Working Capital
        la.working_capital = bs.total_current_assets - bs.total_current_liabilities
        la.working_capital_ratio = (
            float(la.working_capital / bs.total_current_assets)
            if bs.total_current_assets > 0 else 0.0
        )
        
        # Cash Management (simplified calculations)
        la.days_sales_outstanding = 30.0  # Simplified
        la.days_inventory_outstanding = 45.0  # Simplified
        la.days_payable_outstanding = 30.0  # Simplified
        la.cash_conversion_cycle = (
            la.days_sales_outstanding + la.days_inventory_outstanding - la.days_payable_outstanding
        )
        
        # Debt Ratios
        if bs.total_equity > 0:
            la.debt_to_equity = float(bs.total_liabilities / bs.total_equity)
        else:
            la.debt_to_equity = 999.99
        
        if bs.total_assets > 0:
            la.debt_to_assets = float(bs.total_liabilities / bs.total_assets)
        else:
            la.debt_to_assets = 0.0
        
        # Get P&L for profitability ratios
        try:
            pnl = ProfitLossStatement.objects.get(
                session=self.session, month=month, year=year
            )
            
            if pnl.interest_expense > 0:
                la.times_interest_earned = float(pnl.operating_income / pnl.interest_expense)
            else:
                la.times_interest_earned = 999.99
            
            # Profitability Ratios (annualized)
            annual_net_income = pnl.net_income * 12
            if bs.total_assets > 0:
                la.return_on_assets = float(annual_net_income / bs.total_assets * 100)
            if bs.total_equity > 0:
                la.return_on_equity = float(annual_net_income / bs.total_equity * 100)
            
            # Efficiency Ratios
            annual_revenue = pnl.net_sales_revenue * 12
            if bs.total_assets > 0:
                la.asset_turnover = float(annual_revenue / bs.total_assets)
            
            total_inventory = bs.inventory_raw_materials + bs.inventory_finished_goods
            if total_inventory > 0:
                la.inventory_turnover = float(pnl.cost_of_goods_sold * 12 / total_inventory)
            
        except ProfitLossStatement.DoesNotExist:
            la.times_interest_earned = 0.0
            la.return_on_assets = 0.0
            la.return_on_equity = 0.0
            la.asset_turnover = 0.0
            la.inventory_turnover = 0.0
        
        # Determine liquidity status
        if la.current_ratio >= 2.0 and la.quick_ratio >= 1.0:
            la.liquidity_status = 'excellent'
        elif la.current_ratio >= 1.5 and la.quick_ratio >= 0.8:
            la.liquidity_status = 'good'
        elif la.current_ratio >= 1.0 and la.quick_ratio >= 0.5:
            la.liquidity_status = 'adequate'
        elif la.current_ratio >= 0.7:
            la.liquidity_status = 'poor'
        else:
            la.liquidity_status = 'critical'
        
        # Calculate cash runway
        monthly_expenses = self._calculate_monthly_operating_expenses()
        if monthly_expenses > 0:
            la.cash_runway_months = float(bs.cash_and_equivalents / monthly_expenses)
        else:
            la.cash_runway_months = 999.99
        
        la.save()
        return la
    
    def generate_sales_report(self):
        """Generate detailed sales report"""
        month = self.session.current_month
        year = self.session.current_year
        
        # Get or create sales report
        sr, created = SalesReport.objects.get_or_create(
            session=self.session,
            month=month,
            year=year
        )
        
        # Get sales data for this month
        sales_orders = SalesOrder.objects.filter(
            session=self.session,
            sale_month=month,
            sale_year=year
        )
        
        # Overall Sales Performance
        sr.total_units_sold = sales_orders.count()  # Each order is one bike
        
        sr.total_revenue = sales_orders.aggregate(
            total=Sum('sale_price')
        )['total'] or Decimal('0')
        
        if sr.total_units_sold > 0:
            sr.average_selling_price = sr.total_revenue / sr.total_units_sold
        else:
            sr.average_selling_price = Decimal('0')
        
        # Sales by Product Line
        product_breakdown = {}
        for order in sales_orders:
            bike_type = order.bike.bike_type.name if order.bike else 'Unknown'
            if bike_type not in product_breakdown:
                product_breakdown[bike_type] = {
                    'units': 0,
                    'revenue': 0,
                    'avg_price': 0
                }
            
            product_breakdown[bike_type]['units'] += 1
            product_breakdown[bike_type]['revenue'] += float(order.sale_price)
        
        # Calculate average prices
        for bike_type, data in product_breakdown.items():
            if data['units'] > 0:
                data['avg_price'] = data['revenue'] / data['units']
        
        sr.product_line_breakdown = product_breakdown
        
        # Sales by Customer Segment
        segment_breakdown = {}
        for order in sales_orders:
            segment = order.market.name if order.market else 'Unknown'
            if segment not in segment_breakdown:
                segment_breakdown[segment] = {
                    'units': 0,
                    'revenue': 0
                }
            
            segment_breakdown[segment]['units'] += 1
            segment_breakdown[segment]['revenue'] += float(order.sale_price)
        
        sr.segment_breakdown = segment_breakdown
        
        # Regional Performance
        regional_breakdown = {}
        for order in sales_orders:
            market = order.market.name if order.market else 'Unknown'
            if market not in regional_breakdown:
                regional_breakdown[market] = {
                    'units': 0,
                    'revenue': 0,
                    'market_share': 0.0
                }
            
            regional_breakdown[market]['units'] += 1
            regional_breakdown[market]['revenue'] += float(order.sale_price)
            # Market share calculation would need market data
            regional_breakdown[market]['market_share'] = 15.0  # Placeholder
        
        sr.regional_breakdown = regional_breakdown
        
        # Performance Metrics (vs previous month)
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        
        try:
            prev_report = SalesReport.objects.get(
                session=self.session, month=prev_month, year=prev_year
            )
            
            if prev_report.total_revenue > 0:
                sr.revenue_growth_rate = float(
                    (sr.total_revenue - prev_report.total_revenue) / 
                    prev_report.total_revenue * 100
                )
            
            if prev_report.total_units_sold > 0:
                sr.units_growth_rate = float(
                    (sr.total_units_sold - prev_report.total_units_sold) / 
                    prev_report.total_units_sold * 100
                )
                
        except SalesReport.DoesNotExist:
            sr.revenue_growth_rate = 0.0
            sr.units_growth_rate = 0.0
        
        # Market Analysis (simplified)
        sr.market_share_total = 15.0  # Placeholder
        sr.market_growth_rate = 5.0   # Placeholder
        sr.competitive_position = {
            'rank': 2,
            'share_change': 1.5,
            'top_competitor': 'CompetitorA'
        }
        
        # Customer Analytics (simplified)
        sr.new_customers_acquired = max(1, sr.total_units_sold // 10)
        sr.customer_retention_rate = 85.0
        sr.average_order_value = sr.average_selling_price
        
        # Inventory Impact
        sr.inventory_turnover_rate = 6.0  # Placeholder
        sr.stockout_incidents = 0
        sr.excess_inventory_value = Decimal('0')
        
        # Price realization
        sr.price_realization_rate = 95.0  # Placeholder
        
        sr.save()
        return sr
    
    def update_monthly_report(self):
        """Update the existing monthly report with comprehensive data"""
        month = self.session.current_month
        year = self.session.current_year
        
        try:
            report = MonthlyReport.objects.get(
                session=self.session, month=month, year=year
            )
        except MonthlyReport.DoesNotExist:
            return None
        
        # Update with P&L data
        try:
            pnl = ProfitLossStatement.objects.get(
                session=self.session, month=month, year=year
            )
            report.total_income = pnl.net_sales_revenue
            report.total_expenses = pnl.total_operating_expenses
            report.profit_loss = pnl.net_income
        except ProfitLossStatement.DoesNotExist:
            pass
        
        # Update with sales data
        try:
            sales_report = SalesReport.objects.get(
                session=self.session, month=month, year=year
            )
            report.bikes_sold_count = sales_report.total_units_sold
            report.total_sales_revenue = sales_report.total_revenue
        except SalesReport.DoesNotExist:
            pass
        
        report.save()
        return report
    
    # Helper methods for calculations
    def _calculate_sales_revenue(self, month, year):
        """Calculate total sales revenue for the month"""
        return SalesOrder.objects.filter(
            session=self.session, sale_month=month, sale_year=year
        ).aggregate(total=Sum('sale_price'))['total'] or Decimal('0')
    
    def _calculate_beginning_inventory(self, month, year):
        """Calculate beginning inventory value"""
        # Simplified - would need to track inventory values over time
        return Decimal('10000')
    
    def _calculate_purchases(self, month, year):
        """Calculate purchases for the month"""
        return ProcurementOrder.objects.filter(
            session=self.session, month=month, year=year
        ).aggregate(total=Sum('total_cost'))['total'] or Decimal('0')
    
    def _calculate_direct_labor(self, month, year):
        """Calculate direct labor costs"""
        return Transaction.objects.filter(
            session=self.session,
            month=month,
            year=year,
            category='Löhne'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    def _calculate_manufacturing_overhead(self, month, year):
        """Calculate manufacturing overhead"""
        return Transaction.objects.filter(
            session=self.session,
            month=month,
            year=year,
            category__in=['Miete', 'Utilities', 'Factory Overhead']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    def _calculate_ending_inventory(self, month, year):
        """Calculate ending inventory value"""
        raw_materials = self._calculate_raw_materials_inventory()
        finished_goods = self._calculate_finished_goods_inventory()
        return raw_materials + finished_goods
    
    def _calculate_salaries(self, month, year):
        """Calculate salary expenses"""
        return Transaction.objects.filter(
            session=self.session,
            month=month,
            year=year,
            category='Löhne'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    def _calculate_rent_utilities(self, month, year):
        """Calculate rent and utilities"""
        return Transaction.objects.filter(
            session=self.session,
            month=month,
            year=year,
            category='Miete'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    def _calculate_marketing_expenses(self, month, year):
        """Calculate marketing expenses"""
        # Include business strategy marketing costs
        marketing_total = Decimal('0')
        
        # Add transaction-based marketing costs
        transaction_marketing = Transaction.objects.filter(
            session=self.session,
            month=month,
            year=year,
            category__icontains='Marketing'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        marketing_total += transaction_marketing
        
        # Add business strategy marketing campaigns
        try:
            from business_strategy.models import MarketingCampaign
            campaigns = MarketingCampaign.objects.filter(
                session=self.session,
                status='active',
                start_month__lte=month,
                start_year__lte=year
            )
            for campaign in campaigns:
                if campaign.months_remaining > 0:
                    marketing_total += campaign.monthly_spend
        except ImportError:
            pass
        
        return marketing_total
    
    def _calculate_rd_expenses(self, month, year):
        """Calculate R&D expenses"""
        rd_total = Decimal('0')
        
        # Add transaction-based R&D costs
        transaction_rd = Transaction.objects.filter(
            session=self.session,
            month=month,
            year=year,
            category__icontains='R&D'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        rd_total += transaction_rd
        
        # Add business strategy R&D projects
        try:
            from business_strategy.models import ResearchProject
            projects = ResearchProject.objects.filter(
                session=self.session,
                status='active'
            )
            for project in projects:
                if project.months_remaining > 0:
                    rd_total += project.monthly_investment
        except ImportError:
            pass
        
        return rd_total
    
    def _calculate_admin_expenses(self, month, year):
        """Calculate administrative expenses"""
        return Transaction.objects.filter(
            session=self.session,
            month=month,
            year=year,
            category__in=['Administrative', 'Office', 'Legal', 'Accounting']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    def _calculate_other_expenses(self, month, year):
        """Calculate other operating expenses"""
        return Transaction.objects.filter(
            session=self.session,
            month=month,
            year=year,
            category='Other'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    def _calculate_interest_income(self, month, year):
        """Calculate interest income"""
        return Decimal('0')  # Simplified
    
    def _calculate_interest_expense(self, month, year):
        """Calculate interest expense"""
        total_interest = Decimal('0')
        credits = Credit.objects.filter(
            session=self.session,
            is_active=True
        )
        for credit in credits:
            monthly_interest = credit.amount * Decimal(credit.interest_rate / 100 / 12)
            total_interest += monthly_interest
        return total_interest
    
    def _calculate_other_income(self, month, year):
        """Calculate other income"""
        return Transaction.objects.filter(
            session=self.session,
            month=month,
            year=year,
            transaction_type='income',
            category__in=['Other Income', 'Grants', 'Subsidies']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    def _calculate_other_expenses_nonop(self, month, year):
        """Calculate other non-operating expenses"""
        return Transaction.objects.filter(
            session=self.session,
            month=month,
            year=year,
            category__in=['Other Expense', 'Penalties', 'Fines']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    def _calculate_depreciation(self, month, year):
        """Calculate monthly depreciation"""
        return Decimal('500')  # Simplified
    
    def _calculate_ar_change(self, month, year):
        """Calculate accounts receivable change"""
        return Decimal('0')  # Simplified
    
    def _calculate_inventory_change(self, month, year):
        """Calculate inventory change"""
        return Decimal('0')  # Simplified
    
    def _calculate_ap_change(self, month, year):
        """Calculate accounts payable change"""
        return Decimal('0')  # Simplified
    
    def _calculate_equipment_purchases(self, month, year):
        """Calculate equipment purchases"""
        return Transaction.objects.filter(
            session=self.session,
            month=month,
            year=year,
            category__in=['Equipment', 'Machinery']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    def _calculate_facility_investments(self, month, year):
        """Calculate facility investments"""
        return Transaction.objects.filter(
            session=self.session,
            month=month,
            year=year,
            category__in=['Facility', 'Building', 'Construction']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    def _calculate_research_investments(self, month, year):
        """Calculate research investments"""
        return self._calculate_rd_expenses(month, year)
    
    def _calculate_loan_proceeds(self, month, year):
        """Calculate new loan proceeds"""
        return Credit.objects.filter(
            session=self.session,
            taken_month=month,
            taken_year=year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    def _calculate_loan_payments(self, month, year):
        """Calculate loan payments"""
        return Credit.objects.filter(
            session=self.session,
            is_active=True
        ).aggregate(total=Sum('monthly_payment'))['total'] or Decimal('0')
    
    def _calculate_accounts_receivable(self):
        """Calculate current accounts receivable"""
        return Decimal('5000')  # Simplified
    
    def _calculate_raw_materials_inventory(self):
        """Calculate raw materials inventory value"""
        total_value = Decimal('0')
        stocks = ComponentStock.objects.filter(session=self.session)
        for stock in stocks:
            # Simplified - would need component costs
            total_value += stock.quantity * Decimal('10')
        return total_value
    
    def _calculate_finished_goods_inventory(self):
        """Calculate finished goods inventory value"""
        total_value = Decimal('0')
        bikes = ProducedBike.objects.filter(
            session=self.session,
            is_sold=False
        )
        for bike in bikes:
            total_value += bike.production_cost
        return total_value
    
    def _calculate_prepaid_expenses(self):
        """Calculate prepaid expenses"""
        return Decimal('1000')  # Simplified
    
    def _calculate_land_buildings(self):
        """Calculate land and buildings value"""
        return Decimal('100000')  # Simplified
    
    def _calculate_machinery_equipment(self):
        """Calculate machinery and equipment value"""
        return Decimal('50000')  # Simplified
    
    def _calculate_accumulated_depreciation(self):
        """Calculate accumulated depreciation"""
        # Simplified - would track over time
        months_operating = (self.session.current_year - 2024) * 12 + self.session.current_month
        return Decimal('500') * months_operating
    
    def _calculate_intangible_assets(self):
        """Calculate intangible assets value"""
        return Decimal('0')  # Simplified
    
    def _calculate_investments(self):
        """Calculate investments value"""
        return Decimal('0')  # Simplified
    
    def _calculate_accounts_payable(self):
        """Calculate current accounts payable"""
        return Decimal('8000')  # Simplified
    
    def _calculate_short_term_debt(self):
        """Calculate short-term debt"""
        return Credit.objects.filter(
            session=self.session,
            is_active=True,
            credit_type__in=['instant', 'short']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    def _calculate_accrued_expenses(self):
        """Calculate accrued expenses"""
        return Decimal('2000')  # Simplified
    
    def _calculate_taxes_payable(self):
        """Calculate taxes payable"""
        return Decimal('1000')  # Simplified
    
    def _calculate_long_term_debt(self):
        """Calculate long-term debt"""
        return Credit.objects.filter(
            session=self.session,
            is_active=True,
            credit_type__in=['medium', 'long']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    def _calculate_retained_earnings(self):
        """Calculate retained earnings"""
        # Sum all net income from P&L statements
        total_earnings = ProfitLossStatement.objects.filter(
            session=self.session
        ).aggregate(total=Sum('net_income'))['total'] or Decimal('0')
        
        return total_earnings
    
    def _calculate_monthly_operating_expenses(self):
        """Calculate average monthly operating expenses"""
        current_month = self.session.current_month
        current_year = self.session.current_year
        
        try:
            pnl = ProfitLossStatement.objects.get(
                session=self.session, month=current_month, year=current_year
            )
            return pnl.total_operating_expenses
        except ProfitLossStatement.DoesNotExist:
            return Decimal('5000')  # Default estimate