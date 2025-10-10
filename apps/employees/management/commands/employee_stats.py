"""
Management command to display employee statistics.
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, Avg, Sum
from apps.employees.models import Department, Position, Employee


class Command(BaseCommand):
    help = 'Display employee statistics'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n📊 Employee Statistics\n'))
        self.stdout.write('=' * 60)
        
        # Total counts
        total_employees = Employee.objects.filter(is_active=True).count()
        total_departments = Department.objects.filter(is_active=True).count()
        total_positions = Position.objects.filter(is_active=True).count()
        
        self.stdout.write(f"\n🏥 Total Active Employees: {total_employees}")
        self.stdout.write(f"📁 Total Departments: {total_departments}")
        self.stdout.write(f"💼 Total Positions: {total_positions}")
        
        # By department
        self.stdout.write(self.style.SUCCESS('\n\n👥 Employees by Department:'))
        self.stdout.write('-' * 60)
        
        dept_stats = Department.objects.filter(is_active=True).annotate(
            emp_count=Count('employees', filter=models.Q(employees__is_active=True))
        ).order_by('-emp_count')
        
        for dept in dept_stats:
            manager_name = dept.manager.get_full_name() if dept.manager else 'No manager'
            self.stdout.write(f"  {dept.code:6s} - {dept.name:25s} {dept.emp_count:3d} employees | Manager: {manager_name}")
        
        # By position
        self.stdout.write(self.style.SUCCESS('\n\n💼 Employees by Position:'))
        self.stdout.write('-' * 60)
        
        pos_stats = Position.objects.filter(is_active=True).annotate(
            emp_count=Count('employees', filter=models.Q(employees__is_active=True))
        ).order_by('-emp_count')
        
        for pos in pos_stats:
            self.stdout.write(f"  {pos.code:6s} - {pos.title:30s} {pos.emp_count:3d} employees")
        
        # Employment types
        self.stdout.write(self.style.SUCCESS('\n\n📋 Employment Types:'))
        self.stdout.write('-' * 60)
        
        from apps.employees.models import EmploymentType
        for emp_type in EmploymentType:
            count = Employee.objects.filter(is_active=True, employment_type=emp_type.value).count()
            percentage = (count / total_employees * 100) if total_employees > 0 else 0
            self.stdout.write(f"  {emp_type.label:15s} {count:3d} ({percentage:5.1f}%)")
        
        # Salary statistics
        self.stdout.write(self.style.SUCCESS('\n\n💰 Salary Statistics:'))
        self.stdout.write('-' * 60)
        
        from django.db.models import Avg, Min, Max
        salary_stats = Employee.objects.filter(is_active=True).aggregate(
            avg_rate=Avg('hourly_rate'),
            min_rate=Min('hourly_rate'),
            max_rate=Max('hourly_rate')
        )
        
        self.stdout.write(f"  Average Hourly Rate: CHF {salary_stats['avg_rate']:.2f}")
        self.stdout.write(f"  Minimum Hourly Rate: CHF {salary_stats['min_rate']:.2f}")
        self.stdout.write(f"  Maximum Hourly Rate: CHF {salary_stats['max_rate']:.2f}")
        
        self.stdout.write('\n' + '=' * 60 + '\n')


# Import Q for filtering
from django.db import models