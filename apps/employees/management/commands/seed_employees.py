"""
Management command to seed employee data for a Swiss private clinic.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import random

from apps.accounts.models import User
from apps.employees.models import Department, Position, Employee, EmploymentType


class Command(BaseCommand):
    help = 'Seed database with sample employee data for a Swiss private clinic'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing employee data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            Employee.objects.all().delete()
            Department.objects.all().delete()
            Position.objects.all().delete()
            # Delete users except superusers
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('✓ Data cleared'))

        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))

        with transaction.atomic():
            # Create departments
            departments = self.create_departments()
            self.stdout.write(self.style.SUCCESS(f'✓ Created {len(departments)} departments'))

            # Create positions
            positions = self.create_positions()
            self.stdout.write(self.style.SUCCESS(f'✓ Created {len(positions)} positions'))

            # Create employees
            employees = self.create_employees(departments, positions)
            self.stdout.write(self.style.SUCCESS(f'✓ Created {len(employees)} employees'))

        self.stdout.write(self.style.SUCCESS('\n✅ Seeding completed successfully!'))
        self.stdout.write(self.style.SUCCESS('\nLogin credentials for all employees:'))
        self.stdout.write(self.style.SUCCESS('Password: Password123!'))
        self.stdout.write(self.style.SUCCESS('\nSample logins:'))
        self.stdout.write(self.style.SUCCESS('  marie.dubois@clinique-alpes.ch'))
        self.stdout.write(self.style.SUCCESS('  pierre.martin@clinique-alpes.ch'))
        self.stdout.write(self.style.SUCCESS('  sophie.bernard@clinique-alpes.ch'))

    def create_departments(self):
        """Create typical departments for a Swiss private clinic."""
        departments_data = [
            {
                'name': 'Urgences',
                'code': 'URG',
                'description': 'Service des urgences - Emergency Department'
            },
            {
                'name': 'Chirurgie',
                'code': 'CHIR',
                'description': 'Service de chirurgie générale - General Surgery'
            },
            {
                'name': 'Médecine Interne',
                'code': 'MED',
                'description': 'Service de médecine interne - Internal Medicine'
            },
            {
                'name': 'Cardiologie',
                'code': 'CARD',
                'description': 'Service de cardiologie - Cardiology'
            },
            {
                'name': 'Pédiatrie',
                'code': 'PED',
                'description': 'Service de pédiatrie - Pediatrics'
            },
            {
                'name': 'Radiologie',
                'code': 'RAD',
                'description': 'Service de radiologie et imagerie médicale'
            },
            {
                'name': 'Laboratoire',
                'code': 'LAB',
                'description': 'Laboratoire d\'analyses médicales'
            },
            {
                'name': 'Administration',
                'code': 'ADM',
                'description': 'Service administratif et gestion'
            },
        ]

        departments = []
        for data in departments_data:
            dept = Department.objects.create(**data)
            departments.append(dept)

        return departments

    def create_positions(self):
        """Create typical positions for a Swiss private clinic."""
        positions_data = [
            {
                'title': 'Médecin Chef',
                'code': 'MC',
                'description': 'Chef de service médical',
                'requires_certification': True,
                'min_hourly_rate': Decimal('150.00'),
                'max_hourly_rate': Decimal('250.00')
            },
            {
                'title': 'Médecin Spécialiste',
                'code': 'MS',
                'description': 'Médecin spécialiste FMH',
                'requires_certification': True,
                'min_hourly_rate': Decimal('120.00'),
                'max_hourly_rate': Decimal('180.00')
            },
            {
                'title': 'Médecin Assistant',
                'code': 'MA',
                'description': 'Médecin assistant en formation',
                'requires_certification': True,
                'min_hourly_rate': Decimal('80.00'),
                'max_hourly_rate': Decimal('110.00')
            },
            {
                'title': 'Infirmier Diplômé',
                'code': 'IDE',
                'description': 'Infirmier diplômé d\'État',
                'requires_certification': True,
                'min_hourly_rate': Decimal('45.00'),
                'max_hourly_rate': Decimal('65.00')
            },
            {
                'title': 'Infirmier Spécialisé',
                'code': 'IS',
                'description': 'Infirmier avec spécialisation',
                'requires_certification': True,
                'min_hourly_rate': Decimal('50.00'),
                'max_hourly_rate': Decimal('70.00')
            },
            {
                'title': 'Aide-Soignant',
                'code': 'AS',
                'description': 'Aide-soignant certifié',
                'requires_certification': True,
                'min_hourly_rate': Decimal('35.00'),
                'max_hourly_rate': Decimal('45.00')
            },
            {
                'title': 'Secrétaire Médicale',
                'code': 'SM',
                'description': 'Secrétaire médicale',
                'requires_certification': False,
                'min_hourly_rate': Decimal('30.00'),
                'max_hourly_rate': Decimal('40.00')
            },
            {
                'title': 'Technicien de Laboratoire',
                'code': 'TL',
                'description': 'Technicien de laboratoire médical',
                'requires_certification': True,
                'min_hourly_rate': Decimal('40.00'),
                'max_hourly_rate': Decimal('55.00')
            },
            {
                'title': 'Radiologue',
                'code': 'RAD',
                'description': 'Médecin radiologue',
                'requires_certification': True,
                'min_hourly_rate': Decimal('140.00'),
                'max_hourly_rate': Decimal('200.00')
            },
            {
                'title': 'Technicien Radiologue',
                'code': 'TR',
                'description': 'Technicien en radiologie médicale',
                'requires_certification': True,
                'min_hourly_rate': Decimal('42.00'),
                'max_hourly_rate': Decimal('58.00')
            },
            {
                'title': 'Directeur Administratif',
                'code': 'DA',
                'description': 'Directeur des services administratifs',
                'requires_certification': False,
                'min_hourly_rate': Decimal('70.00'),
                'max_hourly_rate': Decimal('100.00')
            },
            {
                'title': 'Gestionnaire RH',
                'code': 'RH',
                'description': 'Responsable des ressources humaines',
                'requires_certification': False,
                'min_hourly_rate': Decimal('50.00'),
                'max_hourly_rate': Decimal('70.00')
            },
        ]

        positions = []
        for data in positions_data:
            pos = Position.objects.create(**data)
            positions.append(pos)

        return positions

    def create_employees(self, departments, positions):
        """Create sample employees with French names."""
        
        # French first names
        first_names_f = [
            'Marie', 'Sophie', 'Isabelle', 'Julie', 'Claire', 'Camille',
            'Amélie', 'Charlotte', 'Émilie', 'Léa', 'Sarah', 'Laura',
            'Pauline', 'Caroline', 'Lucie', 'Céline', 'Audrey', 'Nathalie'
        ]
        
        first_names_m = [
            'Pierre', 'Jean', 'Philippe', 'Laurent', 'Thomas', 'Nicolas',
            'Alexandre', 'François', 'Julien', 'David', 'Sébastien', 'Marc',
            'Olivier', 'Antoine', 'Maxime', 'Luc', 'Vincent', 'Matthieu'
        ]
        
        # French last names
        last_names = [
            'Dubois', 'Martin', 'Bernard', 'Thomas', 'Robert', 'Petit',
            'Durand', 'Leroy', 'Moreau', 'Simon', 'Laurent', 'Lefebvre',
            'Michel', 'Garcia', 'David', 'Bertrand', 'Roux', 'Vincent',
            'Fournier', 'Morel', 'Girard', 'André', 'Mercier', 'Dupont',
            'Lambert', 'Bonnet', 'François', 'Martinez', 'Legrand', 'Garnier'
        ]

        # Position to department mapping
        position_dept_map = {
            'MC': ['Urgences', 'Chirurgie', 'Médecine Interne', 'Cardiologie'],
            'MS': ['Urgences', 'Chirurgie', 'Médecine Interne', 'Cardiologie', 'Pédiatrie'],
            'MA': ['Urgences', 'Chirurgie', 'Médecine Interne', 'Pédiatrie'],
            'IDE': ['Urgences', 'Chirurgie', 'Médecine Interne', 'Cardiologie', 'Pédiatrie'],
            'IS': ['Urgences', 'Chirurgie', 'Cardiologie'],
            'AS': ['Urgences', 'Médecine Interne', 'Pédiatrie'],
            'SM': ['Urgences', 'Chirurgie', 'Administration'],
            'TL': ['Laboratoire'],
            'RAD': ['Radiologie'],
            'TR': ['Radiologie'],
            'DA': ['Administration'],
            'RH': ['Administration'],
        }

        employees = []
        employee_id_counter = 1001
        
        used_names = set()
        
        # Create employees for each position
        for position in positions:
            dept_names = position_dept_map.get(position.code, ['Administration'])
            num_employees = random.randint(2, 5) if position.code not in ['MC', 'DA', 'RH', 'RAD'] else random.randint(1, 2)
            
            for _ in range(num_employees):
                # Generate unique name
                attempts = 0
                while attempts < 100:
                    gender = random.choice(['M', 'F'])
                    first_name = random.choice(first_names_m if gender == 'M' else first_names_f)
                    last_name = random.choice(last_names)
                    full_name = f"{first_name} {last_name}"
                    
                    if full_name not in used_names:
                        used_names.add(full_name)
                        break
                    attempts += 1
                
                if attempts >= 100:
                    continue
                
                # Create user
                email = f"{first_name.lower()}.{last_name.lower()}@clinique-alpes.ch"
                username = email
                
                # Check if user exists
                if User.objects.filter(email=email).exists():
                    continue
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='Password123!',
                    first_name=first_name,
                    last_name=last_name,
                    phone=f"+41 {random.randint(21, 91)} {random.randint(100, 999)} {random.randint(10, 99)} {random.randint(10, 99)}",
                    country='CH'
                )
                
                # Select department
                dept_name = random.choice(dept_names)
                department = next(d for d in departments if d.name == dept_name)
                
                # Generate hire date (between 6 months and 10 years ago)
                days_ago = random.randint(180, 3650)
                hire_date = date.today() - timedelta(days=days_ago)
                
                # Calculate hourly rate within position range
                rate_range = position.max_hourly_rate - position.min_hourly_rate
                hourly_rate = position.min_hourly_rate + (rate_range * Decimal(random.uniform(0.2, 0.8)))
                hourly_rate = hourly_rate.quantize(Decimal('0.01'))
                
                # Determine employment type
                employment_type = random.choices(
                    [EmploymentType.FULL_TIME, EmploymentType.PART_TIME, EmploymentType.CONTRACT],
                    weights=[0.7, 0.2, 0.1]
                )[0]
                
                # Weekly hours based on employment type
                if employment_type == EmploymentType.FULL_TIME:
                    weekly_hours = Decimal('42.00')
                elif employment_type == EmploymentType.PART_TIME:
                    weekly_hours = Decimal(random.choice(['20.00', '25.00', '30.00']))
                else:
                    weekly_hours = Decimal('42.00')
                
                # Create employee
                employee = Employee.objects.create(
                    user=user,
                    employee_id=f"EMP{employee_id_counter:04d}",
                    department=department,
                    position=position,
                    employment_type=employment_type,
                    hire_date=hire_date,
                    hourly_rate=hourly_rate,
                    weekly_hours=weekly_hours,
                    is_active=True,
                    emergency_contact_name=f"{random.choice(first_names_m + first_names_f)} {random.choice(last_names)}",
                    emergency_contact_phone=f"+41 {random.randint(21, 91)} {random.randint(100, 999)} {random.randint(10, 99)} {random.randint(10, 99)}",
                    emergency_contact_relationship=random.choice(['Époux/Épouse', 'Parent', 'Frère/Sœur', 'Ami(e)'])
                )
                
                employees.append(employee)
                employee_id_counter += 1
        
        # Assign some employees as department managers
        for department in departments:
            dept_employees = Employee.objects.filter(department=department, is_active=True)
            if dept_employees.exists():
                # Try to find a senior position (MC or MS)
                senior_employees = dept_employees.filter(position__code__in=['MC', 'MS'])
                if senior_employees.exists():
                    manager = random.choice(senior_employees)
                else:
                    manager = random.choice(dept_employees)
                
                department.manager = manager.user
                department.save()
        
        return employees