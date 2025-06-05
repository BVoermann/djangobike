# manage.py
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

if __name__ == '__main__':
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bike_simulator.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)




# README.md
# Fahrradladen-Simulator

Ein umfassender Django-basierter Simulator für die Verwaltung eines Fahrradladens mit Einkauf, Produktion, Lager, Finanzen und Verkauf.

## Installation

1. **Repository klonen**
```bash
git clone <repository-url>
cd bike_simulator
```

2. **Virtuelle Umgebung erstellen**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows
```

3. **Dependencies installieren**
```bash
pip install -r requirements.txt
```

4. **Datenbank einrichten**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Superuser erstellen (optional)**
```bash
python manage.py createsuperuser
```

6. **Server starten**
```bash
python manage.py runserver
```

Die Anwendung ist dann unter `http://127.0.0.1:8000/` erreichbar.

## Features

### Kernfunktionalität
- **Parametrisierte Simulation**: Alle Simulationsparameter werden über Excel-Dateien in einer ZIP-Datei eingelesen
- **Mehrspieler-fähig**: Jeder Benutzer kann mehrere Spielsessions parallel verwalten
- **Monatliche Zyklen**: Das Spiel läuft in monatlichen Zyklen mit automatischen Berechnungen

### Module

1. **Einkauf (Procurement)**
   - Bestellung von 6 verschiedenen Komponententypen
   - 6 verschiedene Lieferanten mit individuellen Preisen und Qualitätsstufen
   - Reklamationssystem mit Wahrscheinlichkeiten
   - Zahlungsziele und Lieferzeiten

2. **Produktion (Production)**
   - Produktion von 6 verschiedenen Fahrradtypen
   - Fach- und Hilfsarbeiter mit Stundenkapazitäten
   - Materialverbrauch und Verfügbarkeitsprüfung
   - Drei Qualitätsstufen (günstig, standard, premium)

3. **Lager (Warehouse)**
   - Zwei Lager (Deutschland und Frankreich)
   - Kapazitätsverwaltung in m²
   - Lagerkosten und Transportkosten
   - Automatische Platzberechnung

4. **Finanzen (Finance)**
   - Guthaben-Management
   - Drei Kredittypen mit verschiedenen Konditionen
   - Monatliche Transaktionsübersicht
   - Automatische Lohn- und Kostenabrechnungen

5. **Verkauf (Sales)**
   - Zwei Märkte (Münster und Toulouse)
   - Marktspezifische Nachfragepräferenzen
   - Saisonale Effekte
   - Preissensibilität der Kunden

6. **Simulation Engine**
   - Automatische Monatsverarbeitung
   - Lieferungen, Produktion, Löhne, Verkäufe
   - Reklamationsabwicklung
   - Markttrends und saisonale Effekte

### Parameter-Dateien

Die Simulation wird über eine ZIP-Datei mit folgenden Excel-Dateien konfiguriert:

- `lieferanten.xlsx`: Lieferanten und deren Preise
- `fahrraeder.xlsx`: Fahrradtypen und benötigte Komponenten
- `preise_verkauf.xlsx`: Verkaufspreise nach Qualitätsstufen
- `lager.xlsx`: Lagerstandorte und Lagerplätze
- `maerkte.xlsx`: Märkte, Nachfrage und Preissensibilität
- `personal.xlsx`: Arbeitertypen und Löhne
- `finanzen.xlsx`: Startkapital, Kredite und sonstige Kosten

## Deployment

### Lokale Entwicklung
```bash
python manage.py runserver
```

### Produktion (beispielhaft für Railway)
1. `railway.json` erstellen:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python manage.py collectstatic --noinput && python manage.py migrate && gunicorn bike_simulator.wsgi:application"
  }
}
```

2. `Procfile` erstellen:
```
web: gunicorn bike_simulator.wsgi:application
```

3. Umgebungsvariablen setzen:
```
DJANGO_SETTINGS_MODULE=bike_simulator.settings
DEBUG=False
```

### Alternative Deployment-Optionen
- **Render.com**: Kostenloses Hosting für Django-Apps
- **PythonAnywhere**: Speziell für Python/Django optimiert
- **Google Cloud Run**: Containerbasiertes Deployment
- **Fly.io**: Moderne Container-Platform

## API-Endpunkte

Die Anwendung bietet verschiedene JSON-APIs für AJAX-Requests:
- `POST /procurement/<session_id>/`: Bestellungen aufgeben
- `POST /production/<session_id>/`: Produktionspläne erstellen
- `POST /finance/<session_id>/`: Kredite aufnehmen
- `POST /sales/<session_id>/`: Verkäufe tätigen
- `POST /simulation/<session_id>/advance/`: Nächsten Monat simulieren

## Technische Details

### Backend
- **Django 4.2**: Web-Framework
- **SQLite**: Datenbank (entwicklung)
- **PostgreSQL**: Empfohlen für Produktion
- **Pandas**: Excel-Datei-Verarbeitung
- **WhiteNoise**: Statische Dateien

### Frontend
- **Bootstrap 5**: UI-Framework
- **Font Awesome**: Icons
- **Chart.js**: Diagramme
- **Vanilla JavaScript**: Interaktivität

### Datenbank-Modelle
- Benutzer-Sessions mit UUID-Schlüsseln
- Normalisierte Datenstruktur für Komponenten und Fahrräder
- Transaktions-Logging für Finanzen
- Historische Daten für Berichte

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz veröffentlicht.

## Support

Bei Fragen oder Problemen erstellen Sie bitte ein Issue im GitHub-Repository.
```
bike_simulator/
├── manage.py
├── requirements.txt
├── bike_simulator/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── bikeshop/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── utils.py
│   └── migrations/
├── procurement/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── migrations/
├── production/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── migrations/
├── warehouse/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── migrations/
├── finance/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── migrations/
├── sales/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── migrations/
├── simulation/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── engine.py
│   └── migrations/
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── procurement/
│   ├── production/
│   ├── warehouse/
│   ├── finance/
│   └── sales/
├── static/
│   ├── css/
│   ├── js/
│   └── img/
└── media/
    └── uploads/
```

## Installation & Setup

1. Virtuelle Umgebung erstellen:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows
```

2. Dependencies installieren:
```bash
pip install -r requirements.txt
```

3. Datenbank migrieren:
```bash
python manage.py migrate
```

4. Superuser erstellen:
```bash
python manage.py createsuperuser
```

5. Server starten:
```bash
python manage.py runserver
```

## Features

- Parametrisierte Simulation via ZIP-Upload
- Einkauf von Komponenten von verschiedenen Lieferanten
- Produktion von 6 verschiedenen Fahrradtypen
- Lager-Management für Deutschland und Frankreich
- Finanz-Management mit Krediten
- Verkauf an Märkten in Münster und Toulouse
- Monatliche Reports und Dashboard
- Saisonale Nachfrageschwankungen
- Reklamations-System

## Parameter-Dateien

Die Simulation wird über eine ZIP-Datei mit Excel-Dateien parametrisiert. Siehe default_parameters.zip für die Struktur.