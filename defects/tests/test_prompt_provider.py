import io
import logging
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, override_settings
from langchain_core.load import dumpd
from langsmith.utils import LangSmithNotFoundError

from defects.triage import prompt_provider as provider
from defects.triage.prompt_provider import CLASSIFY, PROPOSE, PromptInvalid

HUB = dict(PROMPT_SOURCE="langsmith", PROMPT_TAG="production", PROMPT_CACHE_TTL_S=300, PROMPT_FAILURE_BACKOFF_S=60)


def manifest(text: str) -> dict:
    """What the hub stores for a one-message prompt: produced by LangChain itself, not written by hand."""
    return dumpd(provider.make_template(text))


def commit(text: str, commit_hash: str = "abc12345def") -> SimpleNamespace:
    return SimpleNamespace(manifest=manifest(text), commit_hash=commit_hash)


class LocalPromptTest(SimpleTestCase):
    def test_every_local_prompt_passes_validation(self):
        for name in provider.PROMPT_NAMES:
            with self.subTest(name=name):
                provider.validate_prompt_text(name, provider.local_prompt(name).text)

    def test_local_version_is_a_content_hash(self):
        first = provider.local_prompt(CLASSIFY)

        self.assertEqual(first.source, "local")
        self.assertEqual(len(first.version), 12)
        self.assertEqual(first.version, provider.local_prompt(CLASSIFY).version)
        self.assertNotEqual(first.version, provider.local_prompt(PROPOSE).version)
        self.assertEqual(first.label, f"local:{first.version}")

    @override_settings(PROMPT_SOURCE="local")
    def test_local_source_never_touches_langsmith(self):
        with patch.object(provider, "get_client") as get_client:
            prompt = provider.get_prompt(CLASSIFY)

        self.assertEqual(prompt, provider.local_prompt(CLASSIFY))
        get_client.assert_not_called()

    def test_unknown_prompt_name(self):
        with self.assertRaises(KeyError):
            provider.get_prompt("nope")


class ManifestTest(SimpleTestCase):
    def test_text_survives_a_round_trip_through_langchain_serialization(self):
        for name in provider.PROMPT_NAMES:
            with self.subTest(name=name):
                text = provider.local_prompt(name).text
                self.assertEqual(provider.extract_system_text(manifest(text)), text)

    def test_json_braces_are_not_template_variables(self):
        self.assertEqual(provider.make_template(provider.local_prompt(CLASSIFY).text).input_variables, [])

    def test_rejects_prompts_with_variables(self):
        with self.assertRaises(PromptInvalid):
            provider.extract_system_text(dumpd(provider.make_template("Hello {{name}}")))

    def test_rejects_more_than_one_message_and_non_system_messages(self):
        from langchain_core.prompts import ChatPromptTemplate

        two = ChatPromptTemplate.from_messages([("system", "a"), ("human", "b")], template_format="mustache")
        human = ChatPromptTemplate.from_messages([("human", "a")], template_format="mustache")
        for template in (two, human):
            with self.assertRaises(PromptInvalid):
                provider.extract_system_text(dumpd(template))

    def test_rejects_garbage_manifests(self):
        for bad in ({}, {"kwargs": {}}, {"kwargs": {"messages": []}}, None, "text"):
            with self.subTest(bad=bad), self.assertRaises(PromptInvalid):
                provider.extract_system_text(bad)


class ValidationTest(SimpleTestCase):
    def test_a_missing_label_is_rejected(self):
        text = provider.local_prompt(CLASSIFY).text.replace("crack_chipping", "cracks")

        with self.assertRaisesMessage(PromptInvalid, "crack_chipping"):
            provider.validate_prompt_text(CLASSIFY, text)

    def test_a_missing_tag_is_rejected(self):
        text = provider.local_prompt(CLASSIFY).text.replace("<report>", "")

        with self.assertRaisesMessage(PromptInvalid, "report"):
            provider.validate_prompt_text(CLASSIFY, text)

    def test_an_example_that_breaks_the_schema_is_rejected(self):
        text = provider.local_prompt(PROPOSE).text.replace('"operation_number":2', '"operation_number":0')

        with self.assertRaisesMessage(PromptInvalid, "schema"):
            provider.validate_prompt_text(PROPOSE, text)

    def test_a_prompt_without_examples_is_rejected(self):
        with self.assertRaisesMessage(PromptInvalid, "example"):
            provider.validate_prompt_text(PROPOSE, "<feedback>")


@override_settings(**HUB)
class HubPromptTest(SimpleTestCase):
    def setUp(self):
        # manage.py calls logging.disable(CRITICAL) for `test`; lift it so the warnings can be asserted
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, logging.CRITICAL)
        provider.clear_cache()
        self.addCleanup(provider.clear_cache)
        self.local = provider.local_prompt(CLASSIFY)
        self.client = MagicMock()
        patcher = patch.object(provider, "get_client", return_value=self.client)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _hub_text(self) -> str:
        return self.local.text + "\n# edited in the hub"

    def test_pulls_the_tagged_version_and_records_the_commit(self):
        self.client.pull_prompt_commit.return_value = commit(self._hub_text(), "deadbeef0001")

        prompt = provider.get_prompt(CLASSIFY)

        self.client.pull_prompt_commit.assert_called_once_with(f"{CLASSIFY}:production", skip_cache=True)
        self.assertEqual(prompt.source, "langsmith")
        self.assertEqual(prompt.version, "deadbeef0001")
        self.assertEqual(prompt.text, self._hub_text().strip())

    @override_settings(PROMPT_TAG="staging")
    def test_the_tag_comes_from_settings(self):
        self.client.pull_prompt_commit.return_value = commit(self._hub_text())

        provider.get_prompt(CLASSIFY)

        self.client.pull_prompt_commit.assert_called_once_with(f"{CLASSIFY}:staging", skip_cache=True)

    def test_a_pulled_prompt_is_reused_until_the_ttl_expires(self):
        self.client.pull_prompt_commit.side_effect = [
            commit(self._hub_text(), "commit-1"), commit(self._hub_text() + " v2", "commit-2"),
        ]
        with patch.object(provider.time, "monotonic", side_effect=[1000, 1100, 1301]):
            first = provider.get_prompt(CLASSIFY)   # pulled at t=1000, valid until 1300
            second = provider.get_prompt(CLASSIFY)  # t=1100: from the cache
            third = provider.get_prompt(CLASSIFY)   # t=1301: expired, pulled again

        self.assertEqual((first.version, second.version, third.version), ("commit-1", "commit-1", "commit-2"))
        self.assertEqual(self.client.pull_prompt_commit.call_count, 2)

    def test_failure_falls_back_to_the_local_file(self):
        self.client.pull_prompt_commit.side_effect = LangSmithNotFoundError("no such tag")

        with self.assertLogs(provider.logger, "WARNING") as logs:
            prompt = provider.get_prompt(CLASSIFY)

        self.assertEqual(prompt, self.local)
        self.assertIn("using local:", logs.output[0])

    def test_failure_after_success_keeps_the_last_good_prompt(self):
        self.client.pull_prompt_commit.side_effect = [commit(self._hub_text(), "good"), ConnectionError("down")]
        with patch.object(provider.time, "monotonic", side_effect=[1000, 1301]):
            provider.get_prompt(CLASSIFY)
            with self.assertLogs(provider.logger, "WARNING"):
                stale = provider.get_prompt(CLASSIFY)

        self.assertEqual(stale.version, "good")

    def test_after_a_failure_langsmith_is_left_alone_for_the_backoff_period(self):
        self.client.pull_prompt_commit.side_effect = ConnectionError("down")
        with patch.object(provider.time, "monotonic", side_effect=[1000, 1030, 1061]):
            with self.assertLogs(provider.logger, "WARNING"):
                provider.get_prompt(CLASSIFY)  # fails at t=1000
                provider.get_prompt(CLASSIFY)  # t=1030: still backing off
                provider.get_prompt(CLASSIFY)  # t=1061: tries again

        self.assertEqual(self.client.pull_prompt_commit.call_count, 2)

    def test_an_invalid_edit_in_the_hub_is_not_used(self):
        broken = self.local.text.replace("<report>", "")
        self.client.pull_prompt_commit.return_value = commit(broken)

        with self.assertLogs(provider.logger, "WARNING") as logs:
            prompt = provider.get_prompt(CLASSIFY)

        self.assertEqual(prompt, self.local)
        self.assertIn("PromptInvalid", logs.output[0])

    def test_a_hub_prompt_with_variables_is_not_used(self):
        self.client.pull_prompt_commit.return_value = SimpleNamespace(
            manifest=dumpd(provider.make_template("Hello {{name}} <report>")), commit_hash="x",
        )

        with self.assertLogs(provider.logger, "WARNING"):
            self.assertEqual(provider.get_prompt(CLASSIFY), self.local)

    def test_a_failure_to_create_the_client_also_falls_back(self):
        with patch.object(provider, "get_client", side_effect=RuntimeError("no API key")):
            with self.assertLogs(provider.logger, "WARNING"):
                self.assertEqual(provider.get_prompt(CLASSIFY), self.local)


@override_settings(**HUB)
class PushPromptsCommandTest(SimpleTestCase):
    def setUp(self):
        self.client = MagicMock()
        self.client.push_prompt.return_value = "https://smith.example/prompts/x"
        patcher = patch.object(provider, "get_client", return_value=self.client)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _run(self, *args) -> str:
        out = io.StringIO()
        with redirect_stdout(out):
            call_command("push_prompts", *args, stdout=out)
        return out.getvalue()

    def test_uploads_prompts_that_do_not_exist_yet(self):
        self.client.pull_prompt_commit.side_effect = LangSmithNotFoundError("missing")

        output = self._run()

        self.assertEqual(self.client.push_prompt.call_count, len(provider.PROMPT_NAMES))
        _, kwargs = self.client.push_prompt.call_args
        self.assertFalse(kwargs["is_public"])
        self.assertEqual(provider.extract_system_text(dumpd(kwargs["object"])), provider.local_prompt(PROPOSE).text)
        self.assertIn("uploaded", output)
        self.assertIn("production", output)

    def test_skips_prompts_that_are_unchanged(self):
        self.client.pull_prompt_commit.side_effect = lambda ident, **_: commit(
            provider.local_prompt(ident.split(":")[0]).text, "0123456789"
        )

        output = self._run()

        self.client.push_prompt.assert_not_called()
        self.assertEqual(output.count("unchanged"), len(provider.PROMPT_NAMES))

    def test_uploads_a_new_version_when_the_text_differs(self):
        self.client.pull_prompt_commit.return_value = commit("some older text")

        self._run()

        self.assertEqual(self.client.push_prompt.call_count, len(provider.PROMPT_NAMES))

    def test_dry_run_uploads_nothing(self):
        self.client.pull_prompt_commit.side_effect = LangSmithNotFoundError("missing")

        output = self._run("--dry-run")

        self.client.push_prompt.assert_not_called()
        self.assertIn("would upload", output)

    def test_refuses_to_upload_an_invalid_local_prompt(self):
        with patch.object(provider, "validate_prompt_text", side_effect=PromptInvalid("broken")):
            with self.assertRaisesMessage(CommandError, "broken"):
                self._run()

        self.client.push_prompt.assert_not_called()
