from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from apps.employees.models import Employee, Department

@receiver([post_save, post_delete], sender=Employee)
@receiver([post_save, post_delete], sender=Department)
def invalidate_employee_stats(*args, **kwargs):
    # English: Conservative invalidation — wipe broad stats keys
    # If you use versioning, bump a stats_version instead.
    for suffix in ('global',):
        cache.delete_pattern('app:stats:employees:employee_list:*')
