"""
Event Factory - Creates predefined events and regulations for the game
"""
from decimal import Decimal
from .models import (
    EventCategory, RandomEvent, RegulationTimeline, EventChoice, 
    MarketOpportunity
)


def create_event_categories():
    """Create default event categories"""
    categories_data = [
        {
            'name': 'Product Innovation',
            'category_type': 'innovation',
            'description': 'New product technologies and innovations become available',
            'base_probability': 8.0,
        },
        {
            'name': 'Market Changes',
            'category_type': 'market',
            'description': 'Market demand shifts and new segments emerge',
            'base_probability': 12.0,
        },
        {
            'name': 'New Competition',
            'category_type': 'competition',
            'description': 'New competitors enter the market or existing ones change strategy',
            'base_probability': 10.0,
        },
        {
            'name': 'Promotional Opportunities',
            'category_type': 'promotion',
            'description': 'Special marketing and promotional opportunities',
            'base_probability': 15.0,
        },
        {
            'name': 'Supply Chain Issues',
            'category_type': 'supply_chain',
            'description': 'Disruptions or changes in the supply chain',
            'base_probability': 8.0,
        },
        {
            'name': 'Regulatory Changes',
            'category_type': 'regulatory',
            'description': 'New regulations and policy changes',
            'base_probability': 6.0,
        },
        {
            'name': 'Economic Events',
            'category_type': 'economic',
            'description': 'Economic conditions affecting the business',
            'base_probability': 10.0,
        },
        {
            'name': 'Environmental Events',
            'category_type': 'environmental',
            'description': 'Environmental factors affecting business',
            'base_probability': 7.0,
        },
        {
            'name': 'Technology Breakthroughs',
            'category_type': 'technology',
            'description': 'Major technological advances',
            'base_probability': 5.0,
        },
        {
            'name': 'Crisis Events',
            'category_type': 'crisis',
            'description': 'Unexpected crisis situations',
            'base_probability': 4.0,
        },
    ]
    
    created_categories = []
    for cat_data in categories_data:
        category, created = EventCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults=cat_data
        )
        created_categories.append(category)
    
    return created_categories


def create_innovation_events():
    """Create product innovation events"""
    try:
        innovation_category = EventCategory.objects.get(category_type='innovation')
    except EventCategory.DoesNotExist:
        return []
    
    events_data = [
        {
            'title': 'Revolutionary Battery Technology',
            'description': 'A breakthrough in battery technology offers significantly improved range and charging speed for e-bikes.',
            'detailed_description': 'New lithium-silicon batteries provide 2x range and 5x faster charging. This technology could revolutionize the e-bike market.',
            'severity': 'major',
            'duration_type': 'permanent',
            'probability_weight': 1.5,
            'min_game_month': 6,
            'production_effects': {
                'unlocks_component': 'Advanced Battery System',
                'efficiency_modifier': 1.1,
                'quality_modifier': 1.15
            },
            'market_effects': {
                'demand_modifier': 1.25,
                'creates_opportunities': [
                    {
                        'title': 'Premium E-Bike Market Entry',
                        'type': 'new_segment',
                        'description': 'Advanced battery technology opens premium e-bike segment',
                        'duration': 12,
                        'required_investment': 50000,
                        'potential_revenue': 200000,
                        'required_capabilities': ['advanced_battery_research']
                    }
                ]
            }
        },
        {
            'title': 'Smart Bike Technology Platform',
            'description': 'A new IoT platform allows bikes to be connected, tracked, and remotely monitored.',
            'detailed_description': 'Integration with smartphones, GPS tracking, theft protection, and performance monitoring.',
            'severity': 'moderate',
            'duration_type': 'permanent',
            'probability_weight': 1.2,
            'min_game_month': 4,
            'production_effects': {
                'unlocks_component': 'Smart Control System',
                'quality_modifier': 1.1
            },
            'market_effects': {
                'demand_modifier': 1.15,
                'price_modifier': 1.1
            }
        },
        {
            'title': 'Carbon Fiber Manufacturing Breakthrough',
            'description': 'New manufacturing techniques make carbon fiber frames more affordable and accessible.',
            'detailed_description': 'Automated carbon fiber laying reduces production costs by 40% while maintaining quality.',
            'severity': 'moderate',
            'duration_type': 'permanent',
            'probability_weight': 1.0,
            'min_game_month': 8,
            'production_effects': {
                'cost_modifier': 0.85,
                'quality_modifier': 1.05,
                'unlocks_component': 'Advanced Carbon Frame'
            }
        },
        {
            'title': 'Modular Bike Design System',
            'description': 'A new modular design system allows customers to easily customize and upgrade their bikes.',
            'detailed_description': 'Standardized connection systems enable easy swapping of components and personalization.',
            'severity': 'major',
            'duration_type': 'permanent',
            'probability_weight': 0.8,
            'min_game_month': 10,
            'production_effects': {
                'efficiency_modifier': 1.2,
                'unlocks_feature': 'modular_customization'
            },
            'market_effects': {
                'demand_modifier': 1.3,
                'price_modifier': 1.2,
                'new_segments': ['customization_enthusiasts']
            }
        }
    ]
    
    created_events = []
    for event_data in events_data:
        event = RandomEvent.objects.create(
            category=innovation_category,
            **event_data
        )
        created_events.append(event)
    
    return created_events


def create_market_events():
    """Create market change events"""
    try:
        market_category = EventCategory.objects.get(category_type='market')
    except EventCategory.DoesNotExist:
        return []
    
    events_data = [
        {
            'title': 'Urban Mobility Initiative',
            'description': 'City governments launch major bike-friendly infrastructure projects.',
            'detailed_description': 'New bike lanes, parking facilities, and traffic priority for cyclists boost urban bike demand.',
            'severity': 'major',
            'duration_type': 'medium_term',
            'probability_weight': 1.3,
            'min_game_month': 3,
            'market_effects': {
                'demand_modifier': 1.4,
                'segment_boosts': {
                    'city_bikes': 1.6,
                    'e_bikes': 1.5
                }
            }
        },
        {
            'title': 'Bike Tourism Boom',
            'description': 'Growing interest in cycle tourism creates new market opportunities.',
            'detailed_description': 'Tourists increasingly choose cycling holidays, boosting demand for touring and rental bikes.',
            'severity': 'moderate',
            'duration_type': 'medium_term',
            'probability_weight': 1.0,
            'min_game_month': 2,
            'market_effects': {
                'demand_modifier': 1.2,
                'creates_opportunities': [
                    {
                        'title': 'Tourist Bike Rental Partnership',
                        'type': 'partnership',
                        'description': 'Partner with hotels and tour operators for bike rentals',
                        'duration': 8,
                        'required_investment': 25000,
                        'potential_revenue': 100000
                    }
                ]
            }
        },
        {
            'title': 'Health & Fitness Trend',
            'description': 'Increased focus on health and fitness drives bike sales.',
            'detailed_description': 'Post-pandemic health consciousness and fitness trends boost recreational bike demand.',
            'severity': 'moderate',
            'duration_type': 'medium_term',
            'probability_weight': 1.5,
            'min_game_month': 1,
            'market_effects': {
                'demand_modifier': 1.25,
                'segment_boosts': {
                    'mountain_bikes': 1.3,
                    'fitness_bikes': 1.4
                }
            }
        },
        {
            'title': 'Corporate Bike Programs',
            'description': 'Companies adopt bike-to-work programs for employees.',
            'detailed_description': 'Corporate sustainability initiatives include providing bikes for employee commuting.',
            'severity': 'moderate',
            'duration_type': 'permanent',
            'probability_weight': 1.1,
            'min_game_month': 6,
            'market_effects': {
                'creates_opportunities': [
                    {
                        'title': 'Corporate Fleet Contract',
                        'type': 'bulk_order',
                        'description': 'Supply bikes for corporate employee programs',
                        'duration': 4,
                        'required_investment': 15000,
                        'potential_revenue': 150000,
                        'required_capabilities': ['fleet_management']
                    }
                ]
            }
        }
    ]
    
    created_events = []
    for event_data in events_data:
        event = RandomEvent.objects.create(
            category=market_category,
            **event_data
        )
        created_events.append(event)
    
    return created_events


def create_supply_chain_events():
    """Create supply chain disruption events"""
    try:
        supply_category = EventCategory.objects.get(category_type='supply_chain')
    except EventCategory.DoesNotExist:
        return []
    
    events_data = [
        {
            'title': 'Global Semiconductor Shortage',
            'description': 'Worldwide chip shortage affects e-bike control systems and displays.',
            'detailed_description': 'Limited availability of microcontrollers and displays increases costs and delays.',
            'severity': 'major',
            'duration_type': 'medium_term',
            'probability_weight': 2.0,
            'min_game_month': 3,
            'production_effects': {
                'cost_modifier': 1.3,
                'component_availability': {
                    'electronic_components': 0.7
                }
            },
            'financial_effects': {
                'monthly_cost': 2000
            }
        },
        {
            'title': 'Aluminum Price Surge',
            'description': 'Global aluminum prices increase dramatically due to trade tensions.',
            'detailed_description': 'Raw material costs for frames and components increase by 40-60%.',
            'severity': 'moderate',
            'duration_type': 'temporary',
            'probability_weight': 1.5,
            'min_game_month': 1,
            'production_effects': {
                'cost_modifier': 1.4,
                'affected_components': ['aluminum_frames', 'aluminum_parts']
            }
        },
        {
            'title': 'Shipping Container Crisis',
            'description': 'Global shipping delays affect component deliveries.',
            'detailed_description': 'Port congestion and container shortages cause 2-4 week delays in component deliveries.',
            'severity': 'moderate',
            'duration_type': 'temporary',
            'probability_weight': 1.8,
            'min_game_month': 2,
            'production_effects': {
                'delivery_delays': 2,
                'planning_difficulty': 1.5
            }
        },
        {
            'title': 'Quality Issues at Major Supplier',
            'description': 'A major component supplier faces quality control problems.',
            'detailed_description': 'Defect rates increase and some component batches need to be recalled.',
            'severity': 'moderate',
            'duration_type': 'temporary',
            'probability_weight': 1.2,
            'min_game_month': 4,
            'production_effects': {
                'quality_modifier': 0.9,
                'defect_rate_increase': 0.15
            },
            'financial_effects': {
                'one_time_cost': 8000
            }
        }
    ]
    
    created_events = []
    for event_data in events_data:
        event = RandomEvent.objects.create(
            category=supply_category,
            **event_data
        )
        created_events.append(event)
    
    return created_events


def create_promotional_events():
    """Create promotional opportunity events"""
    try:
        promo_category = EventCategory.objects.get(category_type='promotion')
    except EventCategory.DoesNotExist:
        return []
    
    events_data = [
        {
            'title': 'Major Cycling Event Sponsorship',
            'description': 'Opportunity to sponsor a major cycling race or event.',
            'detailed_description': 'High-visibility sponsorship opportunity with significant marketing impact.',
            'severity': 'moderate',
            'duration_type': 'instant',
            'probability_weight': 1.0,
            'min_game_month': 3,
            'requires_session_balance_min': Decimal('20000'),
        },
        {
            'title': 'Celebrity Endorsement Opportunity',
            'description': 'A celebrity cyclist offers to endorse your bikes.',
            'detailed_description': 'High-profile athlete willing to use and promote your bikes in exchange for sponsorship.',
            'severity': 'major',
            'duration_type': 'medium_term',
            'probability_weight': 0.7,
            'min_game_month': 6,
            'requires_session_balance_min': Decimal('50000'),
            'market_effects': {
                'demand_modifier': 1.3,
                'brand_recognition_boost': 25
            }
        },
        {
            'title': 'Government Green Transportation Grant',
            'description': 'Government offers grants for sustainable transportation companies.',
            'detailed_description': 'Financial incentives for companies promoting eco-friendly transportation solutions.',
            'severity': 'moderate',
            'duration_type': 'instant',
            'probability_weight': 1.5,
            'min_game_month': 4,
            'financial_effects': {
                'one_time_income': 15000
            }
        },
        {
            'title': 'Trade Fair Premium Booth Offer',
            'description': 'Opportunity to get premium booth space at major bike trade fair.',
            'detailed_description': 'Last-minute cancellation opens up prime exhibition space at reduced rate.',
            'severity': 'minor',
            'duration_type': 'instant',
            'probability_weight': 2.0,
            'min_game_month': 2,
            'requires_session_balance_min': Decimal('10000'),
            'market_effects': {
                'demand_modifier': 1.15,
                'brand_recognition_boost': 10
            }
        }
    ]
    
    created_events = []
    for event_data in events_data:
        event = RandomEvent.objects.create(
            category=promo_category,
            **event_data
        )
        
        # Create choices for events that require player decisions
        if 'sponsorship' in event_data['title'].lower() or 'endorsement' in event_data['title'].lower():
            create_event_choices(event, event_data)
        
        created_events.append(event)
    
    return created_events


def create_event_choices(event, event_data):
    """Create multiple choice options for decision events"""
    if 'Sponsorship' in event.title:
        choices_data = [
            {
                'choice_text': 'Accept sponsorship deal',
                'description': 'Pay sponsorship fee for marketing benefits',
                'financial_effects': {'one_time_cost': 20000},
                'market_effects': {'demand_modifier': 1.2, 'brand_recognition_boost': 15},
                'required_balance': Decimal('20000'),
                'order': 1
            },
            {
                'choice_text': 'Decline sponsorship',
                'description': 'Skip this opportunity to preserve cash',
                'financial_effects': {},
                'market_effects': {},
                'is_default': True,
                'order': 2
            }
        ]
    elif 'Endorsement' in event.title:
        choices_data = [
            {
                'choice_text': 'Sign endorsement deal',
                'description': 'Pay celebrity endorsement fee',
                'financial_effects': {'one_time_cost': 50000, 'monthly_cost': 5000},
                'market_effects': {'demand_modifier': 1.3, 'brand_recognition_boost': 25},
                'required_balance': Decimal('50000'),
                'order': 1
            },
            {
                'choice_text': 'Negotiate smaller deal',
                'description': 'Try to negotiate a more affordable arrangement',
                'financial_effects': {'one_time_cost': 25000, 'monthly_cost': 2500},
                'market_effects': {'demand_modifier': 1.15, 'brand_recognition_boost': 12},
                'required_balance': Decimal('25000'),
                'order': 2
            },
            {
                'choice_text': 'Decline endorsement',
                'description': 'Pass on this opportunity',
                'financial_effects': {},
                'market_effects': {},
                'is_default': True,
                'order': 3
            }
        ]
    else:
        return
    
    for choice_data in choices_data:
        EventChoice.objects.create(
            event=event,
            **choice_data
        )


def create_regulation_timeline():
    """Create predefined regulatory changes with realistic timelines"""
    regulations_data = [
        {
            'title': 'Old E-Bike Motor Ban',
            'description': 'Older generation brushed motors will be banned due to efficiency and noise regulations.',
            'regulation_type': 'component_ban',
            'announcement_month': 6,
            'announcement_year': 2025,
            'implementation_month': 1,
            'implementation_year': 2027,
            'restrictions': {
                'banned_components': ['Bürstenmotor 250W Alt', 'Bürstenmotor 350W Alt'],
                'reason': 'Noise and efficiency standards'
            },
            'compliance_requirements': {
                'required_actions': ['Replace motors in inventory', 'Update supplier contracts'],
                'grace_period_months': 18
            },
            'penalties': {
                'base_penalty': 5000,
                'monthly_penalty_rate': 0.02
            }
        },
        {
            'title': 'Enhanced E-Bike Safety Standards',
            'description': 'New safety standards require additional testing and certification for e-bikes.',
            'regulation_type': 'certification_requirement',
            'announcement_month': 3,
            'announcement_year': 2025,
            'implementation_month': 9,
            'implementation_year': 2025,
            'restrictions': {
                'required_certifications': ['Enhanced Safety Certificate'],
                'affected_products': ['All e-bikes']
            },
            'compliance_requirements': {
                'certification_cost': 15000,
                'annual_renewal': 5000,
                'testing_requirements': 'Third-party safety testing'
            },
            'penalties': {
                'base_penalty': 10000,
                'sales_ban': True
            },
            'benefits': {
                'compliance_bonus': 2000,
                'market_trust_bonus': 1.1
            }
        },
        {
            'title': 'Carbon Emissions Reduction Mandate',
            'description': 'Companies must achieve specific carbon emission reduction targets.',
            'regulation_type': 'environmental_standard',
            'announcement_month': 1,
            'announcement_year': 2026,
            'implementation_month': 1,
            'implementation_year': 2027,
            'restrictions': {
                'max_carbon_footprint': 500,  # kg CO2 equivalent per bike
                'reporting_required': True
            },
            'compliance_requirements': {
                'min_sustainability_score': 70,
                'carbon_offset_option': True,
                'offset_cost_per_kg': 50
            },
            'penalties': {
                'base_penalty': 15000,
                'escalating_penalty': True
            },
            'benefits': {
                'green_subsidy': 5000,
                'tax_reduction': 0.05
            }
        },
        {
            'title': 'Lithium Battery Recycling Law',
            'description': 'Manufacturers must take responsibility for battery recycling and disposal.',
            'regulation_type': 'environmental_standard',
            'announcement_month': 9,
            'announcement_year': 2025,
            'implementation_month': 3,
            'implementation_year': 2026,
            'restrictions': {
                'recycling_responsibility': True,
                'deposit_per_battery': 25
            },
            'compliance_requirements': {
                'recycling_program': True,
                'collection_network': True,
                'monthly_recycling_fee': 500
            },
            'penalties': {
                'base_penalty': 8000,
                'per_battery_fine': 100
            }
        },
        {
            'title': 'Anti-Dumping Tariff on Foreign Components',
            'description': 'New tariffs on imported components to protect domestic manufacturers.',
            'regulation_type': 'trade_restriction',
            'announcement_month': 12,
            'announcement_year': 2025,
            'implementation_month': 6,
            'implementation_year': 2026,
            'expiration_month': 6,
            'expiration_year': 2028,
            'restrictions': {
                'import_tariff': 0.25,  # 25% tariff
                'affected_regions': ['Asia'],
                'affected_components': ['Frames', 'Motors', 'Batteries']
            },
            'compliance_requirements': {
                'domestic_content_minimum': 0.6  # 60% domestic content
            }
        }
    ]
    
    created_regulations = []
    for reg_data in regulations_data:
        regulation = RegulationTimeline.objects.create(**reg_data)
        created_regulations.append(regulation)
    
    return created_regulations


def create_crisis_events():
    """Create crisis events that can disrupt business"""
    try:
        crisis_category = EventCategory.objects.get(category_type='crisis')
    except EventCategory.DoesNotExist:
        return []
    
    events_data = [
        {
            'title': 'Factory Fire',
            'description': 'A fire at a major supplier disrupts component deliveries.',
            'detailed_description': 'Factory fire halts production for several months, creating severe supply shortages.',
            'severity': 'critical',
            'duration_type': 'medium_term',
            'probability_weight': 0.5,
            'min_game_month': 6,
            'production_effects': {
                'component_availability': {
                    'affected_supplier': 0.3
                },
                'cost_modifier': 1.6
            },
            'financial_effects': {
                'one_time_cost': 15000
            }
        },
        {
            'title': 'Economic Recession',
            'description': 'Economic downturn reduces consumer spending on bicycles.',
            'detailed_description': 'Reduced disposable income causes significant drop in bike sales across all segments.',
            'severity': 'major',
            'duration_type': 'medium_term',
            'probability_weight': 0.8,
            'min_game_month': 12,
            'market_effects': {
                'demand_modifier': 0.7,
                'price_sensitivity_increase': 1.5
            }
        },
        {
            'title': 'Cyber Attack on Suppliers',
            'description': 'Ransomware attack affects multiple suppliers\' systems.',
            'detailed_description': 'IT systems disruption causes ordering and delivery delays across the supply chain.',
            'severity': 'moderate',
            'duration_type': 'temporary',
            'probability_weight': 1.0,
            'min_game_month': 8,
            'production_effects': {
                'delivery_delays': 4,
                'planning_difficulty': 2.0
            },
            'financial_effects': {
                'one_time_cost': 10000
            }
        }
    ]
    
    created_events = []
    for event_data in events_data:
        event = RandomEvent.objects.create(
            category=crisis_category,
            **event_data
        )
        created_events.append(event)
    
    return created_events


def initialize_all_events_and_regulations():
    """Initialize all predefined events and regulations"""
    results = {
        'categories': create_event_categories(),
        'innovation_events': create_innovation_events(),
        'market_events': create_market_events(),
        'supply_chain_events': create_supply_chain_events(),
        'promotional_events': create_promotional_events(),
        'crisis_events': create_crisis_events(),
        'regulations': create_regulation_timeline(),
    }
    
    return results