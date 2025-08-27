from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from .models import Worker
from .forms import WorkerForm, QuickHireForm
import random
from decimal import Decimal


@login_required
def worker_dashboard(request):
    """Hauptansicht für das Arbeitermanagement"""
    workers = Worker.objects.filter(is_active=True).order_by('worker_type', 'name')

    # Statistiken berechnen
    stats = {
        'total_workers': workers.count(),
        'skilled_workers': workers.filter(worker_type='skilled').count(),
        'unskilled_workers': workers.filter(worker_type='unskilled').count(),
        'total_monthly_costs': Worker.get_total_monthly_costs(),
        'avg_efficiency_skilled': workers.filter(worker_type='skilled').aggregate(
            avg_eff=Avg('efficiency'))['avg_eff'] or 0,
        'avg_efficiency_unskilled': workers.filter(worker_type='unskilled').aggregate(
            avg_eff=Avg('efficiency'))['avg_eff'] or 0,
    }

    # Suche
    search_query = request.GET.get('search', '')
    if search_query:
        workers = workers.filter(
            Q(name__icontains=search_query) |
            Q(worker_type__icontains=search_query)
        )

    # Filterung nach Typ
    filter_type = request.GET.get('type', '')
    if filter_type in ['skilled', 'unskilled']:
        workers = workers.filter(worker_type=filter_type)

    # Paginierung
    paginator = Paginator(workers, 10)
    page_number = request.GET.get('page')
    workers_page = paginator.get_page(page_number)

    context = {
        'workers': workers_page,
        'stats': stats,
        'search_query': search_query,
        'filter_type': filter_type,
    }

    return render(request, 'workers/dashboard.html', context)


@login_required
def add_worker(request):
    """Einzelnen Arbeiter hinzufügen"""
    if request.method == 'POST':
        form = WorkerForm(request.POST)
        if form.is_valid():
            worker = form.save()
            messages.success(request, f'{worker.name} wurde erfolgreich eingestellt!')
            return redirect('workers:dashboard')
    else:
        form = WorkerForm()

    return render(request, 'workers/add_worker.html', {'form': form})


@login_required
def quick_hire(request):
    """Mehrere Arbeiter schnell einstellen"""
    if request.method == 'POST':
        form = QuickHireForm(request.POST)
        if form.is_valid():
            worker_type = form.cleaned_data['worker_type']
            count = form.cleaned_data['count']

            hired_workers = []

            for i in range(count):
                # Generiere zufällige, aber realistische Werte
                if worker_type == 'skilled':
                    base_names = ['Max', 'Anna', 'Peter', 'Lisa', 'Tom', 'Sarah', 'Klaus', 'Maria']
                    surnames = ['Müller', 'Schmidt', 'Weber', 'Fischer', 'Meyer', 'Wagner', 'Becker']
                    hourly_wage = Decimal(str(random.uniform(25, 35))).quantize(Decimal('0.01'))
                    efficiency = random.randint(90, 150)
                    experience = random.randint(3, 8)
                else:
                    base_names = ['Tim', 'Nina', 'Lars', 'Jana', 'Ben', 'Emma', 'Paul', 'Lea']
                    surnames = ['Richter', 'Klein', 'Wolf', 'Schröder', 'Neumann', 'Schwarz', 'Zimmermann']
                    hourly_wage = Decimal(str(random.uniform(15, 20))).quantize(Decimal('0.01'))
                    efficiency = random.randint(80, 120)
                    experience = random.randint(1, 5)

                name = f"{random.choice(base_names)} {random.choice(surnames)}"

                worker = Worker.objects.create(
                    name=name,
                    worker_type=worker_type,
                    hourly_wage=hourly_wage,
                    efficiency=efficiency,
                    experience_level=experience
                )
                hired_workers.append(worker)

            worker_type_display = 'Facharbeiter' if worker_type == 'skilled' else 'Hilfsarbeiter'
            messages.success(
                request,
                f'{count} {worker_type_display} wurden erfolgreich eingestellt!'
            )
            return redirect('workers:dashboard')
    else:
        form = QuickHireForm()

    return render(request, 'workers/quick_hire.html', {'form': form})


@login_required
def fire_worker(request, worker_id):
    """Arbeiter entlassen"""
    worker = get_object_or_404(Worker, id=worker_id, is_active=True)

    if request.method == 'POST':
        worker.is_active = False
        worker.save()
        messages.success(request, f'{worker.name} wurde entlassen.')
        return redirect('workers:dashboard')

    return render(request, 'workers/fire_worker.html', {'worker': worker})


@login_required
def worker_detail(request, worker_id):
    """Detailansicht eines Arbeiters"""
    worker = get_object_or_404(Worker, id=worker_id)

    if request.method == 'POST':
        form = WorkerForm(request.POST, instance=worker)
        if form.is_valid():
            form.save()
            messages.success(request, f'Daten von {worker.name} wurden aktualisiert.')
            return redirect('workers:dashboard')
    else:
        form = WorkerForm(instance=worker)

    context = {
        'worker': worker,
        'form': form,
    }

    return render(request, 'workers/worker_detail.html', context)


@login_required
def fired_workers(request):
    """Ansicht für entlassene Arbeiter"""
    fired_workers = Worker.objects.filter(is_active=False).order_by('-hired_date')

    paginator = Paginator(fired_workers, 10)
    page_number = request.GET.get('page')
    workers_page = paginator.get_page(page_number)

    return render(request, 'workers/fired_workers.html', {'workers': workers_page})