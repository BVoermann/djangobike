from django.core.management.base import BaseCommand
from help_system.models import HelpCategory, InteractiveGuide


class Command(BaseCommand):
    help = 'Create interactive guides for all simulation tabs'

    def handle(self, *args, **options):
        self.stdout.write('Creating interactive guides for simulation tabs...')

        # Get or create categories
        general_cat, _ = HelpCategory.objects.get_or_create(
            category_type='general',
            defaults={
                'name': 'Allgemein',
                'description': 'Allgemeine Anleitungen zur Simulation',
                'icon': 'fas fa-info-circle',
                'order': 0
            }
        )

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

        warehouse_cat, _ = HelpCategory.objects.get_or_create(
            category_type='warehouse',
            defaults={
                'name': 'Lager',
                'description': 'Anleitungen für die Lagerverwaltung',
                'icon': 'fas fa-warehouse',
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

        sales_cat, _ = HelpCategory.objects.get_or_create(
            category_type='sales',
            defaults={
                'name': 'Verkauf',
                'description': 'Anleitungen für den Verkauf und Marketing',
                'icon': 'fas fa-handshake',
                'order': 5
            }
        )

        # Create Procurement Guide
        InteractiveGuide.objects.update_or_create(
            title='Einkauf: Komponenten bestellen',
            defaults={
                'description': 'Lernen Sie, wie Sie Komponenten von Lieferanten bestellen',
                'category': procurement_cat,
                'guide_type': 'walkthrough',
                'target_url_pattern': '/help/mock-simulation/procurement/',
                'user_level_required': 'beginner',
                'steps': [
                    {
                        'title': 'Willkommen beim Einkauf',
                        'content': 'Im Einkaufs-Tab können Sie Komponenten für Ihre Fahrradproduktion bestellen. Diese Übungsumgebung zeigt Ihnen die wichtigsten Funktionen.',
                        'target': '.display-4',
                        'placement': 'bottom'
                    },
                    {
                        'title': 'Lieferant auswählen',
                        'content': 'Wählen Sie hier einen Lieferanten aus. Jeder Lieferant bietet unterschiedliche Qualitätsstufen, Lieferzeiten und Zahlungsbedingungen.',
                        'target': '#mockSupplierDropdown',
                        'placement': 'bottom'
                    },
                    {
                        'title': 'Budget überwachen',
                        'content': 'Hier sehen Sie Ihr verfügbares Budget. Achten Sie darauf, dass Sie nicht mehr ausgeben als verfügbar ist!',
                        'target': '.col-lg-3:first-child .card',
                        'placement': 'right'
                    },
                    {
                        'title': 'Lieferanten-Informationen',
                        'content': 'Diese Badges zeigen wichtige Informationen: Qualitätsstufe, Lieferzeit und Zahlungsziel des ausgewählten Lieferanten.',
                        'target': '.supplier-badges',
                        'placement': 'left'
                    },
                    {
                        'title': 'Komponenten bestellen',
                        'content': 'In dieser Tabelle sehen Sie alle verfügbaren Komponenten. Geben Sie die gewünschte Menge ein und beobachten Sie, wie sich der Gesamtpreis ändert.',
                        'target': '.table-responsive',
                        'placement': 'top'
                    },
                    {
                        'title': 'Bestellung aufgeben',
                        'content': 'Prüfen Sie den Gesamtpreis Ihrer Bestellung und klicken Sie auf "Bestellung aufgeben", um die Komponenten zu bestellen.',
                        'target': '.btn-primary.btn-lg.px-4',
                        'placement': 'top'
                    }
                ],
                'order': 1,
                'is_active': True
            }
        )

        # Create Production Guide
        InteractiveGuide.objects.update_or_create(
            title='Produktion: Fahrräder herstellen',
            defaults={
                'description': 'Lernen Sie, wie Sie aus Komponenten Fahrräder produzieren',
                'category': production_cat,
                'guide_type': 'walkthrough',
                'target_url_pattern': '/help/mock-simulation/production/',
                'user_level_required': 'beginner',
                'steps': [
                    {
                        'title': 'Willkommen bei der Produktion',
                        'content': 'Im Produktions-Tab stellen Sie aus Ihren eingekauften Komponenten fertige Fahrräder her.',
                        'target': 'h1',
                        'placement': 'bottom'
                    },
                    {
                        'title': 'Fahrradtyp auswählen',
                        'content': 'Wählen Sie den Typ des Fahrrads aus, den Sie produzieren möchten. Jeder Typ benötigt unterschiedliche Komponenten.',
                        'target': '.bike-type-selector',
                        'placement': 'bottom'
                    },
                    {
                        'title': 'Verfügbare Komponenten',
                        'content': 'Hier sehen Sie, welche Komponenten Sie auf Lager haben. Stellen Sie sicher, dass genügend Komponenten für die gewünschte Anzahl vorhanden sind.',
                        'target': '.components-status',
                        'placement': 'right'
                    },
                    {
                        'title': 'Produktionsmenge festlegen',
                        'content': 'Geben Sie an, wie viele Fahrräder Sie produzieren möchten. Die benötigten Komponenten werden automatisch berechnet.',
                        'target': '.production-quantity',
                        'placement': 'left'
                    },
                    {
                        'title': 'Produktion starten',
                        'content': 'Klicken Sie hier, um die Produktion zu starten. Die fertigen Fahrräder werden in Ihr Lager aufgenommen.',
                        'target': '.start-production-btn',
                        'placement': 'top'
                    }
                ],
                'order': 2,
                'is_active': True
            }
        )

        # Create Warehouse Guide
        InteractiveGuide.objects.update_or_create(
            title='Lager: Bestand verwalten',
            defaults={
                'description': 'Lernen Sie, wie Sie Ihren Lagerbestand überwachen und verwalten',
                'category': warehouse_cat,
                'guide_type': 'walkthrough',
                'target_url_pattern': '/help/mock-simulation/warehouse/',
                'user_level_required': 'beginner',
                'steps': [
                    {
                        'title': 'Willkommen im Lager',
                        'content': 'Im Lager-Tab können Sie Ihren gesamten Bestand an Komponenten und fertigen Fahrrädern überwachen.',
                        'target': 'h1',
                        'placement': 'bottom'
                    },
                    {
                        'title': 'Komponenten-Bestand',
                        'content': 'Diese Karten zeigen Ihren aktuellen Bestand an Komponenten. Achten Sie darauf, dass Sie immer genügend für die Produktion haben.',
                        'target': '.component-stock-card:first-child',
                        'placement': 'right'
                    },
                    {
                        'title': 'Fertige Fahrräder',
                        'content': 'Hier sehen Sie, wie viele fertige Fahrräder Sie auf Lager haben und zum Verkauf bereit sind.',
                        'target': '.finished-bikes-section',
                        'placement': 'top'
                    },
                    {
                        'title': 'Lageraktivitäten',
                        'content': 'Diese Liste zeigt die letzten Bewegungen in Ihrem Lager: Eingänge von Bestellungen, fertige Produktionen und Verkäufe.',
                        'target': '.list-group',
                        'placement': 'left'
                    }
                ],
                'order': 3,
                'is_active': True
            }
        )

        # Create Finance/Kredite Guide
        InteractiveGuide.objects.update_or_create(
            title='Kredite: Finanzierung verwalten',
            defaults={
                'description': 'Lernen Sie, wie Sie Kredite aufnehmen und Ihre Finanzen verwalten',
                'category': finance_cat,
                'guide_type': 'walkthrough',
                'target_url_pattern': '/help/mock-simulation/finance/',
                'user_level_required': 'beginner',
                'steps': [
                    {
                        'title': 'Willkommen im Finanz-Tab',
                        'content': 'Hier können Sie Ihren Kontostand überwachen und bei Bedarf Kredite aufnehmen.',
                        'target': 'h1',
                        'placement': 'bottom'
                    },
                    {
                        'title': 'Aktueller Kontostand',
                        'content': 'Dies ist Ihr aktueller Kontostand. Wenn dieser niedrig ist, können Sie einen Kredit aufnehmen.',
                        'target': '.balance-display',
                        'placement': 'right'
                    },
                    {
                        'title': 'Kredit aufnehmen',
                        'content': 'Wählen Sie einen Kredittyp, geben Sie den Betrag ein und bestätigen Sie. Beachten Sie die Zinsen und Laufzeiten!',
                        'target': '.credit-form',
                        'placement': 'left'
                    },
                    {
                        'title': 'Laufende Kredite',
                        'content': 'Hier sehen Sie alle Ihre aktiven Kredite mit monatlichen Raten und verbleibender Laufzeit.',
                        'target': '.active-credits',
                        'placement': 'top'
                    }
                ],
                'order': 4,
                'is_active': True
            }
        )

        # Create Sales Guide
        InteractiveGuide.objects.update_or_create(
            title='Verkauf: Fahrräder verkaufen',
            defaults={
                'description': 'Lernen Sie, wie Sie Ihre Fahrräder auf verschiedenen Märkten verkaufen',
                'category': sales_cat,
                'guide_type': 'walkthrough',
                'target_url_pattern': '/help/mock-simulation/sales/',
                'user_level_required': 'beginner',
                'steps': [
                    {
                        'title': 'Willkommen im Verkaufs-Tab',
                        'content': 'Hier können Sie Ihre produzierten Fahrräder auf verschiedenen Märkten verkaufen und Preise festlegen.',
                        'target': 'h1',
                        'placement': 'bottom'
                    },
                    {
                        'title': 'Markt auswählen',
                        'content': 'Wählen Sie den Markt aus, auf dem Sie verkaufen möchten. Jeder Markt hat unterschiedliche Nachfrage und Preissensibilität.',
                        'target': '.market-selector',
                        'placement': 'bottom'
                    },
                    {
                        'title': 'Preise festlegen',
                        'content': 'Legen Sie hier Ihre Verkaufspreise fest. Höhere Preise = mehr Gewinn, aber möglicherweise weniger Verkäufe.',
                        'target': '.price-input',
                        'placement': 'left'
                    },
                    {
                        'title': 'Verkaufsprognose',
                        'content': 'Diese Prognose zeigt Ihnen, wie viele Fahrräder Sie voraussichtlich verkaufen werden und welchen Umsatz Sie erzielen.',
                        'target': '.sales-forecast',
                        'placement': 'right'
                    },
                    {
                        'title': 'Preise speichern',
                        'content': 'Klicken Sie hier, um Ihre Preise zu speichern. Sie werden im nächsten Monat für die Verkäufe verwendet.',
                        'target': '.btn-success',
                        'placement': 'top'
                    }
                ],
                'order': 5,
                'is_active': True
            }
        )

        # Create Financial Reports Guide
        InteractiveGuide.objects.update_or_create(
            title='Finanzberichte: Kennzahlen verstehen',
            defaults={
                'description': 'Lernen Sie, wie Sie Ihre Finanzberichte lesen und interpretieren',
                'category': finance_cat,
                'guide_type': 'walkthrough',
                'target_url_pattern': '/help/mock-simulation/finance/',
                'user_level_required': 'intermediate',
                'steps': [
                    {
                        'title': 'Finanzielle Übersicht',
                        'content': 'Der Finanzberichte-Tab zeigt Ihnen detaillierte Informationen über Ihre wirtschaftliche Leistung.',
                        'target': 'h1',
                        'placement': 'bottom'
                    },
                    {
                        'title': 'Gewinn und Verlust',
                        'content': 'Die Gewinn- und Verlustrechnung zeigt Ihre Einnahmen, Ausgaben und den resultierenden Gewinn oder Verlust.',
                        'target': '.profit-loss-section',
                        'placement': 'right'
                    },
                    {
                        'title': 'Liquidität',
                        'content': 'Die Liquidität zeigt, wie viel Bargeld Sie verfügbar haben. Eine gute Liquidität ist wichtig für die Zahlungsfähigkeit.',
                        'target': '.liquidity-section',
                        'placement': 'left'
                    },
                    {
                        'title': 'Trends analysieren',
                        'content': 'Nutzen Sie diese Diagramme, um Trends in Ihren Finanzen zu erkennen und bessere Entscheidungen zu treffen.',
                        'target': '.chart-section',
                        'placement': 'top'
                    }
                ],
                'order': 6,
                'is_active': True
            }
        )

        self.stdout.write(self.style.SUCCESS(f'Successfully created 6 interactive guides for simulation tabs'))
