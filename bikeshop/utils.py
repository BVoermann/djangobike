import zipfile
import pandas as pd
from io import BytesIO
from django.core.exceptions import ValidationError


def process_parameter_zip(zip_file):
    """Verarbeitet die hochgeladene ZIP-Datei mit Parametern"""
    parameters = {}

    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            # Erforderliche Dateien prüfen
            required_files = [
                'lieferanten.xlsx',
                'fahrraeder.xlsx',
                'preise_verkauf.xlsx',
                'lager.xlsx',
                'maerkte.xlsx',
                'personal.xlsx',
                'finanzen.xlsx'
            ]

            file_list = zip_ref.namelist()
            missing_files = [f for f in required_files if f not in file_list]

            if missing_files:
                raise ValidationError(f'Fehlende Dateien: {", ".join(missing_files)}')

            # Dateien einlesen
            for filename in required_files:
                file_content = zip_ref.read(filename)

                if filename == 'lieferanten.xlsx':
                    parameters['suppliers'] = read_suppliers_excel(file_content)
                elif filename == 'fahrraeder.xlsx':
                    parameters['bikes'] = read_bikes_excel(file_content)
                elif filename == 'preise_verkauf.xlsx':
                    parameters['bike_prices'] = read_bike_prices_excel(file_content)
                elif filename == 'lager.xlsx':
                    parameters['warehouses'] = read_warehouses_excel(file_content)
                elif filename == 'maerkte.xlsx':
                    parameters['markets'] = read_markets_excel(file_content)
                elif filename == 'personal.xlsx':
                    parameters['workers'] = read_workers_excel(file_content)
                elif filename == 'finanzen.xlsx':
                    parameters['finance'] = read_finance_excel(file_content)

    except Exception as e:
        raise ValidationError(f'Fehler beim Lesen der ZIP-Datei: {str(e)}')

    return parameters


def read_suppliers_excel(file_content):
    """Liest Lieferanten-Daten aus Excel"""
    suppliers_df = pd.read_excel(BytesIO(file_content), sheet_name='Lieferanten')
    prices_df = pd.read_excel(BytesIO(file_content), sheet_name='Preise')

    return {
        'suppliers': suppliers_df.to_dict('records'),
        'prices': prices_df.to_dict('records')
    }


def read_bikes_excel(file_content):
    """Liest Fahrrad-Daten aus Excel"""
    df = pd.read_excel(BytesIO(file_content))
    return df.to_dict('records')


def read_bike_prices_excel(file_content):
    """Liest Verkaufspreise aus Excel"""
    df = pd.read_excel(BytesIO(file_content))
    return df.to_dict('records')


def read_warehouses_excel(file_content):
    """Liest Lager-Daten aus Excel"""
    standorte_df = pd.read_excel(BytesIO(file_content), sheet_name='Standorte')
    lagerplatz_df = pd.read_excel(BytesIO(file_content), sheet_name='Lagerplatz')

    return {
        'locations': standorte_df.to_dict('records'),
        'storage_space': lagerplatz_df.to_dict('records')
    }


def read_markets_excel(file_content):
    """Liest Markt-Daten aus Excel"""
    standorte_df = pd.read_excel(BytesIO(file_content), sheet_name='Standorte')
    nachfrage_df = pd.read_excel(BytesIO(file_content), sheet_name='Nachfrage')
    preissensibilitaet_df = pd.read_excel(BytesIO(file_content), sheet_name='Preissensibilität')

    return {
        'locations': standorte_df.to_dict('records'),
        'demand': nachfrage_df.to_dict('records'),
        'price_sensitivity': preissensibilitaet_df.to_dict('records')
    }


def read_workers_excel(file_content):
    """Liest Personal-Daten aus Excel"""
    df = pd.read_excel(BytesIO(file_content))
    return df.to_dict('records')


def read_finance_excel(file_content):
    """Liest Finanz-Daten aus Excel"""
    startkapital_df = pd.read_excel(BytesIO(file_content), sheet_name='Startkapital')
    kredite_df = pd.read_excel(BytesIO(file_content), sheet_name='Kredite')
    sonstiges_df = pd.read_excel(BytesIO(file_content), sheet_name='Sonstiges')

    return {
        'start_capital': startkapital_df.to_dict('records'),
        'credits': kredite_df.to_dict('records'),
        'other_costs': sonstiges_df.to_dict('records')
    }


def initialize_session_data(session, parameters):
    """Initialisiert eine neue Spielsession mit den geladenen Parametern"""
    from .models import Supplier, ComponentType, Component, SupplierPrice, BikeType, BikePrice, Worker

    # Lieferanten erstellen
    for supplier_data in parameters['suppliers']['suppliers']:
        supplier = Supplier.objects.create(
            session=session,
            name=supplier_data['Name'],
            payment_terms=supplier_data['Zahlungsziel'],
            delivery_time=supplier_data['Lieferzeit'],
            complaint_probability=supplier_data['Reklamationswahrscheinlichkeit'],
            complaint_quantity=supplier_data['Reklamationsanzahl'],
            quality=supplier_data['Qualität'].lower()
        )

    # Komponententypen und Komponenten erstellen
    component_types = {}
    components = {}

    # Dynamisch Komponententypen und Komponenten aus den Preis-Daten erstellen
    unique_component_types = set()
    component_names_by_type = {}
    
    for price_data in parameters['suppliers']['prices']:
        comp_type = price_data['Artikeltyp']
        comp_name = price_data['Artikelname']
        
        unique_component_types.add(comp_type)
        if comp_type not in component_names_by_type:
            component_names_by_type[comp_type] = set()
        component_names_by_type[comp_type].add(comp_name)

    # Storage space für Komponententypen
    storage_spaces = {
        'Laufradsatz': 0.1,
        'Rahmen': 0.2,
        'Lenker': 0.005,
        'Sattel': 0.001,
        'Schaltung': 0.001,
        'Motor': 0.05
    }

    for comp_type in unique_component_types:
        component_type = ComponentType.objects.create(
            session=session,
            name=comp_type,
            storage_space_per_unit=storage_spaces.get(comp_type, 0.01)
        )
        component_types[comp_type] = component_type
        components[comp_type] = {}

        for comp_name in component_names_by_type[comp_type]:
            component = Component.objects.create(
                session=session,
                component_type=component_type,
                name=comp_name
            )
            components[comp_type][comp_name] = component

    # Preise erstellen
    suppliers = {s.name: s for s in Supplier.objects.filter(session=session)}
    for price_data in parameters['suppliers']['prices']:
        supplier = suppliers[price_data['Lieferant']]
        component = components[price_data['Artikeltyp']][price_data['Artikelname']]

        SupplierPrice.objects.create(
            session=session,
            supplier=supplier,
            component=component,
            price=price_data['Preis']
        )

    # Fahrradtypen erstellen
    bike_storage_spaces = {
        'Damenrad': 0.5,
        'E-Bike': 0.6,
        'E-Mountainbike': 0.6,
        'Herrenrad': 0.5,
        'Mountainbike': 0.6,
        'Rennrad': 0.5,
        'E-Mountain-Bike': 0.7
    }

    for bike_data in parameters['bikes']:
        bike_type = BikeType.objects.create(
            session=session,
            name=bike_data['Fahrradtyp'],
            skilled_worker_hours=bike_data['Facharbeiter_Stunden'],
            unskilled_worker_hours=bike_data['Hilfsarbeiter_Stunden'],
            storage_space_per_unit=bike_storage_spaces.get(bike_data['Fahrradtyp'], 0.5),
            wheel_set=components['Laufradsatz'][bike_data['Laufradsatz']],
            frame=components['Rahmen'][bike_data['Rahmen']],
            handlebar=components['Lenker'][bike_data['Lenker']],
            saddle=components['Sattel'][bike_data['Sattel']],
            gearshift=components['Schaltung'][bike_data['Schaltung']],
            motor=components['Motor'].get(bike_data['Motor']) if bike_data['Motor'] != 'NULL' else None
        )

    # Verkaufspreise erstellen
    for price_data in parameters['bike_prices']:
        bike_type = BikeType.objects.filter(session=session, name=price_data['Fahrradtyp']).first()

        BikePrice.objects.create(
            session=session,
            bike_type=bike_type,
            price_segment='cheap',
            price=price_data['Preis_Guenstig']
        )
        BikePrice.objects.create(
            session=session,
            bike_type=bike_type,
            price_segment='standard',
            price=price_data['Preis_Standard']
        )
        BikePrice.objects.create(
            session=session,
            bike_type=bike_type,
            price_segment='premium',
            price=price_data['Preis_Premium']
        )

    # Arbeiter erstellen
    for worker_data in parameters['workers']:
        Worker.objects.create(
            session=session,
            worker_type='skilled' if worker_data['Arbeitertyp'] == 'Facharbeiter' else 'unskilled',
            hourly_wage=worker_data['Stundenlohn'],
            monthly_hours=worker_data['Monatsstunden'],
            count=2 if worker_data['Arbeitertyp'] == 'Hilfsarbeiter' else 1  # Startwerte
        )
