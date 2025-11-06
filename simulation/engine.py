from django.db import transaction, models
from bikeshop.models import GameSession, Worker, BikeType
from procurement.models import ProcurementOrder, ProcurementOrderItem
from production.models import ProductionPlan, ProductionOrder, ProducedBike
from warehouse.models import Warehouse, ComponentStock
from finance.models import Credit, Transaction, MonthlyReport
from sales.models import SalesOrder, Market
from sales.market_simulator import MarketSimulator
from competitors.ai_engine import CompetitorAIEngine
from competitors.models import MarketCompetition, CompetitorSale
from .competitive_sales_engine import CompetitiveSalesEngine
from business_strategy.business_engine import BusinessStrategyEngine
from random_events.event_engine import RandomEventsEngine
from finance.financial_engine import FinancialReportingEngine
from decimal import Decimal
import random
import logging

logger = logging.getLogger(__name__)


class SimulationEngine:
    """Hauptsimulationslogik"""

    def __init__(self, session):
        self.session = session
        self.competitor_engine = CompetitorAIEngine(session)
        self.competitive_sales_engine = CompetitiveSalesEngine(session)
        self.market_simulator = MarketSimulator(session)
        self.business_strategy_engine = BusinessStrategyEngine(session)
        self.random_events_engine = RandomEventsEngine(session)
        self.financial_engine = FinancialReportingEngine(session)

    def process_month(self):
        """Verarbeitet einen Monat der Simulation"""
        with transaction.atomic():
            # 1. Business Strategy processing (R&D, Marketing, Sustainability)
            self.business_strategy_engine.process_monthly_business_strategy()

            # 2. Random Events processing (innovations, regulations, market opportunities)
            self.random_events_engine.process_monthly_events()

            # 3. Lieferungen verarbeiten
            self._process_deliveries()

            # 4. Produktion durchführen (with business strategy bonuses)
            self._process_production()

            # 5. Konkurrenten-Aktivitäten
            self.competitor_engine.process_competitor_month()

            # 6. Löhne zahlen
            self._pay_salaries()

            # 7. Kreditzahlungen
            self._process_credit_payments()

            # 8. Alle 3 Monate: Verkäufe verarbeiten (with marketing and sustainability effects)
            if self.session.current_month % 3 == 0:
                self._process_competitive_sales()
                self._pay_rent()
            else:
                # Update inventory aging monthly
                self._update_inventory_ages()

            # 9. Generate comprehensive financial reports and monthly settlement
            self.financial_engine.generate_monthly_settlement()

            # 10. Nächsten Monat
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
                    if self._check_materials_available(order.bike_type, order.price_segment):
                        # Materialien verbrauchen
                        self._consume_materials(order.bike_type, order.price_segment)

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

    def _check_materials_available(self, bike_type, price_segment='standard'):
        """Prüft ob Materialien mit passender Qualität verfügbar sind"""
        from bikeshop.models import Component, ComponentType
        
        # Get all required component types for this bike
        required_components = bike_type.get_required_components()
        
        for component_type_name, compatible_names in required_components.items():
            # Check if we have any compatible components in stock
            component_type = ComponentType.objects.filter(
                session=self.session, 
                name=component_type_name
            ).first()
            
            if not component_type:
                continue
                
            # Find compatible components
            compatible_components = Component.objects.filter(
                session=self.session,
                component_type=component_type,
                name__in=compatible_names
            )
            
            # Check if any compatible component has stock AND correct quality
            has_stock = False
            for component in compatible_components:
                if component.is_compatible_with_segment(self.session, price_segment):
                    total_stock = ComponentStock.objects.filter(
                        session=self.session,
                        component=component
                    ).aggregate(total=models.Sum('quantity'))['total'] or 0
                    
                    if total_stock >= 1:
                        has_stock = True
                        break
            
            if not has_stock:
                return False

        return True

    def _consume_materials(self, bike_type, price_segment='standard'):
        """Verbraucht Materialien für Produktion mit Qualitätsprüfung"""
        from bikeshop.models import Component, ComponentType
        
        # Get all required component types for this bike
        required_components = bike_type.get_required_components()
        
        for component_type_name, compatible_names in required_components.items():
            # Find the first available compatible component
            component_type = ComponentType.objects.filter(
                session=self.session, 
                name=component_type_name
            ).first()
            
            if not component_type:
                continue
                
            # Find compatible components with stock
            compatible_components = Component.objects.filter(
                session=self.session,
                component_type=component_type,
                name__in=compatible_names
            )
            
            # Filter by quality compatibility and prioritize appropriate quality
            quality_compatible = []
            for component in compatible_components:
                if component.is_compatible_with_segment(self.session, price_segment):
                    stock = ComponentStock.objects.filter(
                        session=self.session,
                        component=component,
                        quantity__gt=0
                    ).first()
                    if stock:
                        quality_compatible.append((component, stock))
            
            # Sort by quality to prefer exact matches
            def quality_priority(comp_stock):
                component, stock = comp_stock
                quality = component.get_quality_for_session(self.session)
                quality_rank = {'basic': 1, 'standard': 2, 'premium': 3}
                segment_rank = {'cheap': 1, 'standard': 2, 'premium': 3}
                
                # Prefer exact quality matches
                if (quality == 'basic' and price_segment == 'cheap') or \
                   (quality == 'standard' and price_segment == 'standard') or \
                   (quality == 'premium' and price_segment == 'premium'):
                    return 0  # Highest priority
                else:
                    return abs(quality_rank.get(quality, 2) - segment_rank.get(price_segment, 2))
            
            quality_compatible.sort(key=quality_priority)
            
            # Consume from the best available component
            consumed = False
            if quality_compatible:
                component, stock = quality_compatible[0]
                stock.quantity -= 1
                stock.save()
                consumed = True
            
            # This should not happen if _check_materials_available passed
            if not consumed:
                print(f"Warning: Could not consume {component_type_name} for {bike_type.name} ({price_segment})")

    def _calculate_production_cost(self, bike_type):
        """Berechnet Produktionskosten mit Business Strategy Boni"""
        workers = Worker.objects.filter(session=self.session)
        skilled_worker = workers.filter(worker_type='skilled').first()
        unskilled_worker = workers.filter(worker_type='unskilled').first()

        base_skilled_cost = (skilled_worker.hourly_wage * Decimal(str(bike_type.skilled_worker_hours))
                            if skilled_worker else Decimal('0'))
        base_unskilled_cost = (unskilled_worker.hourly_wage * Decimal(str(bike_type.unskilled_worker_hours))
                              if unskilled_worker else Decimal('0'))

        base_cost = base_skilled_cost + base_unskilled_cost
        
        # Apply R&D cost reduction bonuses
        rd_bonuses = self.business_strategy_engine.get_rd_production_bonuses()
        cost_reduction = rd_bonuses.get('cost_reduction', 0.0) / 100.0  # Convert percentage to decimal
        
        # Apply cost reduction (cannot reduce below 10% of original cost)
        final_cost = base_cost * Decimal(str(max(0.1, 1.0 - cost_reduction)))
        
        return final_cost

    def _pay_salaries(self):
        """Zahlt Löhne"""
        workers = Worker.objects.filter(session=self.session)
        total_salaries = Decimal('0')

        for worker in workers:
            salary = Decimal(str(worker.count)) * worker.hourly_wage * Decimal(str(worker.monthly_hours))
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
        total_payments = Decimal('0')

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

    def _process_competitive_sales(self):
        """Process sales using competitive market system"""
        logger.info(f"Processing competitive sales for month {self.session.current_month}/{self.session.current_year}")

        # First, process player's pending sales decisions
        logger.info("Processing player sales decisions with market simulator...")
        self.market_simulator.process_pending_sales_decisions(
            self.session.current_month,
            self.session.current_year
        )

        # Then, use the existing competitive sales engine for any remaining competitive dynamics
        logger.info("Processing competitive sales with existing engine...")
        self.competitive_sales_engine.process_competitive_sales(
            self.session.current_month,
            self.session.current_year
        )
    
    def _update_inventory_ages(self):
        """Update inventory ages for unsold bikes monthly"""
        unsold_bikes = ProducedBike.objects.filter(
            session=self.session,
            is_sold=False
        )
        
        for bike in unsold_bikes:
            bike.update_inventory_age(self.session.current_month, self.session.current_year)
    
    def _process_sales_legacy(self):
        """Legacy sales processing (kept for reference)"""
        # Simuliere Marktnachfrage
        sales_orders = SalesOrder.objects.filter(
            session=self.session,
            sale_month__lte=self.session.current_month,
            sale_year=self.session.current_year,
            is_completed=False
        )

        total_revenue = Decimal('0')

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
        """Simuliert Verkaufserfolg mit Markt-Wettbewerb"""
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

        # Markt-Wettbewerbs-Effekt
        competition_penalty = self._get_market_competition_penalty(order)

        total_probability = base_probability + seasonal_bonus + segment_bonus - competition_penalty
        return random.random() < max(0.1, total_probability)  # Minimum 10% Chance

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
    
    def _get_market_competition_penalty(self, order):
        """Berechnet Wettbewerbs-Malus für Verkaufschance"""
        try:
            competition = MarketCompetition.objects.get(
                session=self.session,
                market=order.market,
                bike_type=order.bike.bike_type,
                price_segment=order.bike.price_segment,
                month=self.session.current_month,
                year=self.session.current_year
            )
            
            # Sättigung reduziert Verkaufschance
            saturation_penalty = min(0.4, competition.saturation_level * 0.3)
            
            # Preisdruck (negative Werte bedeuten niedrigere Preise = bessere Chancen)
            price_pressure_effect = max(0, competition.price_pressure * 0.2)
            
            return saturation_penalty + price_pressure_effect
            
        except MarketCompetition.DoesNotExist:
            return 0

    def _pay_rent(self):
        """Zahlt Lagermiete (alle 3 Monate)"""
        warehouses = Warehouse.objects.filter(session=self.session)
        total_rent = sum(w.rent_per_month for w in warehouses) * Decimal('3')  # 3 Monate

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
        """Geht zum nächsten Monat und speichert Monatsbericht"""
        # Store current month data before advancing
        self._create_monthly_report()
        
        self.session.current_month += 1
        if self.session.current_month > 12:
            self.session.current_month = 1
            self.session.current_year += 1

        self.session.save()
        
    def _create_monthly_report(self):
        """Erstellt umfassenden Monatsbericht"""
        current_month = self.session.current_month
        current_year = self.session.current_year
        
        # Get opening balance (from previous month report or session start)
        try:
            if current_month > 1:
                prev_report = MonthlyReport.objects.get(
                    session=self.session,
                    month=current_month - 1,
                    year=current_year
                )
                opening_balance = prev_report.closing_balance
            else:
                # January - get from December of previous year
                prev_report = MonthlyReport.objects.get(
                    session=self.session,
                    month=12,
                    year=current_year - 1
                )
                opening_balance = prev_report.closing_balance
        except MonthlyReport.DoesNotExist:
            # First month or no previous report - use default starting balance
            opening_balance = Decimal('80000.00')
        
        closing_balance = self.session.balance
        
        # Get current month transactions
        transactions = Transaction.objects.filter(
            session=self.session,
            month=current_month,
            year=current_year
        )
        
        total_income = sum(t.amount for t in transactions if t.transaction_type == 'income')
        total_expenses = sum(t.amount for t in transactions if t.transaction_type == 'expense')
        
        # Production data
        produced_bikes = ProducedBike.objects.filter(
            session=self.session,
            production_month=current_month,
            production_year=current_year
        )
        
        bikes_produced_count = produced_bikes.count()
        total_production_cost = sum(bike.production_cost for bike in produced_bikes)
        
        production_summary = {}
        for bike in produced_bikes:
            bike_key = f"{bike.bike_type.name} ({bike.get_price_segment_display()})"
            if bike_key not in production_summary:
                production_summary[bike_key] = {'count': 0, 'cost': 0}
            production_summary[bike_key]['count'] += 1
            production_summary[bike_key]['cost'] += float(bike.production_cost)
        
        # ACTUAL COMPLETED SALES DATA (bikes actually sold this month)
        # Get sales orders created this month directly from SalesOrder model
        sales_orders_this_month = SalesOrder.objects.filter(
            session=self.session,
            sale_month=current_month,
            sale_year=current_year
        ).select_related('bike', 'bike__bike_type', 'market')

        bikes_sold_count = sales_orders_this_month.count()

        # Calculate revenues directly from sales orders
        total_sales_revenue = Decimal('0')
        total_transport_costs = Decimal('0')

        # Create sales summary from sales orders
        sales_summary = {}
        for sale_order in sales_orders_this_month:
            bike_key = f"{sale_order.bike.bike_type.name} ({sale_order.bike.get_price_segment_display()})"

            if bike_key not in sales_summary:
                sales_summary[bike_key] = {'count': 0, 'revenue': 0, 'transport_cost': 0, 'net_revenue': 0}

            sales_summary[bike_key]['count'] += 1
            sales_summary[bike_key]['revenue'] += float(sale_order.sale_price)
            sales_summary[bike_key]['transport_cost'] += float(sale_order.transport_cost)
            sales_summary[bike_key]['net_revenue'] += float(sale_order.sale_price - sale_order.transport_cost)

            # Add to totals
            total_sales_revenue += sale_order.sale_price
            total_transport_costs += sale_order.transport_cost
        
        # PLANNED SALES DATA (sales orders created this month but not necessarily completed)
        planned_sales = SalesOrder.objects.filter(
            session=self.session,
            sale_month=current_month,
            sale_year=current_year
        )
        
        planned_sales_summary = {}
        for order in planned_sales:
            bike_key = f"{order.bike.bike_type.name} ({order.bike.get_price_segment_display()})"
            if bike_key not in planned_sales_summary:
                planned_sales_summary[bike_key] = {'count': 0, 'revenue': 0, 'transport_cost': 0, 'status': 'pending'}
            planned_sales_summary[bike_key]['count'] += 1
            planned_sales_summary[bike_key]['revenue'] += float(order.sale_price)
            planned_sales_summary[bike_key]['transport_cost'] += float(order.transport_cost)
            if order.is_completed:
                planned_sales_summary[bike_key]['status'] = 'completed'
        
        # Procurement data
        procurement_orders = ProcurementOrder.objects.filter(
            session=self.session,
            month=current_month,
            year=current_year,
            is_delivered=True
        )
        
        total_procurement_cost = sum(order.total_cost for order in procurement_orders)
        
        procurement_summary = {}
        for order in procurement_orders:
            for item in order.items.all():
                component_name = item.component.name
                if component_name not in procurement_summary:
                    procurement_summary[component_name] = {
                        'quantity': 0, 
                        'cost': 0, 
                        'supplier': order.supplier.name
                    }
                procurement_summary[component_name]['quantity'] += item.quantity_delivered
                procurement_summary[component_name]['cost'] += float(item.total_price)
        
        # Calculate profit/loss
        profit_loss = total_income - total_expenses
        
        # Get top transactions for detailed view
        top_transactions = []
        for transaction in transactions.order_by('-amount')[:10]:
            top_transactions.append({
                'type': transaction.transaction_type,
                'category': transaction.category,
                'amount': float(transaction.amount),
                'description': transaction.description
            })
        
        # Create or update monthly report
        monthly_report, created = MonthlyReport.objects.get_or_create(
            session=self.session,
            month=current_month,
            year=current_year,
            defaults={
                'opening_balance': opening_balance,
                'closing_balance': closing_balance,
                'total_income': total_income,
                'total_expenses': total_expenses,
                'bikes_produced_count': bikes_produced_count,
                'total_production_cost': total_production_cost,
                'production_summary': production_summary,
                'bikes_sold_count': bikes_sold_count,
                'total_sales_revenue': total_sales_revenue,
                'sales_summary': sales_summary,
                'total_procurement_cost': total_procurement_cost,
                'procurement_summary': procurement_summary,
                'profit_loss': profit_loss,
                'detailed_transactions': top_transactions
            }
        )
        
        # Store planned sales in the detailed_transactions field as additional data
        # We'll add it to the detailed transactions as a special entry
        if planned_sales_summary:
            top_transactions.append({
                'type': 'planned_sales_data',
                'category': 'Geplante Verkäufe',
                'amount': 0,
                'description': 'planned_sales_data',
                'planned_sales_summary': planned_sales_summary
            })
        
        # Update if already exists
        if not created:
            monthly_report.opening_balance = opening_balance
            monthly_report.closing_balance = closing_balance
            monthly_report.total_income = total_income
            monthly_report.total_expenses = total_expenses
            monthly_report.bikes_produced_count = bikes_produced_count
            monthly_report.total_production_cost = total_production_cost
            monthly_report.production_summary = production_summary
            monthly_report.bikes_sold_count = bikes_sold_count
            monthly_report.total_sales_revenue = total_sales_revenue
            monthly_report.sales_summary = sales_summary
            monthly_report.total_procurement_cost = total_procurement_cost
            monthly_report.procurement_summary = procurement_summary
            monthly_report.profit_loss = profit_loss
            monthly_report.detailed_transactions = top_transactions
            
        monthly_report.save()
            
        return monthly_report

    def get_dashboard_data(self):
        """Holt Dashboard-Daten"""
        from competitors.models import AICompetitor, CompetitorSale
        
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

        # Konkurrenten-Daten
        competitors = AICompetitor.objects.filter(session=self.session)
        recent_competitor_sales = CompetitorSale.objects.filter(
            competitor__session=self.session,
            month=self.session.current_month,
            year=self.session.current_year
        ).select_related('competitor', 'market', 'bike_type')[:10]

        # Market competition data
        market_competitions = MarketCompetition.objects.filter(
            session=self.session,
            month=self.session.current_month,
            year=self.session.current_year
        ).select_related('market', 'bike_type')[:10]
        
        # Calculate inventory aging summary
        aging_summary = self._get_inventory_aging_summary()

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
            'workers_list': workers,
            'competitors': competitors,
            'recent_competitor_sales': recent_competitor_sales,
            'market_competitions': market_competitions,
            'inventory_aging_summary': aging_summary
        }
    
    def _get_inventory_aging_summary(self):
        """Get summary of inventory aging for dashboard"""
        unsold_bikes = ProducedBike.objects.filter(
            session=self.session,
            is_sold=False
        )
        
        aging_buckets = {
            'new': 0,        # 0-1 months
            'aging': 0,      # 2-3 months
            'old': 0,        # 4-6 months
            'very_old': 0    # 7+ months
        }
        
        total_storage_cost = Decimal('0')
        
        for bike in unsold_bikes:
            total_storage_cost += bike.storage_cost_accumulated
            
            if bike.months_in_inventory <= 1:
                aging_buckets['new'] += 1
            elif bike.months_in_inventory <= 3:
                aging_buckets['aging'] += 1
            elif bike.months_in_inventory <= 6:
                aging_buckets['old'] += 1
            else:
                aging_buckets['very_old'] += 1
        
        return {
            'buckets': aging_buckets,
            'total_unsold': unsold_bikes.count(),
            'total_storage_cost': total_storage_cost
        }
