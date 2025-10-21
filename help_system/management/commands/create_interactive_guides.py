from django.core.management.base import BaseCommand
from help_system.models import HelpCategory, InteractiveGuide


class Command(BaseCommand):
    help = 'Create interactive guides for all simulation tabs'

    def handle(self, *args, **options):
        self.stdout.write('Deleting all interactive guides...')

        # Delete all interactive guides
        deleted_count = InteractiveGuide.objects.all().delete()[0]
        self.stdout.write(f'Deleted {deleted_count} interactive guide(s)')

        self.stdout.write(self.style.SUCCESS(f'Successfully deleted all interactive guides'))
