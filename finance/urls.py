from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('<uuid:session_id>/', views.finance_view, name='finance'),
    path('<uuid:session_id>/dashboard/', views.financial_dashboard, name='dashboard'),
    path('<uuid:session_id>/profit-loss/', views.profit_loss_statement, name='profit_loss'),
    path('<uuid:session_id>/cash-flow/', views.cash_flow_statement, name='cash_flow'),
    path('<uuid:session_id>/balance-sheet/', views.balance_sheet, name='balance_sheet'),
    path('<uuid:session_id>/liquidity/', views.liquidity_analysis, name='liquidity'),
    path('<uuid:session_id>/sales-report/', views.sales_report_detail, name='sales_report'),
    path('<uuid:session_id>/settlement-modal/', views.monthly_settlement_modal, name='settlement_modal'),
    path('<uuid:session_id>/generate-reports/', views.generate_all_reports, name='generate_reports'),
]