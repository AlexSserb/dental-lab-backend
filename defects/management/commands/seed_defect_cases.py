from django.core.management.base import BaseCommand

from defects.models import DefectCase
from defects.triage.case_service import add_case
from operations.models import OperationType

# Demo precedents so the propose step has something to show before real closed cases accumulate.
DEMO_CASES = [
    {
        "defect_type": "fit",
        "severity": "medium",
        "description": "Циркониевая коронка не садится на культевый зуб, слишком тугая по контактным пунктам.",
        "cause": "Слишком малый цементный зазор и плотные контакты в проекте коронки.",
        "resolution": "Увеличить цементный зазор до 40 мкм, ослабить контакты и фрезеровать коронку заново.",
        "operation_type": "CAD/CAM",
    },
    {
        "defect_type": "crack_chipping",
        "severity": "low",
        "description": "Скол керамического слоя на жевательной поверхности металлокерамического моста после обжига.",
        "cause": "Слишком быстрое охлаждение после обжига и тонкий каркас в зоне скола.",
        "resolution": "Медленно охлаждать печь по программе обжига; реставрировать скол керамической массой.",
        "operation_type": "Керамика",
    },
    {
        "defect_type": "porosity",
        "severity": "medium",
        "description": "Пузыри и поры в базисе съёмного пластиночного протеза.",
        "cause": "Недостаточное давление при паковке пластмассы и влажный гипсовый штампик.",
        "resolution": "Паковка под контролируемым давлением, сушить модель до заливки базиса.",
        "operation_type": "Протезы",
    },
    {
        "defect_type": "color",
        "severity": "low",
        "description": "Коронка светлее заказанного оттенка A3 после глазурования.",
        "cause": "Ошибочно выбрана краска для глазурного слоя при повторном нанесении.",
        "resolution": "Перекрасить поверхностной краской и глазуровать заново при температуре первого обжига.",
        "operation_type": "Керамика",
    },
]


class Command(BaseCommand):
    help = (
        "Load demo defect cases (DefectCase, source=seed) as precedents for the triage workflow. Each case is "
        "embedded, so the command needs a working embedding endpoint. Cases already in the table are not duplicated."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Show how many cases would be added without saving anything.",
        )

    def handle(self, *args, **options):
        existing = set(DefectCase.objects.filter(source=DefectCase.Source.SEED).values_list("description", flat=True))
        fresh = [case for case in DEMO_CASES if case["description"] not in existing]
        if not fresh:
            self.stdout.write("All demo cases are already in the database.")
            return
        if options["dry_run"]:
            self.stdout.write(f"Would add {len(fresh)} case(s):")
            for case in fresh:
                self.stdout.write(f"  - [{case['defect_type']}/{case['severity']}] {case['description']}")
            return

        for case in fresh:
            case = dict(case)
            case["operation_type"] = OperationType.objects.filter(name=case["operation_type"]).first()
            add_case(source=DefectCase.Source.SEED, **case)
        self.stdout.write(self.style.SUCCESS(f"Added {len(fresh)} demo case(s)."))
