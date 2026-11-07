from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from knowledge.services.ingest_service import IngestService


class Command(BaseCommand):
    help = "Chunk, embed and store the markdown knowledge base into the database"

    def add_arguments(self, parser):
        parser.add_argument("--path", default=str(Path(settings.BASE_DIR) / "documents" / "knowledge_base"))
        parser.add_argument("--force", action="store_true", help="Re-ingest files even if their content is unchanged")

    def handle(self, *args, **options):
        try:
            result = IngestService.ingest(Path(options["path"]), force=options["force"])
        except (FileNotFoundError, ValueError) as e:
            raise CommandError(str(e))

        for label in ("created", "updated", "skipped", "deleted"):
            for path in getattr(result, label):
                self.stdout.write(f"{label:8} {path}")
        self.stdout.write(self.style.SUCCESS(
            f"Done: {len(result.created)} created, {len(result.updated)} updated, "
            f"{len(result.skipped)} skipped, {len(result.deleted)} deleted"
        ))
