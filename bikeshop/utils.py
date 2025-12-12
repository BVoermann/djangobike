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
                'finanzen.xlsx',
                'konkurrenten.xlsx'
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
                elif filename == 'konkurrenten.xlsx':
                    parameters['competitors'] = read_competitors_excel(file_content)

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
    transportkosten_df = pd.read_excel(BytesIO(file_content), sheet_name='Transportkosten')

    return {
        'start_capital': startkapital_df.to_dict('records'),
        'credits': kredite_df.to_dict('records'),
        'other_costs': sonstiges_df.to_dict('records'),
        'transport_costs': transportkosten_df.to_dict('records')
    }


def read_competitors_excel(file_content):
    """Liest Konkurrenten-Daten aus Excel"""
    competitors_df = pd.read_excel(BytesIO(file_content), sheet_name='Konkurrenten')
    strategies_df = pd.read_excel(BytesIO(file_content), sheet_name='Strategien')
    market_dynamics_df = pd.read_excel(BytesIO(file_content), sheet_name='Marktdynamik')
    bike_preferences_df = pd.read_excel(BytesIO(file_content), sheet_name='Fahrradtyp_Vorlieben')

    return {
        'competitors': competitors_df.to_dict('records'),
        'strategies': strategies_df.to_dict('records'),
        'market_dynamics': market_dynamics_df.to_dict('records'),
        'bike_preferences': bike_preferences_df.to_dict('records')
    }


def initialize_session_data(session, parameters):
    """Initialisiert eine neue Spielsession mit den geladenen Parametern"""
    from .models import Supplier, ComponentType, Component, SupplierPrice, BikeType, BikePrice, Worker, TransportCost
    from sales.models import Market, MarketDemand, MarketPriceSensitivity
    from competitors.models import AICompetitor, StrategyConfiguration, MarketDynamicsSettings, BikeTypePreference

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

    # Storage space für Komponententypen (m² per unit) - UPDATED for realistic storage
    storage_spaces = {
        'Laufradsatz': 0.25,  # Wheel sets need more space (2 wheels + tires)
        'Rahmen': 0.40,       # Frames are bulky
        'Lenker': 0.15,       # Handlebars with packaging
        'Sattel': 0.05,       # Saddles with packaging  
        'Schaltung': 0.08,    # Gearshift components
        'Motor': 0.30         # Electric motors are heavy/bulky
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

    # Fahrradtypen erstellen - UPDATED for realistic bike storage
    bike_storage_spaces = {
        'Damenrad': 1.2,         # Basic bikes need proper spacing
        'E-Bike': 1.5,           # E-bikes are heavier, need more space
        'E-Mountainbike': 1.5,   # E-mountain bikes are bulky
        'Herrenrad': 1.2,        # Basic bikes need proper spacing
        'Mountainbike': 1.3,     # Mountain bikes are larger
        'Rennrad': 1.1,          # Racing bikes are slightly smaller
        'E-Mountain-Bike': 1.8   # Premium E-mountain bikes are largest
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

    # Transportkosten erstellen
    for transport_data in parameters['finance']['transport_costs']:
        TransportCost.objects.create(
            session=session,
            transport_type=transport_data['Transportart'],
            cost_per_km=transport_data['Kosten_pro_km'],
            base_transport_cost=transport_data['Basis_Transportkosten'],
            minimum_cost=transport_data['Mindestkosten']
        )

    # Märkte erstellen
    for location_data in parameters['markets']['locations']:
        # Create market with transport costs based on distance
        distance = location_data['Entfernung']
        cost_per_km = location_data['Transportkosten_pro_km']
        transport_cost = distance * cost_per_km
        
        market = Market.objects.create(
            session=session,
            name=location_data['Markt'],
            location=location_data['Markt'],
            transport_cost_home=transport_cost,
            transport_cost_foreign=transport_cost * 1.5  # 50% higher for foreign markets
        )

    # Marktnachfrage erstellen
    markets = {m.name: m for m in Market.objects.filter(session=session)}
    for demand_data in parameters['markets']['demand']:
        market = markets[demand_data['Markt']]
        bike_type = BikeType.objects.filter(session=session, name=demand_data['Fahrradtyp']).first()
        
        if bike_type:
            MarketDemand.objects.create(
                session=session,
                market=market,
                bike_type=bike_type,
                demand_percentage=demand_data['Nachfrage_pro_Monat']
            )

    # Preissensibilität erstellen
    for sensitivity_data in parameters['markets']['price_sensitivity']:
        market = markets[sensitivity_data['Markt']]
        bike_type = BikeType.objects.filter(session=session, name=sensitivity_data['Fahrradtyp']).first()
        
        if bike_type:
            # Create sensitivity for each price segment
            for segment in ['cheap', 'standard', 'premium']:
                MarketPriceSensitivity.objects.create(
                    session=session,
                    market=market,
                    price_segment=segment,
                    percentage=sensitivity_data['Preissensibilität']
                )

    # AI-Konkurrenten erstellen (nur aktive)
    # Import competitor parameter utilities
    from multiplayer.parameter_utils import (
        apply_competitor_financial_resources_multiplier,
        apply_competitor_market_presence_multiplier,
        apply_competitor_aggressiveness,
        apply_competitor_efficiency_multiplier
    )

    for competitor_data in parameters['competitors']['competitors']:
        if competitor_data.get('Aktiv', True):  # Nur aktive Konkurrenten erstellen
            # Apply parameter multipliers (will be 1.0 for singleplayer, but applied for multiplayer)
            financial_resources = apply_competitor_financial_resources_multiplier(
                competitor_data['Startkapital'], session
            )
            market_presence = apply_competitor_market_presence_multiplier(
                competitor_data['Marktanteil_Start'], session
            )
            aggressiveness = apply_competitor_aggressiveness(
                competitor_data['Aggressivität'], session
            )
            efficiency = apply_competitor_efficiency_multiplier(
                competitor_data['Effizienz'], session
            )

            AICompetitor.objects.create(
                session=session,
                name=competitor_data['Name'],
                strategy=competitor_data['Strategie'],
                financial_resources=financial_resources,
                market_presence=market_presence,
                aggressiveness=aggressiveness,
                efficiency=efficiency
            )

    # Strategiekonfigurationen erstellen
    from multiplayer.parameter_utils import apply_competitor_marketing_budget_multiplier

    for strategy_data in parameters['competitors']['strategies']:
        # Apply marketing budget multiplier (will be 1.0 for singleplayer, but applied for multiplayer)
        marketing_budget = apply_competitor_marketing_budget_multiplier(
            strategy_data['Marketingbudget'], session
        )

        StrategyConfiguration.objects.create(
            session=session,
            strategy=strategy_data['Strategie'],
            designation=strategy_data['Bezeichnung'],
            cheap_ratio=strategy_data['Günstig_Anteil'],
            standard_ratio=strategy_data['Standard_Anteil'],
            premium_ratio=strategy_data['Premium_Anteil'],
            price_factor=strategy_data['Preisfaktor'],
            production_volume=strategy_data['Produktionsvolumen'],
            quality_focus=strategy_data['Qualitätsfokus'],
            marketing_budget=marketing_budget
        )

    # Marktdynamik-Einstellungen erstellen
    for dynamics_data in parameters['competitors']['market_dynamics']:
        MarketDynamicsSettings.objects.create(
            session=session,
            parameter=dynamics_data['Parameter'],
            value=dynamics_data['Wert'],
            description=dynamics_data['Beschreibung']
        )

    # Fahrradtyp-Vorlieben erstellen
    for preference_data in parameters['competitors']['bike_preferences']:
        BikeTypePreference.objects.create(
            session=session,
            strategy=preference_data['Strategie'],
            bike_type_name=preference_data['Fahrradtyp'],
            preference=preference_data['Vorliebe'],
            production_probability=preference_data['Produktionswahrscheinlichkeit']
        )

    # Konkurrenten initialisieren
    from competitors.ai_engine import initialize_competitors_for_session
    initialize_competitors_for_session(session)
