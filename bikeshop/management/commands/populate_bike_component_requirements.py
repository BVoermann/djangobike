from django.core.management.base import BaseCommand
from bikeshop.models import GameSession, BikeType, Component, ComponentType


class Command(BaseCommand):
    help = 'Populate BikeType component requirements based on existing bike-component relationships and logical mappings'

    def add_arguments(self, parser):
        parser.add_argument('--session-id', type=str, help='Specific session ID to update (optional)')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')

    def handle(self, *args, **options):
        sessions = GameSession.objects.all()
        if options['session_id']:
            sessions = sessions.filter(id=options['session_id'])

        if not sessions.exists():
            self.stdout.write(self.style.ERROR('No sessions found'))
            return

        total_updated = 0
        
        for session in sessions:
            self.stdout.write(f'\nProcessing session: {session.name} (ID: {session.id})')
            
            bike_types = BikeType.objects.filter(session=session)
            
            for bike_type in bike_types:
                self.stdout.write(f'  Processing bike type: {bike_type.name}')
                
                # Check if component requirements are already populated
                if (bike_type.required_frame_names or 
                    bike_type.required_wheel_set_names or 
                    bike_type.required_handlebar_names or
                    bike_type.required_saddle_names or
                    bike_type.required_gearshift_names or
                    bike_type.required_motor_names):
                    self.stdout.write(f'    Component requirements already populated, skipping...')
                    continue
                
                # Get component requirements based on logical mapping
                requirements = self.get_component_requirements_for_bike_type(session, bike_type)
                
                if options['dry_run']:
                    self.stdout.write(f'    [DRY RUN] Would update requirements:')
                    for comp_type, names in requirements.items():
                        self.stdout.write(f'      {comp_type}: {names}')
                else:
                    # Update the bike type with component requirements
                    bike_type.required_frame_names = requirements.get('Rahmen', [])
                    bike_type.required_wheel_set_names = requirements.get('Laufradsatz', [])
                    bike_type.required_handlebar_names = requirements.get('Lenker', [])
                    bike_type.required_saddle_names = requirements.get('Sattel', [])
                    bike_type.required_gearshift_names = requirements.get('Schaltung', [])
                    # Handle both motor field names
                    bike_type.required_motor_names = requirements.get('Motor und Akku', requirements.get('Motor', []))
                    
                    bike_type.save()
                    total_updated += 1
                    
                    self.stdout.write(f'    ✓ Updated requirements:')
                    for comp_type, names in requirements.items():
                        self.stdout.write(f'      {comp_type}: {names}')

        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS(f'\n[DRY RUN] Would have updated {total_updated} bike types'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nSuccessfully updated {total_updated} bike types'))

    def get_component_requirements_for_bike_type(self, session, bike_type):
        """
        Define logical component requirements for each bike type based on the bike name
        and available components in the session.
        """
        # Get all available components for this session organized by type
        available_components = {}
        component_types = ComponentType.objects.filter(session=session)
        
        for comp_type in component_types:
            components = Component.objects.filter(session=session, component_type=comp_type)
            available_components[comp_type.name] = [c.name for c in components]
        
        # Define logical mappings based on bike type names
        bike_name = bike_type.name.lower()
        requirements = {}
        
        # Frame requirements
        if 'Rahmen' in available_components:
            if 'damen' in bike_name:
                requirements['Rahmen'] = [c for c in available_components['Rahmen'] if 'damen' in c.lower()]
            elif 'herren' in bike_name:
                requirements['Rahmen'] = [c for c in available_components['Rahmen'] if 'herren' in c.lower()]
            elif 'mountain' in bike_name:
                requirements['Rahmen'] = [c for c in available_components['Rahmen'] if 'mountain' in c.lower()]
            elif 'renn' in bike_name:
                requirements['Rahmen'] = [c for c in available_components['Rahmen'] if 'renn' in c.lower()]
            elif 'e-' in bike_name:
                # E-bikes can use various frames, prioritize carbon for e-mountain
                if 'mountain' in bike_name:
                    requirements['Rahmen'] = [c for c in available_components['Rahmen'] if 'carbon' in c.lower() or 'mountain' in c.lower()]
                else:
                    requirements['Rahmen'] = [c for c in available_components['Rahmen'] if 'basic' in c.lower() or 'standard' in c.lower()]
            else:
                # Default to basic frames
                requirements['Rahmen'] = [c for c in available_components['Rahmen'] if 'basic' in c.lower()]
        
        # Wheel set requirements
        if 'Laufradsatz' in available_components:
            if 'e-mountain' in bike_name:
                requirements['Laufradsatz'] = [c for c in available_components['Laufradsatz'] if 'e-mountain' in c.lower() or 'pro' in c.lower()]
            elif 'mountain' in bike_name:
                requirements['Laufradsatz'] = [c for c in available_components['Laufradsatz'] if 'alpin' in c.lower() or 'mountain' in c.lower()]
            elif 'renn' in bike_name:
                requirements['Laufradsatz'] = [c for c in available_components['Laufradsatz'] if 'speed' in c.lower() or 'ampere' in c.lower()]
            elif 'e-' in bike_name:
                requirements['Laufradsatz'] = [c for c in available_components['Laufradsatz'] if 'ampere' in c.lower() or 'standard' in c.lower()]
            else:
                requirements['Laufradsatz'] = [c for c in available_components['Laufradsatz'] if 'standard' in c.lower()]
        
        # Motor requirements
        motor_component_type = 'Motor und Akku' if 'Motor und Akku' in available_components else 'Motor'
        if motor_component_type in available_components:
            if 'e-' in bike_name:
                if 'mountain' in bike_name:
                    requirements[motor_component_type] = [c for c in available_components[motor_component_type] if 'mountain' in c.lower() or 'high-performance' in c.lower()]
                else:
                    requirements[motor_component_type] = [c for c in available_components[motor_component_type] if 'standard' in c.lower()]
            else:
                # Non-electric bikes don't need motors
                requirements[motor_component_type] = []
        
        # Handlebar requirements
        if 'Lenker' in available_components:
            if 'mountain' in bike_name:
                requirements['Lenker'] = [c for c in available_components['Lenker'] if 'sport' in c.lower() or 'mountain' in c.lower()]
            elif 'renn' in bike_name:
                requirements['Lenker'] = [c for c in available_components['Lenker'] if 'sport' in c.lower()]
            elif 'e-mountain' in bike_name:
                requirements['Lenker'] = [c for c in available_components['Lenker'] if 'e-mountain' in c.lower() or 'pro' in c.lower()]
            else:
                # Default to comfort for regular bikes
                requirements['Lenker'] = [c for c in available_components['Lenker'] if 'comfort' in c.lower()]
        
        # Saddle requirements
        if 'Sattel' in available_components:
            if 'mountain' in bike_name:
                requirements['Sattel'] = [c for c in available_components['Sattel'] if 'sport' in c.lower() or 'mountain' in c.lower()]
            elif 'renn' in bike_name:
                requirements['Sattel'] = [c for c in available_components['Sattel'] if 'sport' in c.lower()]
            elif 'e-mountain' in bike_name:
                requirements['Sattel'] = [c for c in available_components['Sattel'] if 'e-mountain' in c.lower() or 'pro' in c.lower()]
            else:
                # Default to comfort for regular bikes
                requirements['Sattel'] = [c for c in available_components['Sattel'] if 'comfort' in c.lower()]
        
        # Gearshift requirements
        if 'Schaltung' in available_components:
            if 'e-mountain' in bike_name:
                requirements['Schaltung'] = [c for c in available_components['Schaltung'] if 'electronic' in c.lower() or 'e-mountain' in c.lower()]
            elif 'mountain' in bike_name:
                requirements['Schaltung'] = [c for c in available_components['Schaltung'] if 'gepard' in c.lower()]
            elif 'renn' in bike_name:
                requirements['Schaltung'] = [c for c in available_components['Schaltung'] if 'gepard' in c.lower()]
            else:
                # Default to basic gearshift
                requirements['Schaltung'] = [c for c in available_components['Schaltung'] if 'albatross' in c.lower()]
        
        # Fallback: if no specific matches, include all available components of that type
        for comp_type, component_names in available_components.items():
            mapped_type = comp_type
            if comp_type == 'Motor':  # Handle the mapping difference
                mapped_type = 'Motor und Akku'
            
            if mapped_type not in requirements or not requirements[mapped_type]:
                # If we couldn't find specific matches, allow all components
                if mapped_type == 'Motor und Akku' and 'e-' not in bike_name:
                    # Non-electric bikes still shouldn't have motors
                    requirements[mapped_type] = []
                else:
                    requirements[mapped_type] = component_names
        
        return requirements