#!/usr/bin/env python3
"""
Script to create default XLSX files for the Django bikeshop simulation.
This creates all 7 required files with realistic sample data.
"""

import pandas as pd
import os
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

def create_lieferanten_xlsx():
    """Create lieferanten.xlsx with suppliers and their prices"""
    
    # Suppliers sheet
    suppliers_data = [
        {
            'Name': 'BikeComponents GmbH',
            'Zahlungsziel': 30,
            'Lieferzeit': 14,
            'Reklamationswahrscheinlichkeit': 2.5,
            'Reklamationsanzahl': 1.2,
            'Qualität': 'Standard'
        },
        {
            'Name': 'Premium Parts AG',
            'Zahlungsziel': 45,
            'Lieferzeit': 21,
            'Reklamationswahrscheinlichkeit': 1.0,
            'Reklamationsanzahl': 0.8,
            'Qualität': 'Premium'
        },
        {
            'Name': 'Budget Bike Supply',
            'Zahlungsziel': 14,
            'Lieferzeit': 7,
            'Reklamationswahrscheinlichkeit': 5.0,
            'Reklamationsanzahl': 2.5,
            'Qualität': 'Basic'
        },
        {
            'Name': 'EuroCycle Distribution',
            'Zahlungsziel': 30,
            'Lieferzeit': 10,
            'Reklamationswahrscheinlichkeit': 2.0,
            'Reklamationsanzahl': 1.0,
            'Qualität': 'Standard'
        }
    ]
    
    # Prices sheet
    prices_data = []
    suppliers = ['BikeComponents GmbH', 'Premium Parts AG', 'Budget Bike Supply', 'EuroCycle Distribution']
    
    # Component types and their variants (UPDATED with new components)
    components = {
        'Laufradsatz': ['Alpin', 'Ampere', 'Speed', 'Standard', 'E-Mountain Pro'],
        'Rahmen': ['Herrenrahmen Basic', 'Damenrahmen Basic', 'Mountain Basic', 'Renn Basic', 'E-Mountain Carbon'],
        'Lenker': ['Comfort', 'Sport', 'E-Mountain Pro'],
        'Sattel': ['Comfort', 'Sport', 'E-Mountain Pro'],
        'Schaltung': ['Albatross', 'Gepard', 'E-Mountain Electronic'],
        'Motor': ['Standard', 'Mountain', 'High-Performance E-Motor']
    }
    
    # Base prices for different component types (UPDATED with new components)
    base_prices = {
        'Laufradsatz': {'Alpin': 120, 'Ampere': 150, 'Speed': 180, 'Standard': 100, 'E-Mountain Pro': 280},
        'Rahmen': {'Herrenrahmen Basic': 80, 'Damenrahmen Basic': 80, 'Mountain Basic': 120, 'Renn Basic': 100, 'E-Mountain Carbon': 350},
        'Lenker': {'Comfort': 25, 'Sport': 35, 'E-Mountain Pro': 65},
        'Sattel': {'Comfort': 30, 'Sport': 45, 'E-Mountain Pro': 85},
        'Schaltung': {'Albatross': 60, 'Gepard': 85, 'E-Mountain Electronic': 180},
        'Motor': {'Standard': 300, 'Mountain': 450, 'High-Performance E-Motor': 650}
    }
    
    # Price multipliers for different suppliers
    supplier_multipliers = {
        'BikeComponents GmbH': 1.0,
        'Premium Parts AG': 1.3,
        'Budget Bike Supply': 0.8,
        'EuroCycle Distribution': 0.95
    }
    
    for supplier in suppliers:
        for comp_type, comp_list in components.items():
            for comp_name in comp_list:
                base_price = base_prices[comp_type][comp_name]
                final_price = round(base_price * supplier_multipliers[supplier], 2)
                prices_data.append({
                    'Lieferant': supplier,
                    'Artikeltyp': comp_type,
                    'Artikelname': comp_name,
                    'Preis': final_price
                })
    
    # Create Excel file with multiple sheets
    with pd.ExcelWriter('lieferanten.xlsx', engine='openpyxl') as writer:
        pd.DataFrame(suppliers_data).to_excel(writer, sheet_name='Lieferanten', index=False)
        pd.DataFrame(prices_data).to_excel(writer, sheet_name='Preise', index=False)

def create_fahrraeder_xlsx():
    """Create fahrraeder.xlsx with bike types and their components"""
    
    bikes_data = [
        {
            'Fahrradtyp': 'Damenrad',
            'Facharbeiter_Stunden': 3.5,
            'Hilfsarbeiter_Stunden': 2.0,
            'Laufradsatz': 'Standard',
            'Rahmen': 'Damenrahmen Basic',
            'Lenker': 'Comfort',
            'Sattel': 'Comfort',
            'Schaltung': 'Albatross',
            'Motor': 'NULL'
        },
        {
            'Fahrradtyp': 'Herrenrad',
            'Facharbeiter_Stunden': 3.5,
            'Hilfsarbeiter_Stunden': 2.0,
            'Laufradsatz': 'Standard',
            'Rahmen': 'Herrenrahmen Basic',
            'Lenker': 'Comfort',
            'Sattel': 'Comfort',
            'Schaltung': 'Albatross',
            'Motor': 'NULL'
        },
        {
            'Fahrradtyp': 'Mountainbike',
            'Facharbeiter_Stunden': 4.0,
            'Hilfsarbeiter_Stunden': 2.5,
            'Laufradsatz': 'Alpin',
            'Rahmen': 'Mountain Basic',
            'Lenker': 'Sport',
            'Sattel': 'Sport',
            'Schaltung': 'Gepard',
            'Motor': 'NULL'
        },
        {
            'Fahrradtyp': 'Rennrad',
            'Facharbeiter_Stunden': 4.5,
            'Hilfsarbeiter_Stunden': 1.5,
            'Laufradsatz': 'Speed',
            'Rahmen': 'Renn Basic',
            'Lenker': 'Sport',
            'Sattel': 'Sport',
            'Schaltung': 'Gepard',
            'Motor': 'NULL'
        },
        {
            'Fahrradtyp': 'E-Bike',
            'Facharbeiter_Stunden': 5.0,
            'Hilfsarbeiter_Stunden': 3.0,
            'Laufradsatz': 'Ampere',
            'Rahmen': 'Damenrahmen Basic',
            'Lenker': 'Comfort',
            'Sattel': 'Comfort',
            'Schaltung': 'Albatross',
            'Motor': 'Standard'
        },
        {
            'Fahrradtyp': 'E-Mountainbike',
            'Facharbeiter_Stunden': 5.5,
            'Hilfsarbeiter_Stunden': 3.5,
            'Laufradsatz': 'Alpin',
            'Rahmen': 'Mountain Basic',
            'Lenker': 'Sport',
            'Sattel': 'Sport',
            'Schaltung': 'Gepard',
            'Motor': 'Mountain'
        },
        {
            'Fahrradtyp': 'E-Mountain-Bike',
            'Facharbeiter_Stunden': 8.5,
            'Hilfsarbeiter_Stunden': 4.0,
            'Laufradsatz': 'E-Mountain Pro',
            'Rahmen': 'E-Mountain Carbon',
            'Lenker': 'E-Mountain Pro',
            'Sattel': 'E-Mountain Pro',
            'Schaltung': 'E-Mountain Electronic',
            'Motor': 'High-Performance E-Motor'
        }
    ]
    
    df = pd.DataFrame(bikes_data)
    df.to_excel('fahrraeder.xlsx', index=False)

def create_preise_verkauf_xlsx():
    """Create preise_verkauf.xlsx with selling prices for bikes"""
    
    prices_data = [
        {
            'Fahrradtyp': 'Damenrad',
            'Preis_Guenstig': 299.99,
            'Preis_Standard': 399.99,
            'Preis_Premium': 549.99
        },
        {
            'Fahrradtyp': 'Herrenrad',
            'Preis_Guenstig': 299.99,
            'Preis_Standard': 399.99,
            'Preis_Premium': 549.99
        },
        {
            'Fahrradtyp': 'Mountainbike',
            'Preis_Guenstig': 449.99,
            'Preis_Standard': 649.99,
            'Preis_Premium': 899.99
        },
        {
            'Fahrradtyp': 'Rennrad',
            'Preis_Guenstig': 599.99,
            'Preis_Standard': 899.99,
            'Preis_Premium': 1299.99
        },
        {
            'Fahrradtyp': 'E-Bike',
            'Preis_Guenstig': 1199.99,
            'Preis_Standard': 1599.99,
            'Preis_Premium': 2199.99
        },
        {
            'Fahrradtyp': 'E-Mountainbike',
            'Preis_Guenstig': 1499.99,
            'Preis_Standard': 1999.99,
            'Preis_Premium': 2799.99
        },
        {
            'Fahrradtyp': 'E-Mountain-Bike',
            'Preis_Guenstig': 2499.99,
            'Preis_Standard': 3299.99,
            'Preis_Premium': 4499.99
        }
    ]
    
    df = pd.DataFrame(prices_data)
    df.to_excel('preise_verkauf.xlsx', index=False)

def create_lager_xlsx():
    """Create lager.xlsx with warehouse locations and storage space"""
    
    # Warehouse locations
    standorte_data = [
        {
            'Standort': 'Hamburg',
            'Miete_pro_qm': 12.50,
            'Verfuegbare_Flaeche': 200,  # Reduced from 1000 to realistic size
            'Entfernung_zu_Produktion': 0
        },
        {
            'Standort': 'Berlin',
            'Miete_pro_qm': 15.00,
            'Verfuegbare_Flaeche': 150,  # Reduced from 800
            'Entfernung_zu_Produktion': 300
        },
        {
            'Standort': 'München',
            'Miete_pro_qm': 18.00,
            'Verfuegbare_Flaeche': 120,  # Reduced from 600
            'Entfernung_zu_Produktion': 600
        },
        {
            'Standort': 'Köln',
            'Miete_pro_qm': 14.00,
            'Verfuegbare_Flaeche': 180,  # Reduced from 750
            'Entfernung_zu_Produktion': 400
        }
    ]
    
    # Storage space requirements
    lagerplatz_data = [
        {
            'Artikel': 'Laufradsatz',
            'Lagerplatz_pro_Einheit': 0.1
        },
        {
            'Artikel': 'Rahmen',
            'Lagerplatz_pro_Einheit': 0.2
        },
        {
            'Artikel': 'Lenker',
            'Lagerplatz_pro_Einheit': 0.005
        },
        {
            'Artikel': 'Sattel',
            'Lagerplatz_pro_Einheit': 0.001
        },
        {
            'Artikel': 'Schaltung',
            'Lagerplatz_pro_Einheit': 0.001
        },
        {
            'Artikel': 'Motor',
            'Lagerplatz_pro_Einheit': 0.05
        }
    ]
    
    # Create Excel file with multiple sheets
    with pd.ExcelWriter('lager.xlsx', engine='openpyxl') as writer:
        pd.DataFrame(standorte_data).to_excel(writer, sheet_name='Standorte', index=False)
        pd.DataFrame(lagerplatz_data).to_excel(writer, sheet_name='Lagerplatz', index=False)

def create_maerkte_xlsx():
    """Create maerkte.xlsx with market data"""
    
    # Market locations
    standorte_data = [
        {
            'Markt': 'Hamburg',
            'Entfernung': 0,
            'Transportkosten_pro_km': 0.10  # Reduced from €0.50 to €0.10
        },
        {
            'Markt': 'Berlin',
            'Entfernung': 300,
            'Transportkosten_pro_km': 0.10  # Transport: €30 instead of €150
        },
        {
            'Markt': 'München',
            'Entfernung': 600,
            'Transportkosten_pro_km': 0.10  # Transport: €60 instead of €300
        },
        {
            'Markt': 'Köln',
            'Entfernung': 400,
            'Transportkosten_pro_km': 0.10  # Transport: €40 instead of €200
        },
        {
            'Markt': 'Frankfurt',
            'Entfernung': 500,
            'Transportkosten_pro_km': 0.10  # Transport: €50 instead of €250
        }
    ]
    
    # Market demand
    nachfrage_data = []
    markets = ['Hamburg', 'Berlin', 'München', 'Köln', 'Frankfurt']
    bike_types = ['Damenrad', 'Herrenrad', 'Mountainbike', 'Rennrad', 'E-Bike', 'E-Mountainbike', 'E-Mountain-Bike']
    
    # Base demand per market and bike type
    base_demand = {
        'Damenrad': 50,
        'Herrenrad': 45,
        'Mountainbike': 30,
        'Rennrad': 20,
        'E-Bike': 35,
        'E-Mountainbike': 25,
        'E-Mountain-Bike': 15
    }
    
    # Market size multipliers
    market_multipliers = {
        'Hamburg': 1.0,
        'Berlin': 1.5,
        'München': 1.2,
        'Köln': 0.8,
        'Frankfurt': 0.9
    }
    
    for market in markets:
        for bike_type in bike_types:
            demand = int(base_demand[bike_type] * market_multipliers[market])
            nachfrage_data.append({
                'Markt': market,
                'Fahrradtyp': bike_type,
                'Nachfrage_pro_Monat': demand
            })
    
    # Price sensitivity
    preissensibilitaet_data = []
    for market in markets:
        for bike_type in bike_types:
            # Higher price sensitivity for basic bikes, lower for premium bikes
            if bike_type in ['Damenrad', 'Herrenrad']:
                sensitivity = 0.8
            elif bike_type in ['Mountainbike', 'Rennrad']:
                sensitivity = 0.6
            elif bike_type == 'E-Mountain-Bike':
                sensitivity = 0.3  # Very low sensitivity for premium E-Mountain-Bike
            else:  # Other E-bikes
                sensitivity = 0.4
            
            preissensibilitaet_data.append({
                'Markt': market,
                'Fahrradtyp': bike_type,
                'Preissensibilität': sensitivity
            })
    
    # Create Excel file with multiple sheets
    with pd.ExcelWriter('maerkte.xlsx', engine='openpyxl') as writer:
        pd.DataFrame(standorte_data).to_excel(writer, sheet_name='Standorte', index=False)
        pd.DataFrame(nachfrage_data).to_excel(writer, sheet_name='Nachfrage', index=False)
        pd.DataFrame(preissensibilitaet_data).to_excel(writer, sheet_name='Preissensibilität', index=False)

def create_personal_xlsx():
    """Create personal.xlsx with worker data"""
    
    workers_data = [
        {
            'Arbeitertyp': 'Facharbeiter',
            'Stundenlohn': 25.00,
            'Monatsstunden': 160
        },
        {
            'Arbeitertyp': 'Hilfsarbeiter',
            'Stundenlohn': 15.00,
            'Monatsstunden': 160
        }
    ]
    
    df = pd.DataFrame(workers_data)
    df.to_excel('personal.xlsx', index=False)

def create_konkurrenten_xlsx():
    """Create konkurrenten.xlsx with AI competitor configuration"""
    
    # AI Competitors
    competitors_data = [
        {
            'Name': 'BudgetCycles GmbH',
            'Strategie': 'cheap_only',
            'Startkapital': 45000.00,
            'Marktanteil_Start': 18.0,
            'Aggressivität': 0.8,
            'Effizienz': 0.6,
            'Wachstumsrate': 0.05,
            'Aktiv': True
        },
        {
            'Name': 'CycleTech Solutions',
            'Strategie': 'balanced',
            'Startkapital': 65000.00,
            'Marktanteil_Start': 22.0,
            'Aggressivität': 0.5,
            'Effizienz': 0.8,
            'Wachstumsrate': 0.08,
            'Aktiv': True
        },
        {
            'Name': 'PremiumWheels AG',
            'Strategie': 'premium_focus',
            'Startkapital': 55000.00,
            'Marktanteil_Start': 12.0,
            'Aggressivität': 0.3,
            'Effizienz': 0.9,
            'Wachstumsrate': 0.03,
            'Aktiv': True
        },
        {
            'Name': 'E-Motion Bikes',
            'Strategie': 'e_bike_specialist',
            'Startkapital': 60000.00,
            'Marktanteil_Start': 16.0,
            'Aggressivität': 0.6,
            'Effizienz': 0.7,
            'Wachstumsrate': 0.12,
            'Aktiv': True
        },
        {
            'Name': 'FastTrack Racing',
            'Strategie': 'premium_focus',
            'Startkapital': 40000.00,
            'Marktanteil_Start': 8.0,
            'Aggressivität': 0.4,
            'Effizienz': 0.85,
            'Wachstumsrate': 0.06,
            'Aktiv': False
        }
    ]
    
    # Strategy configurations
    strategien_data = [
        {
            'Strategie': 'cheap_only',
            'Bezeichnung': 'Billig-Strategie',
            'Günstig_Anteil': 0.7,
            'Standard_Anteil': 0.25,
            'Premium_Anteil': 0.05,
            'Preisfaktor': 0.75,
            'Produktionsvolumen': 1.4,
            'Qualitätsfokus': 0.3,
            'Marketingbudget': 0.05
        },
        {
            'Strategie': 'balanced',
            'Bezeichnung': 'Ausgewogene Strategie',
            'Günstig_Anteil': 0.4,
            'Standard_Anteil': 0.4,
            'Premium_Anteil': 0.2,
            'Preisfaktor': 1.0,
            'Produktionsvolumen': 1.0,
            'Qualitätsfokus': 0.6,
            'Marketingbudget': 0.08
        },
        {
            'Strategie': 'premium_focus',
            'Bezeichnung': 'Premium-Fokus',
            'Günstig_Anteil': 0.1,
            'Standard_Anteil': 0.3,
            'Premium_Anteil': 0.6,
            'Preisfaktor': 1.3,
            'Produktionsvolumen': 0.6,
            'Qualitätsfokus': 0.9,
            'Marketingbudget': 0.12
        },
        {
            'Strategie': 'e_bike_specialist',
            'Bezeichnung': 'E-Bike Spezialist',
            'Günstig_Anteil': 0.2,
            'Standard_Anteil': 0.5,
            'Premium_Anteil': 0.3,
            'Preisfaktor': 1.1,
            'Produktionsvolumen': 0.8,
            'Qualitätsfokus': 0.7,
            'Marketingbudget': 0.10
        }
    ]
    
    # Market dynamics settings
    marktdynamik_data = [
        {
            'Parameter': 'Basiswettbewerb',
            'Wert': 0.15,
            'Beschreibung': 'Grundlegende Wettbewerbsintensität'
        },
        {
            'Parameter': 'Sättigungsgrenze',
            'Wert': 1.5,
            'Beschreibung': 'Markt gilt als gesättigt ab diesem Nachfrage-Faktor'
        },
        {
            'Parameter': 'Preisdruck_Maximum',
            'Wert': 0.4,
            'Beschreibung': 'Maximaler Preisdruck-Effekt'
        },
        {
            'Parameter': 'Saisonalität_Stärke',
            'Wert': 0.2,
            'Beschreibung': 'Stärke der saisonalen Schwankungen'
        },
        {
            'Parameter': 'KI_Lernrate',
            'Wert': 0.05,
            'Beschreibung': 'Anpassungsgeschwindigkeit der KI-Konkurrenten'
        },
        {
            'Parameter': 'Marktanteil_Volatilität',
            'Wert': 0.1,
            'Beschreibung': 'Schwankung der Marktanteile pro Monat'
        }
    ]
    
    # Bike type preferences for strategies
    fahrradtyp_vorlieben_data = []
    strategies = ['cheap_only', 'balanced', 'premium_focus', 'e_bike_specialist']
    bike_types = ['Damenrad', 'Herrenrad', 'Mountainbike', 'Rennrad', 'E-Bike', 'E-Mountainbike', 'E-Mountain-Bike']
    
    # Define preferences for each strategy-bike combination
    preferences = {
        'cheap_only': {
            'Damenrad': 0.25, 'Herrenrad': 0.25, 'Mountainbike': 0.2,
            'Rennrad': 0.1, 'E-Bike': 0.1, 'E-Mountainbike': 0.05, 'E-Mountain-Bike': 0.05
        },
        'balanced': {
            'Damenrad': 0.18, 'Herrenrad': 0.18, 'Mountainbike': 0.15,
            'Rennrad': 0.12, 'E-Bike': 0.15, 'E-Mountainbike': 0.12, 'E-Mountain-Bike': 0.10
        },
        'premium_focus': {
            'Damenrad': 0.05, 'Herrenrad': 0.05, 'Mountainbike': 0.15,
            'Rennrad': 0.25, 'E-Bike': 0.15, 'E-Mountainbike': 0.15, 'E-Mountain-Bike': 0.20
        },
        'e_bike_specialist': {
            'Damenrad': 0.05, 'Herrenrad': 0.05, 'Mountainbike': 0.05,
            'Rennrad': 0.05, 'E-Bike': 0.35, 'E-Mountainbike': 0.25, 'E-Mountain-Bike': 0.20
        }
    }
    
    for strategy in strategies:
        for bike_type in bike_types:
            fahrradtyp_vorlieben_data.append({
                'Strategie': strategy,
                'Fahrradtyp': bike_type,
                'Vorliebe': preferences[strategy][bike_type],
                'Produktionswahrscheinlichkeit': preferences[strategy][bike_type]
            })
    
    # Create Excel file with multiple sheets
    with pd.ExcelWriter('konkurrenten.xlsx', engine='openpyxl') as writer:
        pd.DataFrame(competitors_data).to_excel(writer, sheet_name='Konkurrenten', index=False)
        pd.DataFrame(strategien_data).to_excel(writer, sheet_name='Strategien', index=False)
        pd.DataFrame(marktdynamik_data).to_excel(writer, sheet_name='Marktdynamik', index=False)
        pd.DataFrame(fahrradtyp_vorlieben_data).to_excel(writer, sheet_name='Fahrradtyp_Vorlieben', index=False)


def create_finanzen_xlsx():
    """Create finanzen.xlsx with financial data"""
    
    # Starting capital
    startkapital_data = [
        {
            'Startkapital': 80000.00,
            'Waehrung': 'EUR'
        }
    ]
    
    # Available credits
    kredite_data = [
        {
            'Kreditgeber': 'Hausbank',
            'Maximaler_Betrag': 50000.00,
            'Zinssatz': 4.5,
            'Laufzeit_Monate': 60
        },
        {
            'Kreditgeber': 'Förderbank',
            'Maximaler_Betrag': 30000.00,
            'Zinssatz': 2.8,
            'Laufzeit_Monate': 48
        },
        {
            'Kreditgeber': 'Schnellkredit',
            'Maximaler_Betrag': 20000.00,
            'Zinssatz': 8.9,
            'Laufzeit_Monate': 24
        },
        {
            'Kreditgeber': 'Sofortkredit',
            'Maximaler_Betrag': 15000.00,
            'Zinssatz': 12.9,
            'Laufzeit_Monate': 12
        }
    ]
    
    # Other costs
    sonstiges_data = [
        {
            'Kostenart': 'Miete Produktionshalle',
            'Betrag_pro_Monat': 3500.00
        },
        {
            'Kostenart': 'Strom',
            'Betrag_pro_Monat': 800.00
        },
        {
            'Kostenart': 'Versicherungen',
            'Betrag_pro_Monat': 450.00
        },
        {
            'Kostenart': 'Verwaltung',
            'Betrag_pro_Monat': 1200.00
        },
        {
            'Kostenart': 'Marketing',
            'Betrag_pro_Monat': 600.00
        }
    ]
    
    # Transport costs
    transportkosten_data = [
        {
            'Transportart': 'Standard Lieferung',
            'Kosten_pro_km': 0.50,
            'Basis_Transportkosten': 5.00,
            'Mindestkosten': 10.00
        },
        {
            'Transportart': 'Express Lieferung',
            'Kosten_pro_km': 0.80,
            'Basis_Transportkosten': 8.00,
            'Mindestkosten': 15.00
        },
        {
            'Transportart': 'Sperrgut',
            'Kosten_pro_km': 1.20,
            'Basis_Transportkosten': 12.00,
            'Mindestkosten': 25.00
        }
    ]
    
    # Create Excel file with multiple sheets
    with pd.ExcelWriter('finanzen.xlsx', engine='openpyxl') as writer:
        pd.DataFrame(startkapital_data).to_excel(writer, sheet_name='Startkapital', index=False)
        pd.DataFrame(kredite_data).to_excel(writer, sheet_name='Kredite', index=False)
        pd.DataFrame(sonstiges_data).to_excel(writer, sheet_name='Sonstiges', index=False)
        pd.DataFrame(transportkosten_data).to_excel(writer, sheet_name='Transportkosten', index=False)

def main():
    """Create all required XLSX files"""
    print("Creating default XLSX files for Django bikeshop simulation...")
    
    try:
        create_lieferanten_xlsx()
        print("✓ Created lieferanten.xlsx")
        
        create_fahrraeder_xlsx()
        print("✓ Created fahrraeder.xlsx")
        
        create_preise_verkauf_xlsx()
        print("✓ Created preise_verkauf.xlsx")
        
        create_lager_xlsx()
        print("✓ Created lager.xlsx")
        
        create_maerkte_xlsx()
        print("✓ Created maerkte.xlsx")
        
        create_personal_xlsx()
        print("✓ Created personal.xlsx")
        
        create_finanzen_xlsx()
        print("✓ Created finanzen.xlsx")
        
        create_konkurrenten_xlsx()
        print("✓ Created konkurrenten.xlsx")
        
        print("\nAll files created successfully!")
        print("You can now zip these files and upload them to the bikeshop simulation.")
        
    except Exception as e:
        print(f"Error creating files: {e}")

if __name__ == "__main__":
    main() 