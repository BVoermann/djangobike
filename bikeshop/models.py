from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class GameSession(models.Model):
    """Hauptsession für das Spiel"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    current_month = models.IntegerField(default=1)
    current_year = models.IntegerField(default=2024)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=80000.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - Monat {self.current_month}/{self.current_year}"


class Supplier(models.Model):
    """Lieferant"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    payment_terms = models.IntegerField(default=30)  # Zahlungsziel in Tagen
    delivery_time = models.IntegerField(default=30)  # Lieferzeit in Tagen
    complaint_probability = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )  # Reklamationswahrscheinlichkeit in %
    complaint_quantity = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )  # Reklamationsanzahl in %
    quality = models.CharField(max_length=20, choices=[
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium')
    ])

    def __str__(self):
        return self.name


class ComponentType(models.Model):
    """Komponententyp (Laufradsatz, Rahmen, etc.)"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    storage_space_per_unit = models.FloatField()  # Lagerplatz pro Einheit in m²

    def __str__(self):
        return self.name


class Component(models.Model):
    """Einzelne Komponente"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    component_type = models.ForeignKey(ComponentType, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.component_type.name} - {self.name}"
    
    def get_quality_for_session(self, session):
        """Get the quality of this component based on its supplier for a given session"""
        supplier_price = SupplierPrice.objects.filter(
            session=session,
            component=self
        ).select_related('supplier').first()
        
        if supplier_price:
            return supplier_price.supplier.quality
        return None
    
    def is_compatible_with_segment(self, session, price_segment):
        """Check if this component's quality is compatible with the bike price segment"""
        quality = self.get_quality_for_session(session)
        if not quality:
            # Backward compatibility: if no supplier relationship exists, 
            # component is compatible with all segments (legacy behavior)
            return True
        
        # Define quality-to-segment mapping
        quality_mapping = {
            'basic': ['cheap', 'standard'],  # Basic quality can be used for cheap and standard bikes
            'standard': ['cheap', 'standard'],  # Standard quality can be used for cheap and standard bikes
            'premium': ['cheap', 'standard', 'premium']  # Premium can be used for all segments
        }
        
        return price_segment in quality_mapping.get(quality, [])
    
    def is_exact_quality_match(self, session, price_segment):
        """Check if this component's quality exactly matches the bike price segment"""
        quality = self.get_quality_for_session(session)
        if not quality:
            # Backward compatibility: components without quality are considered exact matches
            return True
        
        exact_mapping = {
            'cheap': 'basic',
            'standard': 'standard',
            'premium': 'premium'
        }
        
        return quality == exact_mapping.get(price_segment)
    
    def is_quality_upgrade(self, session, price_segment):
        """Check if using this component would be a quality upgrade for the target segment"""
        if not self.is_compatible_with_segment(session, price_segment):
            return False
        
        component_quality = self.get_quality_for_session(session)
        if not component_quality:
            return False
        
        # Define quality hierarchy
        quality_levels = {
            'basic': 1,
            'standard': 2,
            'premium': 3
        }
        
        segment_expected_levels = {
            'cheap': 1,     # Expected: basic
            'standard': 2,  # Expected: standard
            'premium': 3    # Expected: premium
        }
        
        component_level = quality_levels.get(component_quality, 1)
        expected_level = segment_expected_levels.get(price_segment, 1)
        
        # Only consider it an upgrade if component quality is HIGHER than expected
        return component_level > expected_level
    
    def get_quality_upgrade_info(self, session, price_segment):
        """Get information about the quality upgrade"""
        component_quality = self.get_quality_for_session(session)
        if not component_quality:
            return None
        
        quality_names = {
            'basic': 'Basis',
            'standard': 'Standard', 
            'premium': 'Premium'
        }
        
        segment_names = {
            'cheap': 'Günstig',
            'standard': 'Standard',
            'premium': 'Premium'
        }
        
        if self.is_quality_upgrade(session, price_segment):
            return {
                'component_quality': quality_names.get(component_quality, component_quality),
                'target_segment': segment_names.get(price_segment, price_segment),
                'is_upgrade': True
            }
        
        return {
            'component_quality': quality_names.get(component_quality, component_quality),
            'target_segment': segment_names.get(price_segment, price_segment),
            'is_upgrade': False
        }


class SupplierPrice(models.Model):
    """Preise der Lieferanten für Komponenten"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ['session', 'supplier', 'component']


class BikeType(models.Model):
    """Fahrradtyp"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    skilled_worker_hours = models.FloatField()
    unskilled_worker_hours = models.FloatField()
    storage_space_per_unit = models.FloatField()

    # Benötigte Komponenten (Legacy - will be replaced by component requirements)
    wheel_set = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='bikes_wheel', null=True, blank=True)
    frame = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='bikes_frame', null=True, blank=True)
    handlebar = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='bikes_handlebar', null=True, blank=True)
    saddle = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='bikes_saddle', null=True, blank=True)
    gearshift = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='bikes_gearshift', null=True, blank=True)
    motor = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='bikes_motor', null=True, blank=True)
    
    # Component requirements by name (new flexible system)
    required_wheel_set_names = models.JSONField(default=list, blank=True, help_text="List of wheel set component names this bike can use")
    required_frame_names = models.JSONField(default=list, blank=True, help_text="List of frame component names this bike can use")
    required_handlebar_names = models.JSONField(default=list, blank=True, help_text="List of handlebar component names this bike can use")
    required_saddle_names = models.JSONField(default=list, blank=True, help_text="List of saddle component names this bike can use")
    required_gearshift_names = models.JSONField(default=list, blank=True, help_text="List of gearshift component names this bike can use")
    required_motor_names = models.JSONField(default=list, blank=True, help_text="List of motor component names this bike can use (empty if no motor needed)")

    def __str__(self):
        return self.name
    
    def get_compatible_components(self, component_type_name):
        """Get list of compatible component names for a given component type"""
        mapping = {
            'Laufradsatz': self.required_wheel_set_names,
            'Rahmen': self.required_frame_names,
            'Lenker': self.required_handlebar_names,
            'Sattel': self.required_saddle_names,
            'Schaltung': self.required_gearshift_names,
            'Motor und Akku': self.required_motor_names,
            'Motor': self.required_motor_names,  # Handle both motor naming conventions
        }
        return mapping.get(component_type_name, [])
    
    def can_use_component(self, component):
        """Check if this bike type can use the given component"""
        component_type_name = component.component_type.name
        compatible_names = self.get_compatible_components(component_type_name)
        return component.name in compatible_names
    
    def get_required_components(self):
        """Get all required component types and their compatible options"""
        requirements = {}
        
        # Try new flexible system first
        if self.required_wheel_set_names:
            requirements['Laufradsatz'] = self.required_wheel_set_names
        if self.required_frame_names:
            requirements['Rahmen'] = self.required_frame_names
        if self.required_handlebar_names:
            requirements['Lenker'] = self.required_handlebar_names
        if self.required_saddle_names:
            requirements['Sattel'] = self.required_saddle_names
        if self.required_gearshift_names:
            requirements['Schaltung'] = self.required_gearshift_names
        if self.required_motor_names:
            requirements['Motor und Akku'] = self.required_motor_names
            requirements['Motor'] = self.required_motor_names  # Handle both motor naming conventions
        
        # Fallback to legacy system if new fields are empty
        if not requirements:
            if self.wheel_set:
                requirements[self.wheel_set.component_type.name] = [self.wheel_set.name]
            if self.frame:
                requirements[self.frame.component_type.name] = [self.frame.name]
            if self.handlebar:
                requirements[self.handlebar.component_type.name] = [self.handlebar.name]
            if self.saddle:
                requirements[self.saddle.component_type.name] = [self.saddle.name]
            if self.gearshift:
                requirements[self.gearshift.component_type.name] = [self.gearshift.name]
            if self.motor:
                requirements[self.motor.component_type.name] = [self.motor.name]
        
        return requirements
    
    def find_best_components_for_segment(self, session, price_segment):
        """Find the best available components for this bike type and segment.
        
        Returns a dict with:
        - 'components': dict mapping component_type_name -> Component instance
        - 'upgrades': list of upgrade info for components that are higher quality than needed
        - 'missing': list of component types that have no available components
        """
        from warehouse.models import ComponentStock
        
        result = {
            'components': {},
            'upgrades': [],
            'missing': []
        }
        
        required_components = self.get_required_components()
        
        for component_type_name, compatible_names in required_components.items():
            # Find components that match the requirements
            component_type = ComponentType.objects.filter(
                session=session, 
                name=component_type_name
            ).first()
            
            if not component_type:
                result['missing'].append(component_type_name)
                continue
            
            # Get all compatible components for this bike type
            compatible_components = Component.objects.filter(
                session=session,
                component_type=component_type,
                name__in=compatible_names
            )
            
            # Filter by components that have stock
            components_with_stock = []
            for comp in compatible_components:
                stock = ComponentStock.objects.filter(
                    session=session,
                    component=comp,
                    quantity__gt=0
                ).first()
                if stock:
                    components_with_stock.append(comp)
            
            if not components_with_stock:
                result['missing'].append(component_type_name)
                continue
            
            # Try to find exact quality match first
            exact_matches = [
                comp for comp in components_with_stock 
                if comp.is_exact_quality_match(session, price_segment)
            ]
            
            if exact_matches:
                # Use the first exact match
                chosen_component = exact_matches[0]
                result['components'][component_type_name] = chosen_component
            else:
                # Try to find compatible components (quality upgrades)
                compatible_upgrades = [
                    comp for comp in components_with_stock 
                    if comp.is_compatible_with_segment(session, price_segment)
                ]
                
                if compatible_upgrades:
                    # Use the first compatible component (which will be an upgrade)
                    chosen_component = compatible_upgrades[0]
                    result['components'][component_type_name] = chosen_component
                    
                    # Add upgrade information
                    upgrade_info = chosen_component.get_quality_upgrade_info(session, price_segment)
                    if upgrade_info and upgrade_info['is_upgrade']:
                        upgrade_info['component_name'] = chosen_component.name
                        upgrade_info['component_type'] = component_type_name
                        result['upgrades'].append(upgrade_info)
                else:
                    # No compatible components available
                    result['missing'].append(component_type_name)
        
        return result


class BikePrice(models.Model):
    """Verkaufspreise für Fahrräder"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    bike_type = models.ForeignKey(BikeType, on_delete=models.CASCADE)
    price_segment = models.CharField(max_length=20, choices=[
        ('cheap', 'Günstig'),
        ('standard', 'Standard'),
        ('premium', 'Premium')
    ])
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ['session', 'bike_type', 'price_segment']


class Worker(models.Model):
    """Arbeiter"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    worker_type = models.CharField(max_length=20, choices=[
        ('skilled', 'Facharbeiter'),
        ('unskilled', 'Hilfsarbeiter')
    ])
    hourly_wage = models.DecimalField(max_digits=6, decimal_places=2)
    monthly_hours = models.IntegerField(default=150)
    count = models.IntegerField(default=0)

    # Time tracking for current month
    used_hours_this_month = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tracking_month = models.IntegerField(null=True, blank=True)
    tracking_year = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ['session', 'worker_type']

    def __str__(self):
        worker_type_display = dict(self._meta.get_field('worker_type').choices)[self.worker_type]
        return f"{worker_type_display} ({self.count} Arbeiter, {self.hourly_wage}€/h)"

    def get_total_monthly_capacity(self):
        """Returns total hours available per month for all workers of this type"""
        return self.count * self.monthly_hours

    def get_remaining_hours(self, current_month, current_year):
        """Returns remaining available hours for the current month"""
        from decimal import Decimal

        # Reset tracking if month has changed
        if self.tracking_month != current_month or self.tracking_year != current_year:
            self.used_hours_this_month = Decimal('0')
            self.tracking_month = current_month
            self.tracking_year = current_year
            self.save()

        total_capacity = self.get_total_monthly_capacity()
        return total_capacity - float(self.used_hours_this_month)

    def use_hours(self, hours, current_month, current_year):
        """Subtracts hours from available time for the current month"""
        from decimal import Decimal

        # Ensure we're tracking the current month
        if self.tracking_month != current_month or self.tracking_year != current_year:
            self.used_hours_this_month = Decimal('0')
            self.tracking_month = current_month
            self.tracking_year = current_year

        self.used_hours_this_month += Decimal(str(hours))
        self.save()


class TransportCost(models.Model):
    """Transportkosten"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    transport_type = models.CharField(max_length=50)  # Standard Lieferung, Express, etc.
    cost_per_km = models.DecimalField(max_digits=6, decimal_places=2)  # Kosten pro km
    base_transport_cost = models.DecimalField(max_digits=6, decimal_places=2)  # Basis-Transportkosten
    minimum_cost = models.DecimalField(max_digits=6, decimal_places=2)  # Mindestkosten

    class Meta:
        unique_together = ['session', 'transport_type']

    def __str__(self):
        return f"{self.transport_type} - {self.cost_per_km}€/km"
