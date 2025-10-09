from django.core.management.base import BaseCommand
from help_system.models import HelpCategory, TutorialVideo, InteractiveGuide, TooltipHelp, ContextualHelp


class Command(BaseCommand):
    help = 'Create sample help content for the bike shop simulation'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample help content...')
        
        # Create categories
        categories = self.create_categories()
        
        # Create tutorial videos
        self.create_tutorial_videos(categories)
        
        # Create interactive guides
        self.create_interactive_guides(categories)
        
        # Create tooltips
        self.create_tooltips(categories)
        
        # Create contextual help
        self.create_contextual_help(categories)
        
        self.stdout.write(self.style.SUCCESS('Successfully created sample help content'))

    def create_categories(self):
        self.stdout.write('Creating help categories...')
        
        categories_data = [
            {
                'name': 'Grundlagen',
                'category_type': 'basics',
                'description': 'Grundlegende Konzepte und erste Schritte im Fahrradgeschäft-Simulator',
                'icon': 'fas fa-graduation-cap',
                'order': 1
            },
            {
                'name': 'Einkauf & Beschaffung',
                'category_type': 'procurement',
                'description': 'Alles über den Einkauf von Fahrradteilen und Lieferantenverwaltung',
                'icon': 'fas fa-shopping-cart',
                'order': 2
            },
            {
                'name': 'Produktion',
                'category_type': 'production',
                'description': 'Fahrradproduktion, Qualitätskontrolle und Produktionsplanung',
                'icon': 'fas fa-cogs',
                'order': 3
            },
            {
                'name': 'Verkauf & Marketing',
                'category_type': 'sales',
                'description': 'Verkaufsstrategien, Preisgestaltung und Marktanalyse',
                'icon': 'fas fa-chart-line',
                'order': 4
            },
            {
                'name': 'Finanzen',
                'category_type': 'finance',
                'description': 'Finanzmanagement, Budgetierung und Berichtswesen',
                'icon': 'fas fa-euro-sign',
                'order': 5
            },
            {
                'name': 'Lagerverwaltung',
                'category_type': 'warehouse',
                'description': 'Lagerbestandsmanagement und Logistik',
                'icon': 'fas fa-warehouse',
                'order': 6
            },
            {
                'name': 'Strategisches Management',
                'category_type': 'strategy',
                'description': 'Langfristige Planung und strategische Entscheidungen',
                'icon': 'fas fa-chess',
                'order': 7
            }
        ]
        
        categories = {}
        for data in categories_data:
            category, created = HelpCategory.objects.get_or_create(
                category_type=data['category_type'],
                defaults=data
            )
            categories[data['category_type']] = category
            if created:
                self.stdout.write(f'  Created category: {category.name}')
        
        return categories

    def create_tutorial_videos(self, categories):
        self.stdout.write('Creating tutorial videos...')
        
        videos_data = [
            {
                'title': 'Willkommen im BikeShop Simulator',
                'description': 'Eine Einführung in die Grundlagen des Simulators und erste Schritte',
                'category': categories['basics'],
                'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                'duration_minutes': 5,
                'difficulty_level': 'beginner',
                'learning_objectives': 'Nach diesem Video verstehen Sie:\n- Die Benutzeroberfläche des Simulators\n- Grundlegende Navigation\n- Wie Sie eine neue Spielsession starten',
                'tags': 'einführung, grundlagen, navigation',
                'is_featured': True,
                'order': 1
            },
            {
                'title': 'Einkauf von Fahrradteilen',
                'description': 'Lernen Sie, wie Sie Fahrradteile von Lieferanten bestellen und Ihr Lager verwalten',
                'category': categories['procurement'],
                'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                'duration_minutes': 8,
                'difficulty_level': 'beginner',
                'prerequisites': 'Grundkenntnisse der Simulator-Oberfläche',
                'learning_objectives': 'Nach diesem Video können Sie:\n- Lieferanten auswählen\n- Bestellungen aufgeben\n- Lieferzeiten verstehen',
                'tags': 'einkauf, lieferanten, bestellung',
                'order': 1
            },
            {
                'title': 'Fahrradproduktion planen',
                'description': 'Optimieren Sie Ihre Produktionsplanung für maximale Effizienz',
                'category': categories['production'],
                'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                'duration_minutes': 12,
                'difficulty_level': 'intermediate',
                'prerequisites': 'Verständnis von Einkaufsprozessen',
                'learning_objectives': 'Nach diesem Video können Sie:\n- Produktionspläne erstellen\n- Kapazitäten verwalten\n- Qualitätskontrolle durchführen',
                'tags': 'produktion, planung, qualität',
                'order': 1
            },
            {
                'title': 'Verkaufsstrategien entwickeln',
                'description': 'Entwickeln Sie effektive Verkaufsstrategien für verschiedene Marktsegmente',
                'category': categories['sales'],
                'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                'duration_minutes': 15,
                'difficulty_level': 'intermediate',
                'learning_objectives': 'Nach diesem Video können Sie:\n- Marktsegmente analysieren\n- Preise strategisch festlegen\n- Verkaufsprognosen erstellen',
                'tags': 'verkauf, strategie, preise',
                'order': 1
            },
            {
                'title': 'Finanzberichte verstehen',
                'description': 'Interpretieren Sie Ihre Finanzberichte und treffen Sie fundierte Entscheidungen',
                'category': categories['finance'],
                'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                'duration_minutes': 10,
                'difficulty_level': 'advanced',
                'learning_objectives': 'Nach diesem Video können Sie:\n- Gewinn- und Verlustrechnung lesen\n- Liquidität bewerten\n- Finanzielle Kennzahlen interpretieren',
                'tags': 'finanzen, berichte, kennzahlen',
                'order': 1
            }
        ]
        
        for data in videos_data:
            video, created = TutorialVideo.objects.get_or_create(
                title=data['title'],
                defaults=data
            )
            if created:
                self.stdout.write(f'  Created video: {video.title}')

    def create_interactive_guides(self, categories):
        self.stdout.write('Creating interactive guides...')
        
        guides_data = [
            {
                'title': 'Erste Schritte - Onboarding Tour',
                'description': 'Eine geführte Tour durch alle wichtigen Bereiche des Simulators',
                'category': categories['basics'],
                'guide_type': 'onboarding',
                'target_url_pattern': '/*',
                'trigger_condition': 'first_visit',
                'user_level_required': 'beginner',
                'steps': [
                    {
                        'target': '.sidebar-brand',
                        'title': 'Willkommen!',
                        'content': 'Willkommen im BikeShop Simulator! Diese Tour zeigt Ihnen die wichtigsten Funktionen.',
                        'placement': 'bottom'
                    },
                    {
                        'target': '.balance-display',
                        'title': 'Ihr Kontostand',
                        'content': 'Hier sehen Sie Ihren aktuellen Kontostand. Achten Sie darauf, dass er nicht ins Minus rutscht!',
                        'placement': 'right'
                    },
                    {
                        'target': 'a[href*="procurement"]',
                        'title': 'Einkauf',
                        'content': 'Hier kaufen Sie Fahrradteile von Lieferanten. Der erste Schritt zu Ihrem Erfolg!',
                        'placement': 'right'
                    },
                    {
                        'target': 'a[href*="production"]',
                        'title': 'Produktion',
                        'content': 'Verwandeln Sie Ihre gekauften Teile in verkaufsfertige Fahrräder.',
                        'placement': 'right'
                    },
                    {
                        'target': 'a[href*="sales"]',
                        'title': 'Verkauf',
                        'content': 'Verkaufen Sie Ihre produzierten Fahrräder an Kunden.',
                        'placement': 'right'
                    },
                    {
                        'target': 'button[onclick="showMonthAdvanceModal()"]',
                        'title': 'Nächster Monat',
                        'content': 'Wenn Sie alle Aktionen für den Monat abgeschlossen haben, können Sie hier zum nächsten Monat wechseln.',
                        'placement': 'top'
                    }
                ],
                'is_skippable': True,
                'show_progress': True,
                'order': 1
            },
            {
                'title': 'Einkaufsprozess Walkthrough',
                'description': 'Schritt-für-Schritt Anleitung für den Einkauf von Fahrradteilen',
                'category': categories['procurement'],
                'guide_type': 'walkthrough',
                'target_url_pattern': '/procurement/*',
                'trigger_condition': 'first_visit',
                'user_level_required': 'beginner',
                'steps': [
                    {
                        'target': '.supplier-list',
                        'title': 'Lieferanten auswählen',
                        'content': 'Wählen Sie einen Lieferanten aus der Liste. Vergleichen Sie Preise und Lieferzeiten.',
                        'placement': 'bottom'
                    },
                    {
                        'target': '.component-selection',
                        'title': 'Komponenten auswählen',
                        'content': 'Wählen Sie die Fahrradteile aus, die Sie bestellen möchten.',
                        'placement': 'top'
                    },
                    {
                        'target': '.order-form',
                        'title': 'Bestellung aufgeben',
                        'content': 'Geben Sie die gewünschte Menge ein und bestätigen Sie Ihre Bestellung.',
                        'placement': 'left'
                    }
                ],
                'is_skippable': True,
                'show_progress': True,
                'order': 1
            },
            {
                'title': 'Produktionsplanung',
                'description': 'Lernen Sie, wie Sie Ihre Fahrradproduktion optimal planen',
                'category': categories['production'],
                'guide_type': 'walkthrough',
                'target_url_pattern': '/production/*',
                'trigger_condition': 'first_visit',
                'user_level_required': 'intermediate',
                'steps': [
                    {
                        'target': '.production-capacity',
                        'title': 'Produktionskapazität',
                        'content': 'Überprüfen Sie Ihre verfügbare Produktionskapazität für den aktuellen Monat.',
                        'placement': 'bottom'
                    },
                    {
                        'target': '.bike-configuration',
                        'title': 'Fahrrad konfigurieren',
                        'content': 'Wählen Sie die Komponenten für Ihr Fahrrad aus. Achten Sie auf Qualität und Kosten.',
                        'placement': 'top'
                    },
                    {
                        'target': '.quality-control',
                        'title': 'Qualitätskontrolle',
                        'content': 'Stellen Sie sicher, dass Ihre Fahrräder den Qualitätsstandards entsprechen.',
                        'placement': 'left'
                    }
                ],
                'is_skippable': True,
                'show_progress': True,
                'order': 1
            }
        ]
        
        for data in guides_data:
            guide, created = InteractiveGuide.objects.get_or_create(
                title=data['title'],
                defaults=data
            )
            if created:
                self.stdout.write(f'  Created guide: {guide.title}')

    def create_tooltips(self, categories):
        self.stdout.write('Creating tooltips...')
        
        tooltips_data = [
            {
                'title': 'Kontostand',
                'content': 'Ihr aktuelles verfügbares Geld. Achten Sie darauf, dass Sie nicht mehr ausgeben als Sie haben!',
                'element_selector': '.balance-display',
                'page_url_pattern': '/*',
                'tooltip_type': 'info',
                'category': categories['basics'],
                'position': 'bottom'
            },
            {
                'title': 'Aktueller Monat',
                'content': 'Der aktuelle Spielmonat. Die Simulation läuft monatsweise ab.',
                'element_selector': '.month-display',
                'page_url_pattern': '/*',
                'tooltip_type': 'info',
                'category': categories['basics'],
                'position': 'bottom'
            },
            {
                'title': 'Lieferzeit',
                'content': 'Die Zeit, die der Lieferant braucht, um Ihre Bestellung zu liefern. Planen Sie entsprechend!',
                'element_selector': '.delivery-time',
                'page_url_pattern': '/procurement/*',
                'tooltip_type': 'tip',
                'category': categories['procurement'],
                'position': 'top'
            },
            {
                'title': 'Stückpreis',
                'content': 'Der Preis pro Stück der Komponente. Vergleichen Sie Preise zwischen Lieferanten.',
                'element_selector': '.unit-price',
                'page_url_pattern': '/procurement/*',
                'tooltip_type': 'info',
                'category': categories['procurement'],
                'position': 'top'
            },
            {
                'title': 'Produktionskapazität',
                'content': 'Die maximale Anzahl von Fahrrädern, die Sie in diesem Monat produzieren können.',
                'element_selector': '.production-capacity',
                'page_url_pattern': '/production/*',
                'tooltip_type': 'warning',
                'category': categories['production'],
                'position': 'bottom'
            },
            {
                'title': 'Qualitätsbewertung',
                'content': 'Die Qualität Ihrer produzierten Fahrräder beeinflusst den Verkaufspreis und die Kundenzufriedenheit.',
                'element_selector': '.quality-rating',
                'page_url_pattern': '/production/*',
                'tooltip_type': 'tip',
                'category': categories['production'],
                'position': 'top'
            },
            {
                'title': 'Marktpreis',
                'content': 'Der durchschnittliche Marktpreis für diesen Fahrradtyp. Orientieren Sie sich daran bei der Preisgestaltung.',
                'element_selector': '.market-price',
                'page_url_pattern': '/sales/*',
                'tooltip_type': 'info',
                'category': categories['sales'],
                'position': 'top'
            }
        ]
        
        for data in tooltips_data:
            tooltip, created = TooltipHelp.objects.get_or_create(
                element_selector=data['element_selector'],
                page_url_pattern=data['page_url_pattern'],
                defaults=data
            )
            if created:
                self.stdout.write(f'  Created tooltip: {tooltip.title}')

    def create_contextual_help(self, categories):
        self.stdout.write('Creating contextual help...')
        
        contextual_help_data = [
            {
                'title': 'Willkommen im Simulator!',
                'content': 'Sie starten mit einem Startkapital. Ihr Ziel ist es, ein erfolgreiches Fahrradgeschäft aufzubauen. Beginnen Sie mit dem Einkauf von Komponenten!',
                'context_type': 'page_load',
                'trigger_conditions': {'page': '/', 'first_time': True},
                'help_format': 'popup',
                'category': categories['basics'],
                'user_experience_level': 'beginner',
                'priority': 1
            },
            {
                'title': 'Niedrige Liquidität!',
                'content': 'Ihr Kontostand ist niedrig. Achten Sie darauf, genügend Geld für wichtige Ausgaben zu haben. Überlegen Sie, ob Sie einige Fahrräder verkaufen sollten.',
                'context_type': 'milestone_reached',
                'trigger_conditions': {'balance_low': True, 'threshold': 1000},
                'help_format': 'banner',
                'category': categories['finance'],
                'user_experience_level': 'beginner',
                'priority': 2
            },
            {
                'title': 'Leeres Lager',
                'content': 'Ihr Lager ist leer. Ohne Komponenten können Sie keine Fahrräder produzieren. Gehen Sie zum Einkauf und bestellen Sie neue Teile.',
                'context_type': 'error_occurred',
                'trigger_conditions': {'inventory_empty': True},
                'help_format': 'popup',
                'category': categories['warehouse'],
                'user_experience_level': 'beginner',
                'priority': 3
            },
            {
                'title': 'Erste Bestellung',
                'content': 'Großartig! Sie sind dabei, Ihre erste Bestellung aufzugeben. Achten Sie auf die Lieferzeit - Sie können erst produzieren, wenn die Teile geliefert wurden.',
                'context_type': 'action_taken',
                'trigger_conditions': {'first_order': True},
                'help_format': 'sidebar',
                'category': categories['procurement'],
                'user_experience_level': 'beginner',
                'priority': 4
            },
            {
                'title': 'Produktion bereit',
                'content': 'Sie haben alle benötigten Komponenten. Jetzt können Sie mit der Fahrradproduktion beginnen. Beachten Sie Ihre Produktionskapazität!',
                'context_type': 'milestone_reached',
                'trigger_conditions': {'can_produce': True, 'first_production': True},
                'help_format': 'popup',
                'category': categories['production'],
                'user_experience_level': 'beginner',
                'priority': 5
            }
        ]
        
        for data in contextual_help_data:
            help_item, created = ContextualHelp.objects.get_or_create(
                title=data['title'],
                context_type=data['context_type'],
                defaults=data
            )
            if created:
                self.stdout.write(f'  Created contextual help: {help_item.title}')