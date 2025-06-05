from django.db import transaction, models
from bikeshop.models import GameSession, Worker, BikeType
from procurement.models import ProcurementOrder, ProcurementOrderItem
from production.models import ProductionPlan, ProductionOrder, ProducedBike
from warehouse.models import Warehouse, ComponentStock
from finance.models import Credit, Transaction, MonthlyReport
from sales.models import SalesOrder, Market
from decimal import Decimal
import random


class SimulationEngine:
    """Hauptsimulationslogik"""

    def __init__(self, session):
        self.session = session

    def process_month(self):
        """Verarbeitet einen Monat der Simulation"""
        with transaction.atomic():
            # 1. Lieferungen verarbeiten
            self._process_deliveries()

            # 2. Produktion durchführen
            self._process_production()

            # 3. Löhne zahlen
            self._pay_salaries()

            # 4. Kreditzahlungen
            self._process_credit_payments()

            # 5. Alle 3 Monate: Verkäufe verarbeiten
            if self.session.current_month % 3 == 0:
                self._process_sales()
                self._pay_rent()

            # 6. Nächsten Monat
            self._advance_month()

    def _process_deliveries(self):
        """Verarbeitet Lieferungen"""
        orders = ProcurementOrder.objects.filter(
            session=self.session,
            month=self.session.current_month,
            year=self.session.current_year,
            is_delivered=False
        )

        warehouses = list(Warehouse.objects.filter(session=self.session))
        default_warehouse = warehouses[0] if warehouses else None

        for order in orders:
            # Reklamationen simulieren
            has_complaints = random.random() < (order.supplier.complaint_probability / 100)

            for item in order.items.all():
                delivered_quantity = item.quantity_ordered

                if has_complaints:
                    complaint_rate = order.supplier.complaint_quantity / 100
                    defective_quantity = int(item.quantity_ordered * complaint_rate)
                    delivered_quantity -= defective_quantity
                    item.is_defective = defective_quantity > 0

                item.quantity_delivered = delivered_quantity
                item.save()

                # In Lager einbuchen
                if default_warehouse and delivered_quantity > 0:
                    stock, created = ComponentStock.objects.get_or_create(
                        session=self.session,
                        warehouse=default_warehouse,
                        component=item.component,
                        defaults={'quantity': 0}
                    )
                    stock.quantity += delivered_quantity
                    stock.save()

            order.is_delivered = True
            order.save()

    def _process_production(self):
        """Führt Produktion durch"""
        try:
            plan = ProductionPlan.objects.get(
                session=self.session,
                month=self.session.current_month,
                year=self.session.current_year
            )

            warehouses = Warehouse.objects.filter(session=self.session)
            default_warehouse = warehouses.first()

            for order in plan.orders.all():
                produced = 0

                for _ in range(order.quantity_planned):
                    # Prüfe verfügbare Materialien
                    if self._check_materials_available(order.bike_type):
                        # Materialien verbrauchen
                        self._consume_materials(order.bike_type)

                        # Fahrrad produzieren
                        bike = ProducedBike.objects.create(
                            session=self.session,
                            bike_type=order.bike_type,
                            price_segment=order.price_segment,
                            production_month=self.session.current_month,
                            production_year=self.session.current_year,
                            warehouse=default_warehouse,
                            production_cost=self._calculate_production_cost(order.bike_type)
                        )
                        produced += 1
                    else:
                        break

                order.quantity_produced = produced
                order.save()

        except ProductionPlan.DoesNotExist:
            pass

    def _check_materials_available(self, bike_type):
        """Prüft ob Materialien verfügbar sind"""
        required_components = [
            bike_type.wheel_set,
            bike_type.frame,
            bike_type.handlebar,
            bike_type.saddle,
            bike_type.gearshift
        ]

        if bike_type.motor:
            required_components.append(bike_type.motor)

        for component in required_components:
            total_stock = ComponentStock.objects.filter(
                session=self.session,
                component=component
            ).aggregate(total=models.Sum('quantity'))['total'] or 0

            if total_stock < 1:
                return False

        return True

    def _consume_materials(self, bike_type):
        """Verbraucht Materialien für Produktion"""
        required_components = [
            bike_type.wheel_set,
            bike_type.frame,
            bike_type.handlebar,
            bike_type.saddle,
            bike_type.gearshift
        ]

        if bike_type.motor:
            required_components.append(bike_type.motor)

        for component in required_components:
            stock = ComponentStock.objects.filter(
                session=self.session,
                component=component,
                quantity__gt=0
            ).first()

            if stock:
                stock.quantity -= 1
                stock.save()

    def _calculate_production_cost(self, bike_type):
        """Berechnet Produktionskosten"""
        workers = Worker.objects.filter(session=self.session)
        skilled_worker = workers.filter(worker_type='skilled').first()
        unskilled_worker = workers.filter(worker_type='unskilled').first()

        skilled_cost = (skilled_worker.hourly_wage * bike_type.skilled_worker_hours
                        if skilled_worker else 0)
        unskilled_cost = (unskilled_worker.hourly_wage * bike_type.unskilled_worker_hours
                          if unskilled_worker else 0)

        return skilled_cost + unskilled_cost

    def _pay_salaries(self):
        """Zahlt Löhne"""
        workers = Worker.objects.filter(session=self.session)
        total_salaries = 0

        for worker in workers:
            salary = worker.count * worker.hourly_wage * worker.monthly_hours
            total_salaries += salary

        self.session.balance -= total_salaries
        self.session.save()

        Transaction.objects.create(
            session=self.session,
            transaction_type='expense',
            category='Löhne',
            amount=total_salaries,
            description='Monatliche Lohnzahlungen',
            month=self.session.current_month,
            year=self.session.current_year
        )

    def _process_credit_payments(self):
        """Verarbeitet Kreditzahlungen"""
        active_credits = Credit.objects.filter(session=self.session, is_active=True)
        total_payments = 0

        for credit in active_credits:
            if credit.remaining_months > 0:
                self.session.balance -= credit.monthly_payment
                total_payments += credit.monthly_payment

                credit.remaining_months -= 1
                if credit.remaining_months == 0:
                    credit.is_active = False
                credit.save()

        if total_payments > 0:
            Transaction.objects.create(
                session=self.session,
                transaction_type='expense',
                category='Kreditzahlungen',
                amount=total_payments,
                description='Monatliche Kreditzahlungen',
                month=self.session.current_month,
                year=self.session.current_year
            )

    def _process_sales(self):
        """Verarbeitet Verkäufe (alle 3 Monate)"""
        # Simuliere Marktnachfrage
        sales_orders = SalesOrder.objects.filter(
            session=self.session,
            sale_month__lte=self.session.current_month,
            sale_year=self.session.current_year,
            is_completed=False
        )

        total_revenue = 0

        for order in sales_orders:
            # Verkauf mit Wahrscheinlichkeit basierend auf Markt und Saison
            if self._simulate_sale_success(order):
                revenue = order.sale_price - order.transport_cost
                total_revenue += revenue

                order.is_completed = True
                order.save()

        if total_revenue > 0:
            self.session.balance += total_revenue
            self.session.save()

            Transaction.objects.create(
                session=self.session,
                transaction_type='income',
                category='Verkäufe',
                amount=total_revenue,
                description='Verkaufserlöse',
                month=self.session.current_month,
                year=self.session.current_year
            )

    def _simulate_sale_success(self, order):
        """Simuliert Verkaufserfolg"""
        # Basis-Wahrscheinlichkeit
        base_probability = 0.7

        # Saisonale Effekte
        seasonal_bonus = self._get_seasonal_bonus(order.bike.bike_type.name)

        # Preissegment-Effekt
        segment_bonus = {
            'cheap': 0.2,
            'standard': 0.1,
            'premium': -0.1
        }.get(order.bike.price_segment, 0)

        total_probability = base_probability + seasonal_bonus + segment_bonus
        return random.random() < total_probability

    def _get_seasonal_bonus(self, bike_type_name):
        """Gibt saisonalen Bonus zurück"""
        month = self.session.current_month

        # Mountainbikes im Sommer
        if 'Mountain' in bike_type_name and month in [5, 6, 7, 8]:
            return 0.15

        # E-Bikes im Herbst
        if 'E-' in bike_type_name and month in [9, 10]:
            return 0.1

        return 0

    def _pay_rent(self):
        """Zahlt Lagermiete (alle 3 Monate)"""
        warehouses = Warehouse.objects.filter(session=self.session)
        total_rent = sum(w.rent_per_month for w in warehouses) * 3  # 3 Monate

        self.session.balance -= total_rent
        self.session.save()

        Transaction.objects.create(
            session=self.session,
            transaction_type='expense',
            category='Lagermiete',
            amount=total_rent,
            description='Quartalsweise Lagermiete',
            month=self.session.current_month,
            year=self.session.current_year
        )

    def _advance_month(self):
        """Geht zum nächsten Monat"""
        self.session.current_month += 1
        if self.session.current_month > 12:
            self.session.current_month = 1
            self.session.current_year += 1

        self.session.save()

    def get_dashboard_data(self):
        """Holt Dashboard-Daten"""
        # Aktuelle Bestände
        component_stocks = ComponentStock.objects.filter(session=self.session)
        produced_bikes = ProducedBike.objects.filter(session=self.session, is_sold=False)

        # Finanzübersicht
        recent_transactions = Transaction.objects.filter(
            session=self.session
        ).order_by('-created_at')[:10]

        # Arbeiter
        workers = Worker.objects.filter(session=self.session)
        skilled_workers = workers.filter(worker_type='skilled').first()
        unskilled_workers = workers.filter(worker_type='unskilled').first()
        
        total_workers = (skilled_workers.count if skilled_workers else 0) + (unskilled_workers.count if unskilled_workers else 0)

        return {
            'balance': self.session.balance,
            'month': self.session.current_month,
            'year': self.session.current_year,
            'component_stocks': component_stocks,
            'produced_bikes': produced_bikes,
            'recent_transactions': recent_transactions,
            'workers': total_workers,
            'skilled_workers': skilled_workers,
            'unskilled_workers': unskilled_workers,
            'workers_list': workers
        }
