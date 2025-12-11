"""
Management command to create a "Getting Started" guide for beginners.

Usage:
    python manage.py create_getting_started_guide
"""

from django.core.management.base import BaseCommand
from help_system.models import HelpCategory, InteractiveGuide


class Command(BaseCommand):
    help = 'Create a beginner-friendly "Getting Started" guide'

    def handle(self, *args, **options):
        self.stdout.write('Creating Getting Started guide...')

        # Get or create Basics category
        basics_category, created = HelpCategory.objects.get_or_create(
            category_type='basics',
            defaults={
                'name': 'Grundlagen',
                'description': 'Grundlegende Konzepte und erste Schritte im Fahrradgeschäft-Simulator',
                'icon': 'fas fa-graduation-cap',
                'order': 1
            }
        )

        # Create Getting Started guide
        guide, created = InteractiveGuide.objects.update_or_create(
            title='Erste Schritte: Wie funktioniert das Spiel?',
            category=basics_category,
            defaults={
                'description': 'Ein kurzer Leitfaden für Anfänger über die Grundmechaniken des Spiels und die ersten Schritte zum Erfolg',
                'guide_type': 'onboarding',
                'target_url_pattern': '/dashboard/*',
                'trigger_condition': 'manual',
                'is_skippable': True,
                'show_progress': True,
                'user_level_required': 'beginner',
                'order': 1,
                'is_active': True,
                'steps': [
                    {
                        'target': 'body',
                        'title': '🎮 Willkommen im Fahrradgeschäft-Simulator!',
                        'content': '''
                            <h3>Spielziel</h3>
                            <p>Führe dein Fahrradunternehmen zum Erfolg! Kaufe Komponenten ein, produziere Fahrräder und verkaufe sie mit Gewinn.</p>

                            <h3>Spielablauf</h3>
                            <p>Das Spiel läuft in <strong>monatlichen Runden</strong>. Jeden Monat triffst du Entscheidungen in diesen Bereichen:</p>
                            <ul>
                                <li><strong>🛒 Einkauf</strong> - Komponenten bei Lieferanten bestellen</li>
                                <li><strong>⚙️ Produktion</strong> - Fahrräder zusammenbauen</li>
                                <li><strong>💰 Verkauf</strong> - Fahrräder auf Märkten verkaufen</li>
                                <li><strong>💼 Finanzen</strong> - Kredite, Ausgaben, Gewinne verwalten</li>
                            </ul>

                            <p><strong>Wichtig:</strong> Am Monatsende werden alle Entscheidungen gleichzeitig verarbeitet. Du siehst dann die Ergebnisse und kannst für den nächsten Monat planen.</p>
                        ''',
                        'placement': 'center'
                    },
                    {
                        'target': 'body',
                        'title': '💰 Dein Startkapital: 80.000€',
                        'content': '''
                            <h3>Fixkosten pro Monat</h3>
                            <ul>
                                <li>Lagermiete: ~1.200€/Monat</li>
                                <li>Arbeiterlöhne: ~4.800€/Monat</li>
                                <li><strong>Gesamt: ~6.000€/Monat</strong></li>
                            </ul>

                            <p>Das bedeutet: Du hast etwa <strong>13 Monate Zeit</strong>, um profitabel zu werden, bevor dir das Geld ausgeht!</p>

                            <h3>Ziel</h3>
                            <p>Verkaufe mindestens <strong>30 Fahrräder pro Monat</strong>, um die Kosten zu decken und Gewinn zu machen.</p>

                            <div style="background-color: #fef3c7; padding: 10px; border-left: 4px solid #f59e0b; margin-top: 10px;">
                                <strong>💡 Tipp:</strong> Starte klein (5-10 Fahrräder) und baue dann langsam aus!
                            </div>
                        ''',
                        'placement': 'center'
                    },
                    {
                        'target': 'body',
                        'title': '📋 Schritt 1: Komponenten einkaufen',
                        'content': '''
                            <h3>Gehe zum Einkaufs-Tab</h3>

                            <p>Jedes Fahrrad benötigt diese Komponenten:</p>
                            <ul>
                                <li>🛞 <strong>Laufradsatz</strong> (Räder)</li>
                                <li>🏗️ <strong>Rahmen</strong></li>
                                <li>🎮 <strong>Lenker</strong></li>
                                <li>💺 <strong>Sattel</strong></li>
                                <li>⚙️ <strong>Schaltung</strong> (Gangschaltung)</li>
                                <li>🔋 <strong>Motor</strong> (nur für E-Bikes)</li>
                            </ul>

                            <h3>Lieferanten</h3>
                            <p>Du kannst bei 4 Lieferanten bestellen:</p>
                            <ul>
                                <li><strong>Budget Bike Supply</strong> - Günstig, aber niedrige Qualität</li>
                                <li><strong>BikeComponents GmbH</strong> - Standard-Qualität, guter Mittelweg</li>
                                <li><strong>EuroCycle Distribution</strong> - Standard-Qualität, andere Konditionen</li>
                                <li><strong>Premium Parts AG</strong> - Teuer, aber höchste Qualität</li>
                            </ul>

                            <div style="background-color: #fef3c7; padding: 10px; border-left: 4px solid #f59e0b; margin-top: 10px;">
                                <strong>💡 Empfehlung für Monat 1:</strong><br>
                                Bestelle Komponenten für 5-10 einfache Fahrräder (Damenrad oder Herrenrad).<br>
                                Pro Fahrrad: ~150-200€ an Komponenten<br>
                                <strong>Budget: 1.000-2.000€</strong>
                            </div>
                        ''',
                        'placement': 'center'
                    },
                    {
                        'target': 'body',
                        'title': '⚙️ Schritt 2: Fahrräder produzieren',
                        'content': '''
                            <h3>Gehe zum Produktions-Tab</h3>

                            <p>Sobald die Komponenten geliefert wurden (nach Lieferzeit), kannst du Fahrräder produzieren.</p>

                            <h3>Produktionsplanung</h3>
                            <ul>
                                <li>Wähle einen <strong>Fahrrad-Typ</strong> (z.B. Damenrad)</li>
                                <li>Wähle eine <strong>Preiskategorie</strong>:
                                    <ul>
                                        <li><strong>Günstig</strong> - Niedrige Qualität, niedriger Preis (~299€)</li>
                                        <li><strong>Standard</strong> - Mittlere Qualität (~449€)</li>
                                        <li><strong>Premium</strong> - Hohe Qualität, hoher Preis (~699€)</li>
                                    </ul>
                                </li>
                                <li>Gib die <strong>Stückzahl</strong> an</li>
                            </ul>

                            <h3>Arbeiterstunden</h3>
                            <p>Jedes Fahrrad braucht Arbeitsstunden:</p>
                            <ul>
                                <li>Damenrad/Herrenrad: ~5,5 Stunden</li>
                                <li>Mountainbike: ~6,5 Stunden</li>
                                <li>E-Bikes: ~8+ Stunden</li>
                            </ul>

                            <p>Du hast <strong>2 Facharbeiter</strong> (320h/Monat) und <strong>3 Hilfsarbeiter</strong> (480h/Monat).</p>

                            <div style="background-color: #fef3c7; padding: 10px; border-left: 4px solid #f59e0b; margin-top: 10px;">
                                <strong>💡 Empfehlung für Monat 1:</strong><br>
                                Produziere 5-10 Damenräder oder Herrenräder in <strong>Standard-Qualität</strong>.<br>
                                Das ist ein guter Mittelweg zwischen Kosten und Verkaufspreis.
                            </div>
                        ''',
                        'placement': 'center'
                    },
                    {
                        'target': 'body',
                        'title': '💰 Schritt 3: Fahrräder verkaufen',
                        'content': '''
                            <h3>Gehe zum Verkaufs-Tab</h3>

                            <p>Du hast Zugang zu 2 Märkten:</p>
                            <ul>
                                <li><strong>Domestic Market</strong> (Deutschland) - Näher, günstiger Transport</li>
                                <li><strong>EU Market</strong> (Europa) - Größer, höhere Transportkosten</li>
                            </ul>

                            <h3>Marktnachfrage</h3>
                            <p>Im Verkaufs-Tab siehst du die <strong>geschätzte Nachfrage</strong> für jeden Fahrrad-Typ.</p>

                            <p>Ohne Marktforschung:</p>
                            <ul>
                                <li>❓ Sehr breite Schätzung (z.B. 24-92 Fahrräder)</li>
                            </ul>

                            <p>Mit Marktforschung (kostet 500€-5.000€):</p>
                            <ul>
                                <li>🔬 Genauere Schätzung (z.B. 38-72 Fahrräder)</li>
                            </ul>

                            <h3>Verkaufspreis festlegen</h3>
                            <p>Du kannst den Preis selbst festlegen, aber beachte:</p>
                            <ul>
                                <li>Zu teuer → Fahrräder bleiben liegen</li>
                                <li>Zu günstig → Wenig Gewinn</li>
                                <li>Empfohlene Preise werden angezeigt</li>
                            </ul>

                            <div style="background-color: #fef3c7; padding: 10px; border-left: 4px solid #f59e0b; margin-top: 10px;">
                                <strong>💡 Empfehlung für Monat 1:</strong><br>
                                Verkaufe deine 5-10 Fahrräder auf dem <strong>Domestic Market</strong>.<br>
                                Nutze die <strong>empfohlenen Preise</strong> für Standard-Qualität (~449€).<br>
                                Erwarteter Gewinn: 100-150€ pro Fahrrad = <strong>500-1.500€ Gewinn</strong>
                            </div>
                        ''',
                        'placement': 'center'
                    },
                    {
                        'target': 'body',
                        'title': '📊 Schritt 4: Monat abschließen & Ergebnisse sehen',
                        'content': '''
                            <h3>Entscheidungen einreichen</h3>
                            <p>Wenn du mit deinen Entscheidungen zufrieden bist:</p>
                            <ol>
                                <li>Überprüfe noch einmal alle Tabs</li>
                                <li>Klicke auf <strong>"Monat abschließen"</strong> oder ähnlich</li>
                                <li>Das Spiel verarbeitet alle Entscheidungen</li>
                            </ol>

                            <h3>Was passiert dann?</h3>
                            <ul>
                                <li>🚚 Bestellte Komponenten werden geliefert (nach Lieferzeit)</li>
                                <li>⚙️ Fahrräder werden produziert</li>
                                <li>💰 Verkäufe werden abgewickelt</li>
                                <li>📊 Fixkosten werden abgezogen</li>
                                <li>📈 Du siehst deinen neuen Kontostand</li>
                            </ul>

                            <h3>Monatsberichte</h3>
                            <p>Im <strong>Finanzen-Tab</strong> siehst du detaillierte Berichte:</p>
                            <ul>
                                <li>Einnahmen und Ausgaben</li>
                                <li>Welche Fahrräder sich verkauft haben</li>
                                <li>Gewinn/Verlust des Monats</li>
                            </ul>

                            <div style="background-color: #dcfce7; padding: 10px; border-left: 4px solid #22c55e; margin-top: 10px;">
                                <strong>✅ Ziel erreicht wenn:</strong><br>
                                Dein Kontostand steigt und du mehr als 6.000€/Monat Gewinn machst!
                            </div>
                        ''',
                        'placement': 'center'
                    },
                    {
                        'target': 'body',
                        'title': '📈 Typischer Produktionsplan (Beispiel)',
                        'content': '''
                            <h3>Monat 1: Klein starten (Testphase)</h3>
                            <ul>
                                <li>Einkauf: 1.000-2.000€ für Komponenten</li>
                                <li>Produktion: 5-10 Damenräder/Herrenräder (Standard)</li>
                                <li>Verkauf: Alle auf Domestic Market (~449€)</li>
                                <li><strong>Erwarteter Gewinn: 500-1.500€</strong></li>
                            </ul>

                            <h3>Monat 2-3: Skalieren</h3>
                            <ul>
                                <li>Einkauf: 3.000-5.000€</li>
                                <li>Produktion: 15-20 Fahrräder</li>
                                <li>Mix: 70% Stadtfahrräder, 30% Mountainbikes</li>
                                <li><strong>Erwarteter Gewinn: 2.000-3.000€</strong></li>
                            </ul>

                            <h3>Monat 4+: Volle Kapazität</h3>
                            <ul>
                                <li>Einkauf: 8.000-12.000€</li>
                                <li>Produktion: 30-40 Fahrräder</li>
                                <li>Mix: Stadtfahrräder, Mountainbikes, erste E-Bikes</li>
                                <li>Märkte: Beide (Domestic + EU)</li>
                                <li><strong>Erwarteter Gewinn: 6.000-10.000€</strong></li>
                            </ul>

                            <div style="background-color: #dbeafe; padding: 10px; border-left: 4px solid #3b82f6; margin-top: 10px;">
                                <strong>ℹ️ Wichtige Kennzahlen:</strong><br>
                                • Break-Even: ~30 Fahrräder/Monat<br>
                                • Guter Gewinn: 40-50 Fahrräder/Monat<br>
                                • Maximale Kapazität: ~60-70 Fahrräder/Monat
                            </div>
                        ''',
                        'placement': 'center'
                    },
                    {
                        'target': 'body',
                        'title': '💡 Wichtige Tipps für Anfänger',
                        'content': '''
                            <h3>✅ Do's - Das solltest du tun</h3>
                            <ul>
                                <li><strong>Klein anfangen</strong> - Taste dich langsam heran</li>
                                <li><strong>Kontostand im Auge behalten</strong> - Vermeide Bankrott!</li>
                                <li><strong>Lagerplatz beachten</strong> - Komponenten und Fahrräder brauchen Platz</li>
                                <li><strong>Lieferzeiten einplanen</strong> - Komponenten kommen nicht sofort</li>
                                <li><strong>Nachfrage beachten</strong> - Produziere, was gefragt ist</li>
                                <li><strong>Preise anpassen</strong> - Nicht zu teuer, nicht zu günstig</li>
                            </ul>

                            <h3>❌ Don'ts - Das solltest du vermeiden</h3>
                            <ul>
                                <li><strong>Zu viel auf einmal produzieren</strong> - Start nicht mit 50 Fahrrädern!</li>
                                <li><strong>Lager überfüllen</strong> - Lagerplatz kostet Geld</li>
                                <li><strong>Alles verkaufen wollen</strong> - Manche Fahrräder bleiben liegen</li>
                                <li><strong>Fixkosten ignorieren</strong> - 6.000€/Monat laufen automatisch!</li>
                                <li><strong>Nur E-Bikes produzieren</strong> - Zu teuer für den Anfang</li>
                                <li><strong>Marktforschung ignorieren</strong> - 500€ gut investiert ab Monat 2!</li>
                            </ul>

                            <div style="background-color: #fee2e2; padding: 10px; border-left: 4px solid #ef4444; margin-top: 10px;">
                                <strong>⚠️ Häufigster Anfängerfehler:</strong><br>
                                Zu früh zu viel produzieren! Starte mit 5-10 Fahrrädern und baue dann aus.
                            </div>
                        ''',
                        'placement': 'center'
                    },
                    {
                        'target': 'body',
                        'title': '🎯 Zusammenfassung & Erfolgsformel',
                        'content': '''
                            <h3>Die "Erste 3 Monate" Strategie</h3>

                            <p><strong>Monat 1: Lernen</strong></p>
                            <ul>
                                <li>5-10 einfache Fahrräder</li>
                                <li>Standard-Qualität</li>
                                <li>Nur Domestic Market</li>
                                <li>Ziel: Prozesse verstehen</li>
                            </ul>

                            <p><strong>Monat 2: Optimieren</strong></p>
                            <ul>
                                <li>15-20 Fahrräder</li>
                                <li>Mix aus 2-3 Typen</li>
                                <li>Marktforschung kaufen (500€)</li>
                                <li>Ziel: Profitabel werden</li>
                            </ul>

                            <p><strong>Monat 3: Skalieren</strong></p>
                            <ul>
                                <li>25-35 Fahrräder</li>
                                <li>Beide Märkte nutzen</li>
                                <li>Erste E-Bikes testen</li>
                                <li>Ziel: Wachstum sichern</li>
                            </ul>

                            <hr>

                            <h3>🏆 Erfolgsformel</h3>
                            <div style="background-color: #dcfce7; padding: 15px; border-left: 4px solid #22c55e; margin-top: 10px; font-size: 1.1em;">
                                <strong>Gewinn = (Verkaufspreis × Verkaufte Fahrräder) - (Komponentenkosten + Fixkosten)</strong>
                                <br><br>
                                Beispiel:<br>
                                (449€ × 35 Fahrräder) - (5.600€ + 6.000€) = <strong>4.115€ Gewinn!</strong>
                            </div>

                            <hr>

                            <p style="text-align: center; margin-top: 20px; font-size: 1.2em;">
                                <strong>🚀 Jetzt bist du bereit! Viel Erfolg!</strong>
                            </p>
                        ''',
                        'placement': 'center'
                    }
                ]
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created guide: {guide.title}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Updated guide: {guide.title}'))

        self.stdout.write(self.style.SUCCESS('\nGetting Started guide is now available in the help system!'))
        self.stdout.write('Users can access it from the dashboard or help section.')
