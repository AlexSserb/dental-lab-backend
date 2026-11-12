from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from knowledge.services.eval_service import DEFAULT_QUESTIONS, EvalService


class Command(BaseCommand):
    help = "Measure retrieval quality (hit rate @k and MRR) on a set of questions with expected source documents"

    def add_arguments(self, parser):
        parser.add_argument("--questions", default=str(DEFAULT_QUESTIONS), help="Path to a JSON file with cases")
        parser.add_argument("--mode", choices=["dense", "keyword", "hybrid", "rerank"], default="hybrid",
                            help="Search to evaluate (default: hybrid = vector + keyword merged with RRF; rerank = hybrid + cross-encoder)")
        parser.add_argument("--compare", action="store_true", help="Evaluate every mode side by side")
        parser.add_argument("--verbose", action="store_true", help="Show every question, not only failures")

    def handle(self, *args, **options):
        path = Path(options["questions"])
        if not path.is_file():
            raise CommandError(f"Questions file not found: {path}")

        questions = EvalService.load_questions(path)
        if options["compare"]:
            return self.compare(questions)

        report = EvalService.run(questions, mode=options["mode"])
        if not report.answerable:
            raise CommandError("No answerable cases in the questions file")
        self.stdout.write(f"Mode: {options['mode']}\n")

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
            off_topic = [c.best_rerank_score for c in report.unanswerable if c.best_rerank_score is not None]
            real = [c.best_rerank_score for c in report.answerable if c.best_rerank_score is not None]
            if off_topic and real:
                self.stdout.write(
                    f"Best rerank score for unanswerable questions: {', '.join(f'{x:.2f}' for x in off_topic)} "
                    f"(answerable: min {min(real):.2f}, max {max(real):.2f})"
                )

    def compare(self, questions):
        reports = {mode: EvalService.run(questions, mode=mode) for mode in ("dense", "keyword", "hybrid", "rerank")}
        if not reports["dense"].answerable:
            raise CommandError("No answerable cases in the questions file")

        self.stdout.write(f"{'mode':9} {'hit@1':>6} {'hit@3':>6} {'hit@5':>6} {'MRR':>7}")
        for mode, report in reports.items():
            self.stdout.write(
                f"{mode:9} {report.hit_rate(1):>6.0%} {report.hit_rate(3):>6.0%} "
                f"{report.hit_rate(5):>6.0%} {report.mrr:>7.3f}"
            )
        self.stdout.write(f"\nAnswerable questions: {len(reports['dense'].answerable)}")
