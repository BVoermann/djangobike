from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from bikeshop.models import GameSession, Worker
from warehouse.models import Warehouse
from .models import (
    Credit, Transaction, MonthlyReport, ProfitLossStatement,
    CashFlowStatement, BalanceSheet, LiquidityAnalysis, SalesReport
)
from .financial_engine import FinancialReportingEngine
from decimal import Decimal
import json


def _calculate_recurring_costs(session):
    """Calculate all recurring costs for the session"""
    recurring_costs = {
        'monthly': [],
        'quarterly': [],
        'total_monthly': Decimal('0'),
        'total_quarterly': Decimal('0'),
        'total_annual': Decimal('0'),
    }

    # 1. Worker salaries (monthly)
    workers = Worker.objects.filter(session=session)
    worker_costs = []
    total_worker_cost = Decimal('0')

    for worker in workers:
        if worker.count > 0:
            monthly_cost = worker.hourly_wage * Decimal(str(worker.monthly_hours)) * Decimal(str(worker.count))
            total_worker_cost += monthly_cost
            worker_costs.append({
                'name': str(worker),
                'type': worker.get_worker_type_display(),
                'count': worker.count,
                'hourly_wage': worker.hourly_wage,
                'monthly_hours': worker.monthly_hours,
                'monthly_cost': monthly_cost,
                'category': 'Löhne'
            })

    if worker_costs:
        recurring_costs['monthly'].append({
            'category': 'Löhne',
            'items': worker_costs,
            'subtotal': total_worker_cost,
            'icon': 'fa-users'
        })
        recurring_costs['total_monthly'] += total_worker_cost

    # 2. Warehouse rent (quarterly, but show monthly equivalent)
    warehouses = Warehouse.objects.filter(session=session)
    warehouse_costs = []
    total_warehouse_cost = Decimal('0')

    for warehouse in warehouses:
        warehouse_costs.append({
            'name': str(warehouse),
            'location': warehouse.location,
            'capacity': warehouse.capacity_m2,
            'monthly_cost': warehouse.rent_per_month,
            'quarterly_cost': warehouse.rent_per_month * Decimal('3'),
            'category': 'Lagermiete'
        })
        total_warehouse_cost += warehouse.rent_per_month

    if warehouse_costs:
        recurring_costs['quarterly'].append({
            'category': 'Lagermiete',
            'items': warehouse_costs,
            'subtotal': total_warehouse_cost,
            'quarterly_total': total_warehouse_cost * Decimal('3'),
            'icon': 'fa-warehouse'
        })
        recurring_costs['total_quarterly'] += total_warehouse_cost * Decimal('3')

    # 3. Credit payments (monthly)
    active_credits = Credit.objects.filter(session=session, is_active=True)
    credit_costs = []
    total_credit_cost = Decimal('0')

    for credit in active_credits:
        credit_costs.append({
            'type': credit.get_credit_type_display(),
            'amount': credit.amount,
            'interest_rate': credit.interest_rate,
            'monthly_payment': credit.monthly_payment,
            'remaining_months': credit.remaining_months,
            'total_remaining': credit.monthly_payment * credit.remaining_months,
            'category': 'Kreditzahlungen'
        })
        total_credit_cost += credit.monthly_payment

    if credit_costs:
        recurring_costs['monthly'].append({
            'category': 'Kreditzahlungen',
            'items': credit_costs,
            'subtotal': total_credit_cost,
            'icon': 'fa-credit-card'
        })
        recurring_costs['total_monthly'] += total_credit_cost

    # Calculate total annual costs
    recurring_costs['total_annual'] = (
        (recurring_costs['total_monthly'] * Decimal('12')) +
        (recurring_costs['total_quarterly'] * Decimal('4'))
    )

    # Add summary
    recurring_costs['summary'] = {
        'monthly': recurring_costs['total_monthly'],
        'quarterly': recurring_costs['total_quarterly'],
        'annual': recurring_costs['total_annual'],
        'avg_monthly': recurring_costs['total_monthly'] + (recurring_costs['total_quarterly'] / Decimal('3'))
    }

    return recurring_costs


@login_required
def finance_view(request, session_id):
    """Finanzansicht"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)

    # Aktuelle Kredite
    active_credits = Credit.objects.filter(session=session, is_active=True)

    # Transaktionen des aktuellen Monats
    current_transactions = Transaction.objects.filter(
        session=session,
        month=session.current_month,
        year=session.current_year
    ).order_by('-created_at')

    # Monatsbericht
    monthly_reports = MonthlyReport.objects.filter(session=session).order_by('-year', '-month')[:6]

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')

            if action == 'take_credit':
                credit_type = data.get('credit_type')
                amount = Decimal(str(data.get('amount')))

                # Kreditkonditionen - use interest_rate parameter
                from multiplayer.parameter_utils import get_interest_rate, apply_loan_availability_multiplier
                base_interest_rate = get_interest_rate(session)  # Get from game parameters (default 5%)

                # Apply multipliers to base rate for different credit types
                credit_conditions = {
                    'instant': {'rate': base_interest_rate * 3.0, 'months': 1},    # 3x base (e.g., 15% if base is 5%)
                    'short': {'rate': base_interest_rate * 2.0, 'months': 3},      # 2x base (e.g., 10% if base is 5%)
                    'medium': {'rate': base_interest_rate * 1.6, 'months': 6},     # 1.6x base (e.g., 8% if base is 5%)
                    'long': {'rate': base_interest_rate * 1.2, 'months': 12}       # 1.2x base (e.g., 6% if base is 5%)
                }

                conditions = credit_conditions[credit_type]

                # Sofortkredit hat niedrigere Maximalgrenze (15% des Guthabens)
                if credit_type == 'instant':
                    base_max_amount = session.balance * Decimal('0.15')
                else:
                    base_max_amount = session.balance * Decimal('0.25')  # Andere Kredite: 25% des Guthabens

                # Apply loan availability multiplier from game parameters
                max_amount = apply_loan_availability_multiplier(base_max_amount, session)

                if amount > max_amount:
                    return JsonResponse({'success': False, 'error': 'Kreditbetrag zu hoch!'})

                monthly_payment = amount * (Decimal('1') + Decimal(str(conditions['rate'])) / Decimal('100')) / Decimal(str(conditions['months']))

                Credit.objects.create(
                    session=session,
                    credit_type=credit_type,
                    amount=amount,
                    interest_rate=conditions['rate'],
                    duration_months=conditions['months'],
                    remaining_months=conditions['months'],
                    monthly_payment=monthly_payment,
                    taken_month=session.current_month,
                    taken_year=session.current_year
                )

                session.balance += amount
                session.save()

                Transaction.objects.create(
                    session=session,
                    transaction_type='income',
                    category='Kredit',
                    amount=amount,
                    description=f'{credit_type.title()}er Kredit aufgenommen',
                    month=session.current_month,
                    year=session.current_year
                )

                return JsonResponse({'success': True, 'message': 'Kredit erfolgreich aufgenommen!'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'finance/finance.html', {
        'session': session,
        'active_credits': active_credits,
        'current_transactions': current_transactions,
        'monthly_reports': monthly_reports
    })


@login_required
def profit_loss_statement(request, session_id):
    """Profit & Loss Statement"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Get P&L statements for the last 12 months
    pnl_statements = ProfitLossStatement.objects.filter(
        session=session
    ).order_by('-year', '-month')[:12]
    
    # Current month P&L
    try:
        current_pnl = ProfitLossStatement.objects.get(
            session=session,
            month=session.current_month,
            year=session.current_year
        )
    except ProfitLossStatement.DoesNotExist:
        # Generate if doesn't exist
        engine = FinancialReportingEngine(session)
        current_pnl = engine.generate_profit_loss_statement()
    
    return render(request, 'finance/profit_loss.html', {
        'session': session,
        'current_pnl': current_pnl,
        'pnl_statements': pnl_statements
    })


@login_required
def cash_flow_statement(request, session_id):
    """Cash Flow Statement"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Get cash flow statements for the last 12 months
    cf_statements = CashFlowStatement.objects.filter(
        session=session
    ).order_by('-year', '-month')[:12]
    
    # Current month cash flow
    try:
        current_cf = CashFlowStatement.objects.get(
            session=session,
            month=session.current_month,
            year=session.current_year
        )
    except CashFlowStatement.DoesNotExist:
        # Generate if doesn't exist
        engine = FinancialReportingEngine(session)
        current_cf = engine.generate_cash_flow_statement()
    
    return render(request, 'finance/cash_flow.html', {
        'session': session,
        'current_cf': current_cf,
        'cf_statements': cf_statements
    })


@login_required
def balance_sheet(request, session_id):
    """Balance Sheet"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Get balance sheets for the last 12 months
    balance_sheets = BalanceSheet.objects.filter(
        session=session
    ).order_by('-year', '-month')[:12]
    
    # Current month balance sheet
    try:
        current_bs = BalanceSheet.objects.get(
            session=session,
            month=session.current_month,
            year=session.current_year
        )
    except BalanceSheet.DoesNotExist:
        # Generate if doesn't exist
        engine = FinancialReportingEngine(session)
        current_bs = engine.generate_balance_sheet()
    
    return render(request, 'finance/balance_sheet.html', {
        'session': session,
        'current_bs': current_bs,
        'balance_sheets': balance_sheets
    })


@login_required
def liquidity_analysis(request, session_id):
    """Liquidity Analysis"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Get liquidity analyses for the last 12 months
    analyses = LiquidityAnalysis.objects.filter(
        session=session
    ).order_by('-year', '-month')[:12]
    
    # Current month liquidity analysis
    try:
        current_analysis = LiquidityAnalysis.objects.get(
            session=session,
            month=session.current_month,
            year=session.current_year
        )
    except LiquidityAnalysis.DoesNotExist:
        # Generate if doesn't exist
        engine = FinancialReportingEngine(session)
        current_analysis = engine.generate_liquidity_analysis()
    
    return render(request, 'finance/liquidity_analysis.html', {
        'session': session,
        'current_analysis': current_analysis,
        'analyses': analyses
    })


@login_required
def sales_report_detail(request, session_id):
    """Detailed Sales Report"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Get sales reports for the last 12 months
    sales_reports = SalesReport.objects.filter(
        session=session
    ).order_by('-year', '-month')[:12]
    
    # Current month sales report
    try:
        current_report = SalesReport.objects.get(
            session=session,
            month=session.current_month,
            year=session.current_year
        )
    except SalesReport.DoesNotExist:
        # Generate if doesn't exist
        engine = FinancialReportingEngine(session)
        current_report = engine.generate_sales_report()
    
    return render(request, 'finance/sales_report.html', {
        'session': session,
        'current_report': current_report,
        'sales_reports': sales_reports
    })


@login_required
def financial_dashboard(request, session_id):
    """Comprehensive Financial Dashboard"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)

    engine = FinancialReportingEngine(session)

    # Get current month reports (generate if needed)
    try:
        current_pnl = ProfitLossStatement.objects.get(
            session=session,
            month=session.current_month,
            year=session.current_year
        )
    except ProfitLossStatement.DoesNotExist:
        current_pnl = engine.generate_profit_loss_statement()

    try:
        current_cf = CashFlowStatement.objects.get(
            session=session,
            month=session.current_month,
            year=session.current_year
        )
    except CashFlowStatement.DoesNotExist:
        current_cf = engine.generate_cash_flow_statement()

    try:
        current_bs = BalanceSheet.objects.get(
            session=session,
            month=session.current_month,
            year=session.current_year
        )
    except BalanceSheet.DoesNotExist:
        current_bs = engine.generate_balance_sheet()

    try:
        current_liquidity = LiquidityAnalysis.objects.get(
            session=session,
            month=session.current_month,
            year=session.current_year
        )
    except LiquidityAnalysis.DoesNotExist:
        current_liquidity = engine.generate_liquidity_analysis()

    try:
        current_sales = SalesReport.objects.get(
            session=session,
            month=session.current_month,
            year=session.current_year
        )
    except SalesReport.DoesNotExist:
        current_sales = engine.generate_sales_report()

    # Get historical data for charts
    historical_pnl = ProfitLossStatement.objects.filter(
        session=session
    ).order_by('year', 'month')[:12]

    historical_liquidity = LiquidityAnalysis.objects.filter(
        session=session
    ).order_by('year', 'month')[:12]

    # Calculate recurring costs
    recurring_costs = _calculate_recurring_costs(session)

    return render(request, 'finance/financial_dashboard.html', {
        'session': session,
        'current_pnl': current_pnl,
        'current_cf': current_cf,
        'current_bs': current_bs,
        'current_liquidity': current_liquidity,
        'current_sales': current_sales,
        'historical_pnl': historical_pnl,
        'historical_liquidity': historical_liquidity,
        'recurring_costs': recurring_costs
    })


@login_required
def monthly_settlement_modal(request, session_id):
    """AJAX endpoint for monthly settlement modal"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    # Get the current month's financial reports
    engine = FinancialReportingEngine(session)
    
    # Get or generate current month reports
    try:
        sales_report = SalesReport.objects.get(
            session=session,
            month=session.current_month,
            year=session.current_year
        )
    except SalesReport.DoesNotExist:
        sales_report = engine.generate_sales_report()
    
    try:
        pnl = ProfitLossStatement.objects.get(
            session=session,
            month=session.current_month,
            year=session.current_year
        )
    except ProfitLossStatement.DoesNotExist:
        pnl = engine.generate_profit_loss_statement()
    
    try:
        liquidity = LiquidityAnalysis.objects.get(
            session=session,
            month=session.current_month,
            year=session.current_year
        )
    except LiquidityAnalysis.DoesNotExist:
        liquidity = engine.generate_liquidity_analysis()
    
    # Prepare settlement data
    settlement_data = {
        'month': session.current_month,
        'year': session.current_year,
        'sales': {
            'total_units': sales_report.total_units_sold,
            'total_revenue': float(sales_report.total_revenue),
            'avg_price': float(sales_report.average_selling_price),
            'growth_rate': sales_report.revenue_growth_rate,
            'product_breakdown': sales_report.product_line_breakdown,
            'segment_breakdown': sales_report.segment_breakdown,
            'regional_breakdown': sales_report.regional_breakdown,
            'market_share': sales_report.market_share_total
        },
        'financial': {
            'net_income': float(pnl.net_income),
            'gross_profit': float(pnl.gross_profit),
            'gross_margin': pnl.gross_profit_margin,
            'operating_income': float(pnl.operating_income),
            'operating_margin': pnl.operating_margin,
            'net_margin': pnl.net_profit_margin
        },
        'liquidity': {
            'current_ratio': liquidity.current_ratio,
            'quick_ratio': liquidity.quick_ratio,
            'cash_ratio': liquidity.cash_ratio,
            'working_capital': float(liquidity.working_capital),
            'liquidity_status': liquidity.liquidity_status,
            'cash_runway': liquidity.cash_runway_months
        },
        'performance_indicators': {
            'revenue_growth': sales_report.revenue_growth_rate,
            'unit_growth': sales_report.units_growth_rate,
            'customer_retention': sales_report.customer_retention_rate,
            'new_customers': sales_report.new_customers_acquired
        }
    }
    
    return JsonResponse({
        'success': True,
        'settlement_data': settlement_data
    })


@login_required
def generate_all_reports(request, session_id):
    """Generate all financial reports for current month"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    if request.method == 'POST':
        try:
            engine = FinancialReportingEngine(session)
            engine.generate_monthly_settlement()
            
            return JsonResponse({
                'success': True,
                'message': 'All financial reports generated successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})