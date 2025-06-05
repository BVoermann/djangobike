from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from bikeshop.models import GameSession
from .models import Credit, Transaction, MonthlyReport
import json


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
                amount = float(data.get('amount'))

                # Kreditkonditionen
                credit_conditions = {
                    'short': {'rate': 10, 'months': 3},
                    'medium': {'rate': 8, 'months': 6},
                    'long': {'rate': 6, 'months': 12}
                }

                conditions = credit_conditions[credit_type]
                max_amount = session.balance * 0.25  # Maximal 25% des Guthabens

                if amount > max_amount:
                    return JsonResponse({'success': False, 'error': 'Kreditbetrag zu hoch!'})

                monthly_payment = amount * (1 + conditions['rate'] / 100) / conditions['months']

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
