from django.core.management.base import BaseCommand
from help_system.models import HelpCategory, InteractiveGuide


class Command(BaseCommand):
    help = 'Create sample interactive guides for the bike shop simulation'

    def handle(self, *args, **options):
        self.stdout.write('Creating interactive guides...')
        
        # Get or create categories
        procurement_cat, _ = HelpCategory.objects.get_or_create(
            category_type='procurement',
            defaults={
                'name': 'Einkauf',
                'description': 'Anleitungen für die Beschaffung von Komponenten',
                'icon': 'fas fa-shopping-cart',
                'order': 1
            }
        )
        
        production_cat, _ = HelpCategory.objects.get_or_create(
            category_type='production',
            defaults={
                'name': 'Produktion',
                'description': 'Anleitungen für die Fahrradproduktion',
                'icon': 'fas fa-cogs',
                'order': 2
            }
        )
        
        sales_cat, _ = HelpCategory.objects.get_or_create(
            category_type='sales',
            defaults={
                'name': 'Verkauf',
                'description': 'Anleitungen für den Verkauf und Marketing',
                'icon': 'fas fa-handshake',
                'order': 3
            }
        )
        
        finance_cat, _ = HelpCategory.objects.get_or_create(
            category_type='finance',
            defaults={
                'name': 'Finanzen',
                'description': 'Anleitungen für Finanzmanagement',
                'icon': 'fas fa-euro-sign',
                'order': 4
            }
        )
        
        # Create Procurement Guide
        procurement_guide, created = InteractiveGuide.objects.get_or_create(
            title='Erste Schritte - Einkauf',
            defaults={
                'description': 'Lernen Sie, wie Sie Komponenten einkaufen und Lieferanten verwalten',
                'category': procurement_cat,
                'guide_type': 'onboarding',
                'target_url_pattern': '/procurement/*',
                'user_level_required': 'beginner',
                'steps': [
                    {
                        'title': 'Willkommen beim Einkauf',
                        'content': 'In diesem Bereich können Sie Komponenten für Ihre Fahrräder bestellen. Lassen Sie uns durch die wichtigsten Funktionen gehen.',
                        'target': 'body',
                        'placement': 'center',
                        'navigate_to': 'procurement'
                    },
                    {
                        'title': 'Komponentenübersicht',
                        'content': 'Hier sehen Sie alle verfügbaren Komponenten. Jede Komponente hat verschiedene Qualitätsstufen und Preise.',
                        'target': '.components-table',
                        'placement': 'top'
                    },
                    {
                        'title': 'Lieferanten verwalten',
                        'content': 'Wählen Sie den besten Lieferanten basierend auf Preis, Qualität und Lieferzeit.',
                        'target': '.supplier-dropdown',
                        'placement': 'bottom'
                    },
                    {
                        'title': 'Bestellung aufgeben',
                        'content': 'Geben Sie die gewünschte Menge ein und klicken Sie auf "Bestellen", um Ihre Bestellung abzuschicken.',
                        'target': '.order-form',
                        'placement': 'top'
                    },
                    {
                        'title': 'Budget im Blick behalten',
                        'content': 'Achten Sie auf Ihr verfügbares Budget oben rechts. Überziehen Sie nicht Ihre finanziellen Möglichkeiten!',
                        'target': '.budget-display',
                        'placement': 'left'
                    }
                ],
                'order': 1,
                'is_active': True
            }
        )
        
        # Create Production Guide
        production_guide, created = InteractiveGuide.objects.get_or_create(
            title='Fahrradproduktion starten',
            defaults={
                'description': 'Lernen Sie, wie Sie Fahrräder produzieren und Ihre Produktionskapazität verwalten',
                'category': production_cat,
                'guide_type': 'walkthrough',
                'target_url_pattern': '/production/*',
                'user_level_required': 'beginner',
                'steps': [
                    {
                        'title': 'Produktionsübersicht',
                        'content': 'Hier verwalten Sie Ihre Fahrradproduktion. Sie können verschiedene Fahrradtypen produzieren.',
                        'target': 'body',
                        'placement': 'center'
                    },
                    {
                        'title': 'Fahrradtyp auswählen',
                        'content': 'Wählen Sie den Typ des Fahrrads, den Sie produzieren möchten. Jeder Typ benötigt verschiedene Komponenten.',
                        'target': '.bike-type-selector',
                        'placement': 'top'
                    },
                    {
                        'title': 'Komponenten prüfen',
                        'content': 'Stellen Sie sicher, dass Sie genügend Komponenten im Lager haben, bevor Sie die Produktion starten.',
                        'target': '.components-status',
                        'placement': 'right'
                    },
                    {
                        'title': 'Arbeiter einstellen',
                        'content': 'Sie benötigen qualifizierte Arbeiter für die Produktion. Hier können Sie neue Mitarbeiter einstellen.',
                        'target': '.hire-worker-btn',
                        'placement': 'bottom'
                    },
                    {
                        'title': 'Produktion starten',
                        'content': 'Wenn alle Voraussetzungen erfüllt sind, können Sie die Produktion für diesen Monat starten.',
                        'target': '.start-production-btn',
                        'placement': 'top'
                    }
                ],
                'order': 2,
                'is_active': True
            }
        )
        
        # Create Sales Guide  
        sales_guide, created = InteractiveGuide.objects.get_or_create(
            title='Verkauf und Marketing',
            defaults={
                'description': 'Verstehen Sie die Marktdynamik und optimieren Sie Ihre Verkaufsstrategie',
                'category': sales_cat,
                'guide_type': 'walkthrough',
                'target_url_pattern': '/sales/*',
                'user_level_required': 'intermediate',
                'steps': [
                    {
                        'title': 'Verkaufsbereich',
                        'content': 'Hier analysieren Sie Markttrends und setzen Verkaufspreise für Ihre Fahrräder fest.',
                        'target': 'body',
                        'placement': 'center'
                    },
                    {
                        'title': 'Marktanalyse',
                        'content': 'Studieren Sie die Nachfrage nach verschiedenen Fahrradtypen in verschiedenen Märkten.',
                        'target': '.market-analysis',
                        'placement': 'top'
                    },
                    {
                        'title': 'Preise festlegen',
                        'content': 'Setzen Sie competitive Preise, die sowohl profitabel als auch marktgerecht sind.',
                        'target': '.price-setting',
                        'placement': 'bottom'
                    },
                    {
                        'title': 'Marketing-Budget',
                        'content': 'Investieren Sie in Marketing, um die Nachfrage nach Ihren Produkten zu steigern.',
                        'target': '.marketing-budget',
                        'placement': 'left'
                    },
                    {
                        'title': 'Verkaufsprognose',
                        'content': 'Überprüfen Sie die Verkaufsprognose, um Ihre Produktionsplanung anzupassen.',
                        'target': '.sales-forecast',
                        'placement': 'right'
                    }
                ],
                'order': 3,
                'is_active': True
            }
        )
        
        # Create Finance Guide
        finance_guide, created = InteractiveGuide.objects.get_or_create(
            title='Finanzmanagement Grundlagen',
            defaults={
                'description': 'Behalten Sie Ihre Finanzen im Griff und verstehen Sie wichtige Kennzahlen',
                'category': finance_cat,
                'guide_type': 'onboarding',
                'target_url_pattern': '/finance/*',
                'user_level_required': 'beginner',
                'steps': [
                    {
                        'title': 'Finanz-Dashboard',
                        'content': 'Ihr Finanz-Dashboard zeigt alle wichtigen Kennzahlen auf einen Blick.',
                        'target': 'body',
                        'placement': 'center'
                    },
                    {
                        'title': 'Aktueller Kontostand',
                        'content': 'Hier sehen Sie Ihren aktuellen Kontostand. Achten Sie darauf, dass er nicht ins Negative rutscht!',
                        'target': '.balance-display',
                        'placement': 'bottom'
                    },
                    {
                        'title': 'Gewinn- und Verlustrechnung',
                        'content': 'Diese Übersicht zeigt Ihnen Ihre Einnahmen und Ausgaben im Detail.',
                        'target': '.profit-loss-section',
                        'placement': 'top'
                    },
                    {
                        'title': 'Kredite verwalten',
                        'content': 'Falls Sie zusätzliches Kapital benötigen, können Sie hier Kredite aufnehmen.',
                        'target': '.credit-management',
                        'placement': 'right'
                    },
                    {
                        'title': 'Finanzberichte',
                        'content': 'Regelmäßige Finanzberichte helfen Ihnen, den Überblick über Ihr Unternehmen zu behalten.',
                        'target': '.financial-reports',
                        'placement': 'left'
                    }
                ],
                'order': 4,
                'is_active': True
            }
        )
        
        # Create multi-page simulation guide
        simulation_guide, created = InteractiveGuide.objects.get_or_create(
            title='Komplette Simulation - Rundgang',
            defaults={
                'description': 'Ein vollständiger Rundgang durch alle Bereiche der Simulation',
                'category': procurement_cat,  # Using procurement as general category
                'guide_type': 'walkthrough',
                'target_url_pattern': '/session/*',
                'user_level_required': 'beginner',
                'steps': [
                    {
                        'title': 'Willkommen zur Simulation',
                        'content': 'Dieser Rundgang führt Sie durch alle wichtigen Bereiche der Fahrrad-Simulation. Wir beginnen mit dem Einkauf.',
                        'target': 'body',
                        'placement': 'center',
                        'navigate_to': '/procurement/{{ session_id }}/'
                    },
                    {
                        'title': 'Einkauf - Komponenten bestellen',
                        'content': 'Im Einkaufsbereich bestellen Sie alle Komponenten, die Sie für die Fahrradproduktion benötigen.',
                        'target': '.main-content',
                        'placement': 'top'
                    },
                    {
                        'title': 'Zur Produktion wechseln',
                        'content': 'Nachdem Sie Komponenten bestellt haben, gehen wir zur Produktion über.',
                        'target': 'body',
                        'placement': 'center',
                        'navigate_to': '/production/{{ session_id }}/'
                    },
                    {
                        'title': 'Produktion - Fahrräder herstellen',
                        'content': 'Hier produzieren Sie Ihre Fahrräder aus den bestellten Komponenten.',
                        'target': '.main-content',
                        'placement': 'top'
                    },
                    {
                        'title': 'Zum Verkauf wechseln',
                        'content': 'Jetzt schauen wir uns an, wie Sie Ihre produzierten Fahrräder verkaufen.',
                        'target': 'body',
                        'placement': 'center',
                        'navigate_to': '/sales/{{ session_id }}/'
                    },
                    {
                        'title': 'Verkauf - Markt erobern',
                        'content': 'Im Verkaufsbereich legen Sie Preise fest und investieren in Marketing.',
                        'target': '.main-content',
                        'placement': 'top'
                    },
                    {
                        'title': 'Finanzen prüfen',
                        'content': 'Zum Abschluss schauen wir uns Ihre Finanzen an.',
                        'target': 'body',
                        'placement': 'center',
                        'navigate_to': '/finance/{{ session_id }}/'
                    },
                    {
                        'title': 'Finanz-Übersicht',
                        'content': 'Hier behalten Sie Ihre Finanzen im Blick und können wichtige Entscheidungen treffen.',
                        'target': '.main-content',
                        'placement': 'top'
                    },
                    {
                        'title': 'Simulation komplett!',
                        'content': 'Gratulation! Sie haben alle wichtigen Bereiche der Simulation kennengelernt. Viel Erfolg beim Aufbau Ihres Fahrrad-Imperiums!',
                        'target': 'body',
                        'placement': 'center'
                    }
                ],
                'order': 0,  # First guide
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {InteractiveGuide.objects.count()} interactive guides'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('Guides already exist, skipping creation')
            )