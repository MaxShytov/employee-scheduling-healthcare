"""
Management command to seed employee data for a Swiss private clinic.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import random
import re
import unicodedata

from apps.accounts.models import User
from apps.employees.models import Department, Position, Location, Employee, EmploymentType


def to_ascii_name(s: str) -> str:
    SPECIALS = {
        "ß": "ss", "Æ": "AE", "æ": "ae", "Œ": "OE", "œ": "oe",
        "Ø": "O",  "ø": "o",  "Ð": "D",  "ð": "d",
        "Þ": "TH", "þ": "th", "Ł": "L",  "ł": "l",
    }
    s = s.strip()
    # Сначала вручную заменим проблемные символы
    s = "".join(SPECIALS.get(ch, ch) for ch in s)
    # Уберём диакритику (é→e, ç→c и т.д.)
    s = unicodedata.normalize("NFKD", s).encode(
        "ascii", "ignore").decode("ascii")
    # Оставим только буквы
    s = re.sub(r"[^A-Za-z]", "", s)
    return s.lower()


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
            Location.objects.all().delete()  # ← ДОБАВЛЕНО
            Department.objects.all().delete()
            Position.objects.all().delete()
            # Delete users except superusers
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('✓ Data cleared'))

        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))

        with transaction.atomic():
            # Create locations first
            locations = self.create_locations()
            self.stdout.write(self.style.SUCCESS(
                f'✓ Created {len(locations)} locations'))
            
            # Create departments
            departments = self.create_departments()
            self.stdout.write(self.style.SUCCESS(
                f'✓ Created {len(departments)} departments'))

            # Create positions
            positions = self.create_positions()
            self.stdout.write(self.style.SUCCESS(
                f'✓ Created {len(positions)} positions'))

            # Create employees
            employees = self.create_employees(departments, positions, locations)
            self.stdout.write(self.style.SUCCESS(
                f'✓ Created {len(employees)} employees'))

        self.stdout.write(self.style.SUCCESS(
            '\n✅ Seeding completed successfully!'))
        self.stdout.write(self.style.SUCCESS(
            '\n📍 Created locations:'))
        for location in locations:
            self.stdout.write(self.style.SUCCESS(
                f'   • {location.name} - {location.city}'))
        self.stdout.write(self.style.SUCCESS(
            '\nLogin credentials for all employees:'))
        self.stdout.write(self.style.SUCCESS('Password: Password123!'))
        self.stdout.write(self.style.SUCCESS('\nSample logins:'))
        self.stdout.write(self.style.SUCCESS(
            '  marie.dubois@clinique-alpes.ch'))
        self.stdout.write(self.style.SUCCESS(
            '  pierre.martin@clinique-alpes.ch'))
        self.stdout.write(self.style.SUCCESS(
            '  sophie.bernard@clinique-alpes.ch'))

    def create_locations(self):
        """Create clinic locations in Switzerland, Canada, Luxembourg, and Monaco."""
        locations_data = [
            # Switzerland locations
            {
                'name': 'Clinique des Alpes - Genève',
                'code': 'GVA',
                'address': 'Rue du Rhône 45',
                'city': 'Genève',
                'postal_code': '1204',
                'state_province': 'GE',  # Geneva canton
                'country': 'CH',
                'phone': '+41 22 123 45 67',
                'email': 'info@clinique-alpes.ch',
                'labor_budget': Decimal('250000.00'),
                'latitude': Decimal('46.204391'),
                'longitude': Decimal('6.143158'),
                'description': 'Main clinic location in Geneva city center'
            },
            {
                'name': 'Clinique des Alpes - Lausanne',
                'code': 'LAU',
                'address': 'Avenue de la Gare 12',
                'city': 'Lausanne',
                'postal_code': '1003',
                'state_province': 'VD',  # Vaud canton
                'country': 'CH',
                'phone': '+41 21 987 65 43',
                'email': 'lausanne@clinique-alpes.ch',
                'labor_budget': Decimal('180000.00'),
                'latitude': Decimal('46.516968'),
                'longitude': Decimal('6.629117'),
                'description': 'Secondary location in Lausanne'
            },
            {
                'name': 'Clinique des Alpes - Bern',
                'code': 'BRN',
                'address': 'Spitalstrasse 1',
                'city': 'Bern',
                'postal_code': '3010',
                'state_province': 'BE',  # Bern canton
                'country': 'CH',
                'phone': '+41 31 456 78 90',
                'email': 'bern@clinique-alpes.ch',
                'labor_budget': Decimal('150000.00'),
                'latitude': Decimal('46.947456'),
                'longitude': Decimal('7.447396'),
                'description': 'Branch office in Bern'
            },
            # Canada locations - Toronto Dental Clinics
            {
                'name': 'Toronto Smile Dental Clinic',
                'code': 'TOR1',
                'address': '350 Bay Street, Suite 1200',
                'city': 'Toronto',
                'postal_code': 'M5H 2S6',
                'state_province': 'ON',  # Ontario province
                'country': 'CA',
                'phone': '+1 416 555 0101',
                'email': 'info@torontosmile.ca',
                'labor_budget': Decimal('120000.00'),
                'latitude': Decimal('43.651070'),
                'longitude': Decimal('-79.381786'),
                'description': 'Downtown Toronto dental clinic specializing in cosmetic dentistry'
            },
            {
                'name': 'North York Dental Care',
                'code': 'TOR2',
                'address': '5650 Yonge Street, Suite 102',
                'city': 'Toronto',
                'postal_code': 'M2M 4G3',
                'state_province': 'ON',  # Ontario province
                'country': 'CA',
                'phone': '+1 416 555 0202',
                'email': 'info@northyorkdental.ca',
                'labor_budget': Decimal('95000.00'),
                'latitude': Decimal('43.777111'),
                'longitude': Decimal('-79.417297'),
                'description': 'Family dental practice in North York area'
            },
            # Luxembourg - Family Doctor
            {
                'name': 'Cabinet Médical Dr. Schneider',
                'code': 'LUX',
                'address': '12 Rue de la Gare',
                'city': 'Luxembourg',
                'postal_code': 'L-1611',
                'state_province': '',  # Luxembourg has no states/provinces
                'country': 'LU',
                'phone': '+352 26 12 34 56',
                'email': 'contact@drschneider.lu',
                'labor_budget': Decimal('80000.00'),
                'latitude': Decimal('49.611622'),
                'longitude': Decimal('6.131935'),
                'description': 'Family medicine practice in Luxembourg City center'
            },
            # Monaco - ENT Specialist
            {
                'name': 'Cabinet ORL Dr. Moretti',
                'code': 'MCO',
                'address': '7 Avenue Prince Héréditaire Albert',
                'city': 'Monte-Carlo',
                'postal_code': '98000',
                'state_province': '',  # Monaco has no states/provinces
                'country': 'MC',
                'phone': '+377 93 50 12 34',
                'email': 'secretariat@orlmoretti.mc',
                'labor_budget': Decimal('150000.00'),
                'latitude': Decimal('43.738418'),
                'longitude': Decimal('7.424616'),
                'description': 'ENT (Ear, Nose, Throat) specialist clinic in Monte-Carlo'
            },
        ]

        from apps.core.models import Address

        locations = []
        for data in locations_data:
            # Extract address fields
            address_data = {
                'address': data.pop('address'),
                'address_line_2': data.pop('address_line_2', ''),
                'city': data.pop('city'),
                'postal_code': data.pop('postal_code'),
                'state_province': data.pop('state_province', ''),
                'country': data.pop('country'),
                'latitude': data.pop('latitude', None),
                'longitude': data.pop('longitude', None),
            }

            # Create Address record
            address = Address.objects.create(**address_data)

            # Create Location with reference to Address
            location = Location.objects.create(
                address_detail=address,
                **data  # remaining fields (name, code, phone, email, etc.)
            )
            locations.append(location)

        return locations

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

    def create_employees(self, departments, positions, locations):
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

        # Get main location (Geneva)
        main_location = locations[0]  # Genève

        # Create employees for each position
        for position in positions:
            dept_names = position_dept_map.get(
                position.code, ['Administration'])
            num_employees = random.randint(2, 5) if position.code not in [
                'MC', 'DA', 'RH', 'RAD'] else random.randint(1, 2)

            for _ in range(num_employees):
                # Generate unique name
                attempts = 0
                while attempts < 100:
                    gender = random.choice(['M', 'F'])
                    first_name = random.choice(
                        first_names_m if gender == 'M' else first_names_f)
                    last_name = random.choice(last_names)
                    full_name = f"{first_name} {last_name}"

                    if full_name not in used_names:
                        used_names.add(full_name)
                        break
                    attempts += 1

                if attempts >= 100:
                    continue

                # Create user
                local_part = f"{to_ascii_name(first_name)}.{to_ascii_name(last_name)}"
                email = f"{local_part}@clinique-alpes.ch"
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
                department = next(
                    d for d in departments if d.name == dept_name)

                # Randomly assign location with weighted distribution
                # Geneva: 40%, Lausanne: 25%, Bern: 20%, Toronto clinics: 10%, Luxembourg: 3%, Monaco: 2%
                location = random.choices(
                    locations,
                    weights=[0.40, 0.25, 0.20, 0.05, 0.05, 0.03, 0.02]
                )[0]

                # Generate hire date (between 6 months and 10 years ago)
                days_ago = random.randint(180, 3650)
                hire_date = date.today() - timedelta(days=days_ago)

                # Calculate hourly rate within position range
                rate_range = position.max_hourly_rate - position.min_hourly_rate
                hourly_rate = position.min_hourly_rate + \
                    (rate_range * Decimal(random.uniform(0.2, 0.8)))
                hourly_rate = hourly_rate.quantize(Decimal('0.01'))

                # Determine employment type
                employment_type = random.choices(
                    [EmploymentType.FULL_TIME, EmploymentType.PART_TIME,
                        EmploymentType.CONTRACT],
                    weights=[0.7, 0.2, 0.1]
                )[0]

                # Weekly hours based on employment type
                if employment_type == EmploymentType.FULL_TIME:
                    weekly_hours = Decimal('42.00')
                elif employment_type == EmploymentType.PART_TIME:
                    weekly_hours = Decimal(
                        random.choice(['20.00', '25.00', '30.00']))
                else:
                    weekly_hours = Decimal('42.00')

                # Create employee
                employee = Employee.objects.create(
                    user=user,
                    employee_id=f"EMP{employee_id_counter:04d}",
                    department=department,
                    position=position,
                    location=location,  # ← ДОБАВЛЕНО
                    employment_type=employment_type,
                    hire_date=hire_date,
                    hourly_rate=hourly_rate,
                    weekly_hours=weekly_hours,
                    is_active=True,
                    emergency_contact_name=f"{random.choice(first_names_m + first_names_f)} {random.choice(last_names)}",
                    emergency_contact_phone=f"+41 {random.randint(21, 91)} {random.randint(100, 999)} {random.randint(10, 99)} {random.randint(10, 99)}",
                    emergency_contact_relationship=random.choice(
                        ['Époux/Épouse', 'Parent', 'Frère/Sœur', 'Ami(e)'])
                )

                employees.append(employee)
                employee_id_counter += 1

        # Assign some employees as department managers
        for department in departments:
            dept_employees = Employee.objects.filter(
                department=department, is_active=True)
            if dept_employees.exists():
                # Try to find a senior position (MC or MS)
                senior_employees = dept_employees.filter(
                    position__code__in=['MC', 'MS'])
                if senior_employees.exists():
                    manager = random.choice(senior_employees)
                else:
                    manager = random.choice(dept_employees)

                department.manager = manager.user
                department.save()

        # Assign location managers
        for location in locations:
            loc_employees = Employee.objects.filter(
                location=location, is_active=True)
            if loc_employees.exists():
                # Try to find DA (Directeur Administratif) or senior position
                admin_employees = loc_employees.filter(
                    position__code__in=['DA', 'MC', 'MS'])
                if admin_employees.exists():
                    manager = random.choice(admin_employees)
                else:
                    manager = random.choice(loc_employees)

                location.manager = manager.user
                location.save()

        return employees