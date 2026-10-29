from datetime import date

from django.core.management.base import BaseCommand

from bslfsr.models import Beneficiary, FarmerRecord, PeaceActivity
from core.models import Location, School
from projects.models import ActivityData, Indicator, Project


class Command(BaseCommand):
    help = "Create a small, repeatable demonstration dataset for the KAPDA workflow."

    def handle(self, *args, **options):
        location, _ = Location.objects.get_or_create(
            district="Demo District",
            sub_county="Demo Sub-county",
            parish="Demo Parish",
            defaults={"village": "Demo Village"},
        )
        school, _ = School.objects.get_or_create(
            name="KAPDA Demonstration School",
            defaults={"school_type": "primary", "kapda_supported": True, "location": location},
        )
        project, _ = Project.objects.update_or_create(
            code="DEMO-KAPDA",
            defaults={
                "name": "KAPDA Demonstration Programme",
                "description": "Small test dataset covering the EPICK and BSLFSR workflows.",
                "donor": "Demonstration",
                "start_date": date(2026, 1, 1),
                "end_date": date(2026, 12, 31),
                "active": True,
            },
        )

        definitions = [
            ("DEMO-01", "Learners enrolled", "EPICK", 120, 85, "sex, age_group, school, parish, disability_status"),
            ("DEMO-02", "Learner attendance", "EPICK", 100, 78, "sex, age_group, school, class_level"),
            ("DEMO-03", "Girls receiving sanitary pads", "Menstrual Health and WASH Module", 80, 62, "age_group, school, parish, support_type"),
            ("DEMO-04", "SMC/PTA participation", "SMC and PTA", 60, 44, "sex, participant_category, school"),
            ("DEMO-05", "BSLFSR beneficiaries reached", "BSLFSR", 150, 97, "sex, age_group, participant_category, parish, disability_status"),
            ("DEMO-06", "Farmers using improved practices", "BSLFSR", 75, 51, "sex, age_group, parish, participant_category"),
            ("DEMO-07", "Peacebuilding participants", "BSLFSR", 90, 57, "sex, age_group, parish, participant_category"),
        ]
        indicators = []
        for code, name, activity_type, target, actual, attributes in definitions:
            indicator, _ = Indicator.objects.update_or_create(
                code=code,
                defaults={
                    "project": project,
                    "name": name,
                    "activity_type": activity_type,
                    "unit": "people",
                    "target": target,
                    "definition": f"Demonstration indicator for {activity_type}.",
                    "attribute_fields": attributes,
                    "status": Indicator.Status.IN_PROGRESS,
                    "active": True,
                },
            )
            indicators.append((indicator, actual))

        for index, (indicator, actual) in enumerate(indicators):
            ActivityData.objects.update_or_create(
                activity=indicator,
                project=project,
                collection_date=date(2026, 10, 1 + index),
                defaults={
                    "actual_value": actual,
                    "reporting_period": "quarter",
                    "phase": "year_1",
                    "sex": "F" if index % 2 == 0 else "M",
                    "age": "13-17" if index < 4 else "18-24",
                    "age_group": "13-17" if index < 4 else "18-24",
                    "school": school,
                    "parish": location.parish,
                    "sub_county": location.sub_county,
                    "participant_category": "girl" if index < 4 else "woman",
                    "support_type": "sanitary_pads" if index == 2 else "",
                    "data_source": "KAPDA demo records",
                    "status": "submitted",
                    "attributes": {"demo_record": True, "indicator_type": indicator.activity_type},
                },
            )

        beneficiary_specs = [
            ("Demo Learner 1", "F", "girl", "refugee", False),
            ("Demo Learner 2", "M", "boy", "host", False),
            ("Demo Woman 1", "F", "woman", "host", False),
            ("Demo Woman 2", "F", "woman", "refugee", True),
            ("Demo Man 1", "M", "man", "host", False),
            ("Demo Youth 1", "M", "boy", "refugee", False),
            ("Demo Youth 2", "F", "girl", "host", False),
        ]
        for name, sex, category, displacement, disability in beneficiary_specs:
            beneficiary, _ = Beneficiary.objects.get_or_create(
                full_name=name,
                project=project,
                defaults={
                    "sex": sex,
                    "participant_category": category,
                    "displacement_status": displacement,
                    "disability_status": disability,
                    "location": location,
                    "estimated_age": 15 if category in {"girl", "boy"} else 24,
                },
            )
            FarmerRecord.objects.get_or_create(
                beneficiary=beneficiary,
                season="2026 demo season",
                defaults={"crop": "Beans", "quantity_distributed": 2, "improved_practices": "Demonstration plot"},
            )

        PeaceActivity.objects.get_or_create(
            project=project,
            title="Demo community dialogue",
            defaults={
                "activity_type": "dialogue",
                "activity_date": date(2026, 10, 10),
                "location": location,
                "female_participants": 18,
                "male_participants": 14,
                "youth_participants": 12,
            },
        )
        self.stdout.write(self.style.SUCCESS("Demo data loaded: 7 indicators, 7 activity records, 7 beneficiaries, farmer records and 1 peace activity."))
