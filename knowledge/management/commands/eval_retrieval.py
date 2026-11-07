from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from knowledge.services.eval_service import DEFAULT_QUESTIONS, EvalService


class Command(BaseCommand):
    help = "Measure retrieval quality (hit rate @k and MRR) on a set of questions with expected source documents"

    def add_arguments(self, parser):
        parser.add_argument("--questions", default=str(DEFAULT_QUESTIONS), help="Path to a JSON file with cases")
        parser.add_argument("--verbose", action="store_true", help="Show every question, not only failures")

    def handle(self, *args, **options):
        path = Path(options["questions"])
        if not path.is_file():
            raise CommandError(f"Questions file not found: {path}")

        report = EvalService.run(EvalService.load_questions(path))
        if not report.answerable:
            raise CommandError("No answerable cases in the questions file")

        for case in report.cases:
            if case.expected and not options["verbose"] and case.rank == 1:
                continue
            if not case.expected:
                status = "N/A "  # unanswerable on purpose; see the distance summary below
            else:
                status = "OK  " if case.rank == 1 else ("MISS" if case.rank is None else f"#{case.rank}  ")
            self.stdout.write(f"[{status}] {case.question}")
            if case.expected and case.rank != 1:
                self.stdout.write(f"         expected: {', '.join(case.expected)}")
                self.stdout.write(f"         got:      {', '.join(case.ranked_documents[:3])}")

        self.stdout.write("")
        self.stdout.write(f"Answerable questions: {len(report.answerable)}")
        for k in report.ks:
            self.stdout.write(f"hit rate @{k}: {report.hit_rate(k):.0%}")
        self.stdout.write(f"MRR:          {report.mrr:.3f}")
        if report.unanswerable:
            distances = ", ".join(f"{c.best_distance:.3f}" for c in report.unanswerable if c.best_distance is not None)
            answerable = [c.best_distance for c in report.answerable if c.best_distance is not None]
            self.stdout.write(
                f"Best distance for unanswerable questions: {distances} "
                f"(answerable: min {min(answerable):.3f}, max {max(answerable):.3f})"
            )
