from django.contrib import admin
from .models import Worker


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'worker_type',
        'hourly_wage',
        'efficiency',
        'experience_level',
        'monthly_cost',
        'is_active',
        'hired_date'
    ]

    list_filter = [
        'worker_type',
        'is_active',
        'hired_date',
        'experience_level'
    ]

    search_fields = ['name', 'worker_type']

    list_editable = ['hourly_wage', 'efficiency', 'experience_level', 'is_active']

    readonly_fields = ['hired_date', 'monthly_cost', 'productivity_score']

    fieldsets = (
        ('Grundinformationen', {
            'fields': ('name', 'worker_type', 'is_active')
        }),
        ('Arbeitsdetails', {
            'fields': ('hourly_wage', 'efficiency', 'experience_level')
        }),
        ('Berechnete Werte', {
            'fields': ('monthly_cost', 'productivity_score'),
            'classes': ('collapse',)
        }),
        ('Zeitstempel', {
            'fields': ('hired_date',),
            'classes': ('collapse',)
        }),
    )

    actions = ['fire_selected_workers', 'rehire_selected_workers']

    def fire_selected_workers(self, request, queryset):
        """Ausgewählte Arbeiter entlassen"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} Arbeiter wurden entlassen.')

    fire_selected_workers.short_description = "Ausgewählte Arbeiter entlassen"

    def rehire_selected_workers(self, request, queryset):
        """Ausgewählte Arbeiter wieder einstellen"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} Arbeiter wurden wieder eingestellt.')

    rehire_selected_workers.short_description = "Ausgewählte Arbeiter wieder einstellen"