# Django Bikeshop Simulation - XLSX Files Documentation

This document explains the structure and content of the required XLSX files for the Django bikeshop simulation.

## Required Files

The simulation requires a ZIP file containing exactly 8 XLSX files:

### 1. `lieferanten.xlsx` (Suppliers)
Contains supplier information and component prices.

**Sheets:**
- **Lieferanten**: Supplier details
  - `Name`: Supplier name
  - `Zahlungsziel`: Payment terms (days)
  - `Lieferzeit`: Delivery time (days)
  - `Reklamationswahrscheinlichkeit`: Complaint probability (%)
  - `Reklamationsanzahl`: Complaint quantity (%)
  - `Qualität`: Quality level (Basic/Standard/Premium)

- **Preise**: Component prices per supplier
  - `Lieferant`: Supplier name
  - `Artikeltyp`: Component type
  - `Artikelname`: Component name
  - `Preis`: Price in EUR

### 2. `fahrraeder.xlsx` (Bicycles)
Defines bicycle types and their required components.

**Columns:**
- `Fahrradtyp`: Bicycle type
- `Facharbeiter_Stunden`: Skilled worker hours required
- `Hilfsarbeiter_Stunden`: Unskilled worker hours required
- `Laufradsatz`: Required wheel set
- `Rahmen`: Required frame
- `Lenker`: Required handlebar
- `Sattel`: Required saddle
- `Schaltung`: Required gearshift
- `Motor`: Required motor (NULL for non-electric bikes)

### 3. `preise_verkauf.xlsx` (Sales Prices)
Selling prices for different bicycle types and price segments.

**Columns:**
- `Fahrradtyp`: Bicycle type
- `Preis_Guenstig`: Budget price segment
- `Preis_Standard`: Standard price segment
- `Preis_Premium`: Premium price segment

### 4. `lager.xlsx` (Warehouse)
Warehouse locations and storage space requirements.

**Sheets:**
- **Standorte**: Warehouse locations
  - `Standort`: Location name
  - `Miete_pro_qm`: Rent per square meter
  - `Verfuegbare_Flaeche`: Available space (m²)
  - `Entfernung_zu_Produktion`: Distance to production (km)

- **Lagerplatz**: Storage space per component
  - `Artikel`: Component type
  - `Lagerplatz_pro_Einheit`: Storage space per unit (m²)

### 5. `maerkte.xlsx` (Markets)
Market information including demand and price sensitivity.

**Sheets:**
- **Standorte**: Market locations
  - `Markt`: Market name
  - `Entfernung`: Distance from production (km)
  - `Transportkosten_pro_km`: Transport cost per km

- **Nachfrage**: Market demand
  - `Markt`: Market name
  - `Fahrradtyp`: Bicycle type
  - `Nachfrage_pro_Monat`: Monthly demand

- **Preissensibilität**: Price sensitivity
  - `Markt`: Market name
  - `Fahrradtyp`: Bicycle type
  - `Preissensibilität`: Price sensitivity factor

### 6. `personal.xlsx` (Personnel)
Worker types and their costs.

**Columns:**
- `Arbeitertyp`: Worker type (Facharbeiter/Hilfsarbeiter)
- `Stundenlohn`: Hourly wage
- `Monatsstunden`: Monthly working hours

### 7. `finanzen.xlsx` (Finance)
Financial parameters including starting capital and available credits.

**Sheets:**
- **Startkapital**: Starting capital
  - `Startkapital`: Starting capital amount
  - `Waehrung`: Currency

- **Kredite**: Available credits
  - `Kreditgeber`: Credit provider
  - `Maximaler_Betrag`: Maximum amount
  - `Zinssatz`: Interest rate (%)
  - `Laufzeit_Monate`: Term in months

- **Sonstiges**: Other monthly costs
  - `Kostenart`: Cost type
  - `Betrag_pro_Monat`: Monthly amount

- **Transportkosten**: Transport cost parameters
  - `Transportart`: Transport type (Standard Lieferung, Express Lieferung, etc.)
  - `Kosten_pro_km`: Cost per kilometer
  - `Basis_Transportkosten`: Base transport cost
  - `Mindestkosten`: Minimum cost

### 8. `konkurrenten.xlsx` (AI Competitors)
AI competitor configuration and market dynamics settings.

**Sheets:**
- **Konkurrenten**: AI competitor companies
  - `Name`: Competitor company name
  - `Strategie`: Strategy type (cheap_only, balanced, premium_focus, e_bike_specialist)
  - `Startkapital`: Starting financial resources
  - `Marktanteil_Start`: Initial market share percentage
  - `Aggressivität`: Aggressiveness factor (0.0-1.0)
  - `Effizienz`: Production efficiency (0.0-1.0)
  - `Wachstumsrate`: Monthly growth rate
  - `Aktiv`: Whether competitor is active (True/False)

- **Strategien**: Strategy behavior configuration
  - `Strategie`: Strategy identifier
  - `Bezeichnung`: Strategy display name
  - `Günstig_Anteil`: Ratio for cheap price segment (0.0-1.0)
  - `Standard_Anteil`: Ratio for standard price segment (0.0-1.0)
  - `Premium_Anteil`: Ratio for premium price segment (0.0-1.0)
  - `Preisfaktor`: Price adjustment factor
  - `Produktionsvolumen`: Production volume multiplier
  - `Qualitätsfokus`: Quality focus factor (0.0-1.0)
  - `Marketingbudget`: Marketing budget percentage

- **Marktdynamik**: Market dynamics settings
  - `Parameter`: Parameter name
  - `Wert`: Parameter value
  - `Beschreibung`: Parameter description

- **Fahrradtyp_Vorlieben**: Bike type preferences per strategy
  - `Strategie`: Strategy identifier
  - `Fahrradtyp`: Bicycle type name
  - `Vorliebe`: Preference weight (0.0-1.0)
  - `Produktionswahrscheinlichkeit`: Production probability (0.0-1.0)

## Component Types and Variants

The simulation includes the following component types:

- **Laufradsatz** (Wheel Sets): Alpin, Ampere, Speed, Standard
- **Rahmen** (Frames): Herrenrahmen Basic, Damenrahmen Basic, Mountain Basic, Renn Basic
- **Lenker** (Handlebars): Comfort, Sport
- **Sattel** (Saddles): Comfort, Sport
- **Schaltung** (Gearshifts): Albatross, Gepard
- **Motor** (Motors): Standard, Mountain (only for E-bikes)

## Bicycle Types

The simulation supports these bicycle types:
- Damenrad (Women's bike)
- Herrenrad (Men's bike)
- Mountainbike
- Rennrad (Racing bike)
- E-Bike
- E-Mountainbike

## Usage

1. Ensure all 8 XLSX files are present
2. Create a ZIP file containing all files
3. Upload the ZIP file through the Django application's parameter upload interface
4. The system will validate and process the files to initialize a new simulation session

## AI Competitor Customization

The `konkurrenten.xlsx` file allows you to:
- **Enable/Disable Competitors**: Set `Aktiv` to True/False
- **Adjust Difficulty**: Modify competitor financial resources and efficiency
- **Create New Strategies**: Define custom strategy behaviors
- **Fine-tune Market Dynamics**: Adjust competition intensity and market saturation
- **Customize Bike Preferences**: Set which bike types each strategy prefers

## Default Values

The provided default files contain realistic sample data suitable for testing and learning the simulation. You can modify these values to create different scenarios or difficulty levels. 