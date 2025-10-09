from decimal import Decimal
from django.utils import timezone
from .models import SessionGameMode, GameResult


class VictoryChecker:
    """Engine for checking victory conditions and managing game completion"""
    
    def __init__(self, session_game_mode):
        self.session_game_mode = session_game_mode
        self.session = session_game_mode.session
        self.game_mode = session_game_mode.game_mode
    
    def check_all_conditions(self):
        """Check all victory and failure conditions"""
        if self.session_game_mode.is_completed or self.session_game_mode.is_failed:
            return  # Game already ended
        
        # Check time limit
        if self._check_time_limit():
            return
        
        # Check bankruptcy
        if self._check_bankruptcy():
            return
        
        # Check failure conditions
        if self._check_failure_conditions():
            return
        
        # Check victory conditions
        self._check_victory_conditions()
    
    def _check_time_limit(self):
        """Check if game time limit is exceeded"""
        if self.session.current_month > self.game_mode.duration_months:
            self.session_game_mode.complete_game()
            return True
        return False
    
    def _check_bankruptcy(self):
        """Check for bankruptcy condition"""
        if self.session.balance < self.game_mode.bankruptcy_threshold:
            self._trigger_bankruptcy_failure()
            return True
        return False
    
    def _check_failure_conditions(self):
        """Check all failure conditions"""
        failure_objectives = self.game_mode.objectives.filter(
            is_failure_condition=True, 
            is_active=True
        )
        
        for objective in failure_objectives:
            if not objective.evaluate(self.session):
                self.session_game_mode.fail_game(f"Fehlschlag bei: {objective.name}")
                return True
        
        return False
    
    def _check_victory_conditions(self):
        """Check victory conditions"""
        # Strategy 1: All primary objectives must be met
        primary_objectives = self.game_mode.objectives.filter(
            is_primary=True, 
            is_active=True
        )
        
        if primary_objectives.exists():
            all_primary_met = all(obj.evaluate(self.session) for obj in primary_objectives)
            if all_primary_met:
                self.session_game_mode.complete_game()
                return True
        
        # Strategy 2: Score-based victory (if configured)
        if self._check_score_based_victory():
            return True
        
        # Strategy 3: Time-based with minimum requirements
        if self._check_time_based_victory():
            return True
        
        return False
    
    def _check_score_based_victory(self):
        """Check for score-based victory conditions"""
        victory_conditions = self.game_mode.victory_conditions
        
        if 'min_score' in victory_conditions:
            current_score = float(self.session_game_mode.calculate_final_score())
            min_score = victory_conditions['min_score']
            
            if current_score >= min_score:
                self.session_game_mode.complete_game()
                return True
        
        return False
    
    def _check_time_based_victory(self):
        """Check for time-based victory with minimum requirements"""
        victory_conditions = self.game_mode.victory_conditions
        
        # Only check if we're at or near the end of the game
        months_remaining = self.game_mode.duration_months - self.session.current_month
        
        if months_remaining <= 3:  # Last 3 months
            if 'min_completion_percentage' in victory_conditions:
                completion_pct = float(self.session_game_mode.calculate_completion_percentage())
                min_completion = victory_conditions['min_completion_percentage']
                
                if completion_pct >= min_completion:
                    self.session_game_mode.complete_game()
                    return True
        
        return False
    
    def _trigger_bankruptcy_failure(self):
        """Handle bankruptcy-specific failure"""
        from .bankruptcy_engine import BankruptcyChecker
        
        # Create bankruptcy event
        bankruptcy_checker = BankruptcyChecker(self.session, self.game_mode)
        bankruptcy_event = bankruptcy_checker.trigger_bankruptcy()
        
        # Fail the game
        self.session_game_mode.fail_game("Bankrott")
    
    def get_victory_progress(self):
        """Get detailed progress towards victory"""
        progress_data = {
            'primary_objectives': [],
            'secondary_objectives': [],
            'failure_risks': [],
            'time_remaining': max(0, self.game_mode.duration_months - self.session.current_month),
            'overall_progress': float(self.session_game_mode.calculate_completion_percentage()),
            'current_score': float(self.session_game_mode.calculate_final_score()),
        }
        
        # Analyze primary objectives
        primary_objectives = self.game_mode.objectives.filter(
            is_primary=True, 
            is_active=True
        )
        
        for objective in primary_objectives:
            current_value = objective.get_current_value(self.session)
            target_value = float(objective.target_value)
            is_met = objective.evaluate(self.session)
            
            progress_pct = min((current_value / target_value) * 100, 200) if target_value > 0 else (100 if is_met else 0)
            
            progress_data['primary_objectives'].append({
                'name': objective.name,
                'description': objective.description,
                'current_value': current_value,
                'target_value': target_value,
                'is_met': is_met,
                'progress_percentage': progress_pct,
                'difficulty': self._assess_objective_difficulty(objective)
            })
        
        # Analyze secondary objectives
        secondary_objectives = self.game_mode.objectives.filter(
            is_primary=False, 
            is_failure_condition=False,
            is_active=True
        )
        
        for objective in secondary_objectives:
            current_value = objective.get_current_value(self.session)
            target_value = float(objective.target_value)
            is_met = objective.evaluate(self.session)
            
            progress_pct = min((current_value / target_value) * 100, 200) if target_value > 0 else (100 if is_met else 0)
            
            progress_data['secondary_objectives'].append({
                'name': objective.name,
                'current_value': current_value,
                'target_value': target_value,
                'is_met': is_met,
                'progress_percentage': progress_pct,
                'weight': float(objective.weight)
            })
        
        # Check failure risks
        failure_objectives = self.game_mode.objectives.filter(
            is_failure_condition=True,
            is_active=True
        )
        
        for objective in failure_objectives:
            current_value = objective.get_current_value(self.session)
            target_value = float(objective.target_value)
            is_violated = not objective.evaluate(self.session)
            
            if is_violated or self._is_at_risk(objective):
                progress_data['failure_risks'].append({
                    'name': objective.name,
                    'description': objective.description,
                    'current_value': current_value,
                    'target_value': target_value,
                    'is_violated': is_violated,
                    'risk_level': self._assess_failure_risk(objective)
                })
        
        # Check bankruptcy risk
        bankruptcy_risk = self._assess_bankruptcy_risk()
        if bankruptcy_risk['level'] != 'minimal':
            progress_data['failure_risks'].append({
                'name': 'Bankrott-Risiko',
                'description': 'Gefahr der Zahlungsunfähigkeit',
                'current_value': float(self.session.balance),
                'target_value': float(self.game_mode.bankruptcy_threshold),
                'is_violated': self.session.balance < self.game_mode.bankruptcy_threshold,
                'risk_level': bankruptcy_risk['level']
            })
        
        return progress_data
    
    def _assess_objective_difficulty(self, objective):
        """Assess how difficult it will be to achieve an objective"""
        current_value = objective.get_current_value(self.session)
        target_value = float(objective.target_value)
        
        if target_value <= 0:
            return 'unknown'
        
        progress_ratio = current_value / target_value
        months_remaining = self.game_mode.duration_months - self.session.current_month
        
        if progress_ratio >= 1.0:
            return 'achieved'
        elif progress_ratio >= 0.8:
            return 'easy'
        elif progress_ratio >= 0.5:
            return 'moderate'
        elif progress_ratio >= 0.2 and months_remaining > 6:
            return 'challenging'
        else:
            return 'difficult'
    
    def _is_at_risk(self, objective):
        """Check if objective is at risk of being violated"""
        current_value = objective.get_current_value(self.session)
        target_value = float(objective.target_value)
        
        # For objectives that must stay above a threshold
        if objective.comparison_operator in ['gte', 'gt']:
            buffer_zone = target_value * 0.2  # 20% buffer
            return current_value < (target_value + buffer_zone)
        
        # For objectives that must stay below a threshold
        elif objective.comparison_operator in ['lte', 'lt']:
            buffer_zone = target_value * 0.2
            return current_value > (target_value - buffer_zone)
        
        return False
    
    def _assess_failure_risk(self, objective):
        """Assess the risk level for a failure condition"""
        if not objective.evaluate(self.session):
            return 'critical'
        
        if self._is_at_risk(objective):
            return 'high'
        
        return 'low'
    
    def _assess_bankruptcy_risk(self):
        """Quick bankruptcy risk assessment"""
        from .bankruptcy_engine import BankruptcyChecker
        
        bankruptcy_checker = BankruptcyChecker(self.session, self.game_mode)
        risk_assessment = bankruptcy_checker.assess_bankruptcy_risk()
        
        return {
            'level': risk_assessment['risk_level'],
            'distance': risk_assessment['distance_to_bankruptcy']
        }
    
    def get_recommendations(self):
        """Get strategic recommendations for achieving victory"""
        recommendations = []
        
        # Check primary objectives that are not met
        primary_objectives = self.game_mode.objectives.filter(
            is_primary=True,
            is_active=True
        )
        
        unmet_primary = [obj for obj in primary_objectives if not obj.evaluate(self.session)]
        
        for objective in unmet_primary:
            rec = self._get_objective_recommendation(objective)
            if rec:
                recommendations.append(rec)
        
        # Check for failure risks
        failure_objectives = self.game_mode.objectives.filter(
            is_failure_condition=True,
            is_active=True
        )
        
        for objective in failure_objectives:
            if self._is_at_risk(objective):
                rec = self._get_risk_mitigation_recommendation(objective)
                if rec:
                    recommendations.append(rec)
        
        # General strategic recommendations
        months_remaining = self.game_mode.duration_months - self.session.current_month
        if months_remaining <= 6:
            recommendations.append({
                'type': 'time_pressure',
                'priority': 'high',
                'title': 'Zeitdruck',
                'description': f'Nur noch {months_remaining} Monate - konzentrieren Sie sich auf die wichtigsten Ziele.'
            })
        
        return recommendations
    
    def _get_objective_recommendation(self, objective):
        """Get specific recommendation for achieving an objective"""
        recommendations_map = {
            'profit_total': {
                'title': 'Gewinn steigern',
                'description': 'Erhöhen Sie Verkaufspreise oder reduzieren Sie Kosten. Fokus auf profitable Produktlinien.'
            },
            'market_share': {
                'title': 'Marktanteil ausbauen',
                'description': 'Verstärken Sie Marketing und Verkaufsaktivitäten. Überprüfen Sie Ihre Preispositionierung.'
            },
            'bikes_sold': {
                'title': 'Verkäufe steigern',
                'description': 'Erhöhen Sie Produktionskapazitäten und optimieren Sie Ihre Verkaufsstrategie.'
            },
            'quality_rating': {
                'title': 'Qualität verbessern',
                'description': 'Investieren Sie in bessere Komponenten und optimieren Sie Produktionsprozesse.'
            },
            'balance_minimum': {
                'title': 'Liquidität sichern',
                'description': 'Reduzieren Sie Ausgaben und steigern Sie kurzfristige Verkäufe.'
            }
        }
        
        template = recommendations_map.get(objective.objective_type)
        if template:
            return {
                'type': 'objective',
                'priority': 'high' if objective.is_primary else 'medium',
                'objective_name': objective.name,
                'title': template['title'],
                'description': template['description']
            }
        
        return None
    
    def _get_risk_mitigation_recommendation(self, objective):
        """Get recommendation for mitigating failure risk"""
        return {
            'type': 'risk_mitigation',
            'priority': 'critical',
            'objective_name': objective.name,
            'title': f'Risiko: {objective.name}',
            'description': f'Sofortige Maßnahmen erforderlich - {objective.description}'
        }