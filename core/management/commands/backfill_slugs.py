from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate missing slugs for all models that define a slug field."

    def handle(self, *args, **options):
        total = 0
        for model in apps.get_models():
            if not any(field.name == "slug" for field in model._meta.fields):
                continue
            missing = model.objects.filter(slug__isnull=True)
            count = missing.count()
            for record in missing.iterator():
                record.save()
            if count:
                self.stdout.write(f"{model._meta.label}: generated {count} slug(s)")
                total += count
        self.stdout.write(self.style.SUCCESS(f"Generated {total} missing slug(s)."))
