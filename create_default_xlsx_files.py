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
            'Verfuegbare_Flaeche': 1000,
            'Entfernung_zu_Produktion': 0
        },
        {
            'Standort': 'Berlin',
            'Miete_pro_qm': 15.00,
            'Verfuegbare_Flaeche': 800,
            'Entfernung_zu_Produktion': 300
        },
        {
            'Standort': 'München',
            'Miete_pro_qm': 18.00,
            'Verfuegbare_Flaeche': 600,
            'Entfernung_zu_Produktion': 600
        },
        {
            'Standort': 'Köln',
            'Miete_pro_qm': 14.00,
            'Verfuegbare_Flaeche': 750,
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
            'Transportkosten_pro_km': 0.50
        },
        {
            'Markt': 'Berlin',
            'Entfernung': 300,
            'Transportkosten_pro_km': 0.50
        },
        {
            'Markt': 'München',
            'Entfernung': 600,
            'Transportkosten_pro_km': 0.50
        },
        {
            'Markt': 'Köln',
            'Entfernung': 400,
            'Transportkosten_pro_km': 0.50
        },
        {
            'Markt': 'Frankfurt',
            'Entfernung': 500,
            'Transportkosten_pro_km': 0.50
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
    
    # Create Excel file with multiple sheets
    with pd.ExcelWriter('finanzen.xlsx', engine='openpyxl') as writer:
        pd.DataFrame(startkapital_data).to_excel(writer, sheet_name='Startkapital', index=False)
        pd.DataFrame(kredite_data).to_excel(writer, sheet_name='Kredite', index=False)
        pd.DataFrame(sonstiges_data).to_excel(writer, sheet_name='Sonstiges', index=False)

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
        
        print("\nAll files created successfully!")
        print("You can now zip these files and upload them to the bikeshop simulation.")
        
    except Exception as e:
        print(f"Error creating files: {e}")

if __name__ == "__main__":
    main() 