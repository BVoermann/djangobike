from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from .models import BankruptcyEvent
from sales.models import SalesOrder
from procurement.models import ProcurementOrder
from production.models import ProducedBike


class BankruptcyChecker:
    """Engine for detecting and handling bankruptcy situations"""
    
    def __init__(self, session, game_mode):
        self.session = session
        self.game_mode = game_mode
        self.bankruptcy_threshold = game_mode.bankruptcy_threshold
    
    def is_bankrupt(self):
        """Check if session is currently bankrupt"""
        return self.session.balance < self.bankruptcy_threshold
    
    def assess_bankruptcy_risk(self):
        """Assess the risk of bankruptcy and provide detailed analysis"""
        current_balance = self.session.balance
        
        # Calculate financial trends
        monthly_trends = self._calculate_monthly_trends()
        risk_factors = self._identify_risk_factors()
        
        # Determine risk level
        if current_balance < self.bankruptcy_threshold:
            risk_level = 'critical'
        else:
            distance_to_bankruptcy = current_balance - self.bankruptcy_threshold
            monthly_burn_rate = monthly_trends.get('avg_monthly_loss', 0)
            
            if monthly_burn_rate > 0:
                months_until_bankruptcy = distance_to_bankruptcy / monthly_burn_rate
                if months_until_bankruptcy <= 1:
                    risk_level = 'critical'
                elif months_until_bankruptcy <= 3:
                    risk_level = 'high'
                elif months_until_bankruptcy <= 6:
                    risk_level = 'medium'
                else:
                    risk_level = 'low'
            else:
                # No loss trend, assess based on distance
                if distance_to_bankruptcy < 5000:
                    risk_level = 'high'
                elif distance_to_bankruptcy < 15000:
                    risk_level = 'medium'
                elif distance_to_bankruptcy < 30000:
                    risk_level = 'low'
                else:
                    risk_level = 'minimal'
        
        # Generate recommendations
        recommendations = self._generate_recommendations(risk_factors, monthly_trends)
        
        return {
            'risk_level': risk_level,
            'current_balance': float(current_balance),
            'bankruptcy_threshold': float(self.bankruptcy_threshold),
            'distance_to_bankruptcy': float(current_balance - self.bankruptcy_threshold),
            'monthly_trends': monthly_trends,
            'risk_factors': risk_factors,
            'recommendations': recommendations,
            'months_until_bankruptcy': months_until_bankruptcy if 'months_until_bankruptcy' in locals() else None,
        }
    
    def trigger_bankruptcy(self, primary_cause=None):
        """Trigger bankruptcy event and elimination"""
        if self.session.bankruptcy_events.filter(player_eliminated=True).exists():
            return  # Already bankrupt
        
        # Analyze bankruptcy cause
        if not primary_cause:
            primary_cause = self._determine_bankruptcy_cause()
        
        contributing_factors = self._identify_contributing_factors()
        
        # Create bankruptcy event
        bankruptcy_event = BankruptcyEvent.objects.create(
            session=self.session,
            session_game_mode=getattr(self.session, 'game_mode_config', None),
            balance_at_bankruptcy=self.session.balance,
            bankruptcy_threshold=self.bankruptcy_threshold,
            trigger_month=self.session.current_month,
            trigger_year=self.session.current_year,
            primary_cause=primary_cause,
            contributing_factors=contributing_factors,
            player_eliminated=True,
            elimination_reason=self._generate_elimination_reason(primary_cause, contributing_factors)
        )
        
        # Mark session as inactive
        self.session.is_active = False
        self.session.save()
        
        # If there's a game mode, mark it as failed
        if hasattr(self.session, 'game_mode_config'):
            session_game_mode = self.session.game_mode_config
            if not session_game_mode.is_failed:
                session_game_mode.fail_game("Bankrott")
        
        return bankruptcy_event
    
    def _calculate_monthly_trends(self):
        """Calculate monthly financial trends"""
        # Get last 6 months of data
        current_month = self.session.current_month
        current_year = self.session.current_year
        
        monthly_data = []
        for i in range(6):
            month = current_month - i
            year = current_year
            
            if month <= 0:
                month += 12
                year -= 1
            
            # Calculate monthly revenue and costs
            monthly_revenue = SalesOrder.objects.filter(
                session=self.session,
                month=month,
                year=year
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            monthly_costs = ProcurementOrder.objects.filter(
                session=self.session,
                month=month,
                year=year
            ).aggregate(total=Sum('total_cost'))['total'] or 0
            
            net_income = monthly_revenue - monthly_costs
            
            monthly_data.append({
                'month': month,
                'year': year,
                'revenue': float(monthly_revenue),
                'costs': float(monthly_costs),
                'net_income': float(net_income)
            })
        
        # Calculate trends
        if len(monthly_data) >= 2:
            recent_losses = [data['net_income'] for data in monthly_data[:3] if data['net_income'] < 0]
            avg_monthly_loss = sum(recent_losses) / len(recent_losses) if recent_losses else 0
            
            revenue_trend = 'declining' if len(monthly_data) >= 3 and monthly_data[0]['revenue'] < monthly_data[2]['revenue'] else 'stable'
            cost_trend = 'increasing' if len(monthly_data) >= 3 and monthly_data[0]['costs'] > monthly_data[2]['costs'] else 'stable'
        else:
            avg_monthly_loss = 0
            revenue_trend = 'unknown'
            cost_trend = 'unknown'
        
        return {
            'monthly_data': monthly_data,
            'avg_monthly_loss': abs(avg_monthly_loss),
            'revenue_trend': revenue_trend,
            'cost_trend': cost_trend,
            'consecutive_losses': self._count_consecutive_losses(monthly_data)
        }
    
    def _identify_risk_factors(self):
        """Identify specific risk factors"""
        risk_factors = []
        
        # Low balance
        if self.session.balance < self.bankruptcy_threshold * 2:
            risk_factors.append({
                'factor': 'low_balance',
                'severity': 'high',
                'description': 'Kontostand ist gefährlich niedrig'
            })
        
        # No recent sales
        recent_sales = SalesOrder.objects.filter(
            session=self.session,
            month__gte=self.session.current_month - 2
        ).count()
        
        if recent_sales == 0:
            risk_factors.append({
                'factor': 'no_sales',
                'severity': 'high',
                'description': 'Keine Verkäufe in den letzten Monaten'
            })
        
        # High inventory with no sales
        total_bikes = ProducedBike.objects.filter(session=self.session).count()
        sold_bikes = SalesOrder.objects.filter(session=self.session).aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        unsold_bikes = total_bikes - sold_bikes
        if unsold_bikes > 20:
            risk_factors.append({
                'factor': 'excess_inventory',
                'severity': 'medium',
                'description': f'{unsold_bikes} unverkaufte Fahrräder im Lager'
            })
        
        # High monthly costs
        monthly_costs = ProcurementOrder.objects.filter(
            session=self.session,
            month=self.session.current_month,
            year=self.session.current_year
        ).aggregate(total=Sum('total_cost'))['total'] or 0
        
        if monthly_costs > self.session.balance * 0.5:
            risk_factors.append({
                'factor': 'high_costs',
                'severity': 'high',
                'description': 'Monatliche Ausgaben sind sehr hoch im Verhältnis zum Kontostand'
            })
        
        return risk_factors
    
    def _generate_recommendations(self, risk_factors, monthly_trends):
        """Generate specific recommendations to avoid bankruptcy"""
        recommendations = []
        
        for factor in risk_factors:
            if factor['factor'] == 'low_balance':
                recommendations.append("Sofortige Maßnahmen zur Liquiditätssteigerung erforderlich - verkaufen Sie Lagerbestände")
            elif factor['factor'] == 'no_sales':
                recommendations.append("Überprüfen Sie Ihre Preisgestaltung und Marktpositionierung")
            elif factor['factor'] == 'excess_inventory':
                recommendations.append("Reduzieren Sie die Produktion und konzentrieren Sie sich auf den Verkauf")
            elif factor['factor'] == 'high_costs':
                recommendations.append("Reduzieren Sie Ihre Ausgaben und überprüfen Sie Ihre Einkaufsstrategie")
        
        if monthly_trends['revenue_trend'] == 'declining':
            recommendations.append("Entwickeln Sie neue Verkaufsstrategien zur Umsatzsteigerung")
        
        if monthly_trends['cost_trend'] == 'increasing':
            recommendations.append("Optimieren Sie Ihre Kostenstruktur")
        
        if not recommendations:
            recommendations.append("Überwachen Sie weiterhin Ihre Finanzen und planen Sie vorausschauend")
        
        return recommendations
    
    def _determine_bankruptcy_cause(self):
        """Determine the primary cause of bankruptcy"""
        # Get recent financial data
        recent_revenue = SalesOrder.objects.filter(
            session=self.session,
            month__gte=self.session.current_month - 3
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        recent_costs = ProcurementOrder.objects.filter(
            session=self.session,
            month__gte=self.session.current_month - 3
        ).aggregate(total=Sum('total_cost'))['total'] or 0
        
        if recent_revenue == 0:
            return 'low_sales'
        elif recent_costs > recent_revenue * 2:
            return 'excessive_spending'
        elif recent_costs > 0 and recent_revenue / recent_costs < 0.5:
            return 'high_costs'
        else:
            return 'poor_planning'
    
    def _identify_contributing_factors(self):
        """Identify contributing factors to bankruptcy"""
        factors = []
        
        # Check production vs sales ratio
        total_produced = ProducedBike.objects.filter(session=self.session).count()
        total_sold = SalesOrder.objects.filter(session=self.session).aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        if total_produced > total_sold * 2:
            factors.append('overproduction')
        
        # Check if no sales in recent months
        recent_sales = SalesOrder.objects.filter(
            session=self.session,
            month__gte=self.session.current_month - 2
        ).count()
        
        if recent_sales == 0:
            factors.append('no_recent_sales')
        
        # Check for high procurement costs
        total_procurement = ProcurementOrder.objects.filter(session=self.session).aggregate(
            total=models.Sum('total_cost')
        )['total'] or 0
        
        if total_procurement > float(self.game_mode.starting_balance) * 1.5:
            factors.append('excessive_procurement')
        
        return factors
    
    def _generate_elimination_reason(self, primary_cause, contributing_factors):
        """Generate human-readable elimination reason"""
        cause_messages = {
            'excessive_spending': 'Übermäßige Ausgaben haben zur Insolvenz geführt',
            'low_sales': 'Unzureichende Verkäufe konnten die Kosten nicht decken',
            'high_costs': 'Zu hohe Produktionskosten im Verhältnis zum Umsatz',
            'poor_planning': 'Schlechte Finanzplanung führte zur Zahlungsunfähigkeit',
            'market_downturn': 'Markteinbruch führte zur Insolvenz',
            'external_event': 'Externe Ereignisse führten zur Zahlungsunfähigkeit',
        }
        
        base_message = cause_messages.get(primary_cause, 'Finanzielle Schwierigkeiten führten zur Insolvenz')
        
        if contributing_factors:
            factor_messages = {
                'overproduction': 'Überproduktion',
                'no_recent_sales': 'fehlende Verkäufe',
                'excessive_procurement': 'zu hohe Einkaufskosten'
            }
            
            factor_text = ', '.join([factor_messages.get(f, f) for f in contributing_factors])
            base_message += f". Beitragende Faktoren: {factor_text}"
        
        return base_message
    
    def _count_consecutive_losses(self, monthly_data):
        """Count consecutive months with losses"""
        consecutive = 0
        for month_data in monthly_data:
            if month_data['net_income'] < 0:
                consecutive += 1
            else:
                break
        return consecutive


def check_all_sessions_for_bankruptcy():
    """Utility function to check all active sessions for bankruptcy"""
    from bikeshop.models import GameSession
    from .models import SessionGameMode
    
    bankruptcies = []
    
    active_sessions = GameSession.objects.filter(is_active=True)
    
    for session in active_sessions:
        if hasattr(session, 'game_mode_config'):
            session_game_mode = session.game_mode_config
            checker = BankruptcyChecker(session, session_game_mode.game_mode)
            
            if checker.is_bankrupt():
                bankruptcy_event = checker.trigger_bankruptcy()
                bankruptcies.append(bankruptcy_event)
    
    return bankruptcies