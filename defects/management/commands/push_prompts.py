from django.core.management.base import BaseCommand, CommandError

from defects.triage import prompt_provider as provider


class Command(BaseCommand):
    help = (
        "Upload the local triage prompts (defects/triage/prompt_templates) to the LangSmith prompt hub as a new "
        "commit, when their text differs from the latest one. Moving the production tag stays a manual step."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Only show what would be uploaded.")

    def handle(self, *args, **options):
        from langsmith.utils import LangSmithNotFoundError

        client = provider.get_client()
        for name in provider.PROMPT_NAMES:
            local = provider.local_prompt(name)
            try:
                provider.validate_prompt_text(name, local.text)
            except provider.PromptInvalid as exc:
                raise CommandError(f"Local prompt is invalid, nothing uploaded: {exc}") from exc

            latest = None
            try:
                latest = client.pull_prompt_commit(f"{name}:latest", skip_cache=True)
            except (LangSmithNotFoundError, ValueError):
                pass  # the prompt does not exist yet, or has no commits

            if latest is not None and self._same_text(latest, local.text):
                self.stdout.write(f"{name}: unchanged (commit {latest.commit_hash[:8]})")
                continue
            if options["dry_run"]:
                self.stdout.write(f"{name}: would upload {'a new version' if latest else 'a new prompt'}")
                continue

            url = client.push_prompt(
                name,
                object=provider.make_template(local.text),
                is_public=False,
                description="Defect triage workflow of the dental laboratory",
                commit_description=f"Synced from the repository (file hash {local.version})",
            )
            self.stdout.write(self.style.SUCCESS(f"{name}: uploaded {url}"))

        self.stdout.write("Tag the commit you want to use as 'production' in the LangSmith UI.")

    @staticmethod
    def _same_text(commit, text: str) -> bool:
        try:
            return provider.extract_system_text(commit.manifest) == text
        except provider.PromptInvalid:
            return False
