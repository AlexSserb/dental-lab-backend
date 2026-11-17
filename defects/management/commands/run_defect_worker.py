from django.core.management.base import BaseCommand

from defects.graph import build_graph
from defects.worker import DefectWorker, checkpointer_dsn


class Command(BaseCommand):
    help = (
        "Run the defect triage worker: it polls DefectTriage, starts the graph for submitted rows and resumes "
        "the paused graph for decided rows. The LangGraph checkpoint tables are created by an idempotent setup() "
        "at startup, so a fresh database needs no extra migration step."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--once", action="store_true", help="Run a single polling pass and exit (used by tests and cron).",
        )
        parser.add_argument(
            "--interval", type=float, default=None,
            help="Seconds between polls when there is nothing to do (default: DEFECT_WORKER_POLL_S or 2).",
        )

    def handle(self, *args, **options):
        from langgraph.checkpoint.postgres import PostgresSaver

        with PostgresSaver.from_conn_string(checkpointer_dsn()) as checkpointer:
            checkpointer.setup()  # idempotent: creates the checkpoint tables if they do not exist yet
            worker = DefectWorker(graph=build_graph(checkpointer), poll_interval_s=options["interval"])
            if options["once"]:
                worker.tick()
            else:
                worker.run_forever()
