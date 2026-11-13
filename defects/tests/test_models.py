from django.contrib import admin
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import User
from core.tests import BaseTestCase
from defects.admin import DefectCaseAdmin, DefectTriageAdmin
from defects.models import DefectCase, DefectSeverity, DefectTriage, DefectType
from operations.models import OperationType
from orders.models import Order
from works.models import Work


class DefectModelsTest(BaseTestCase):
    order_id = "c5f7d483-347b-4cbb-93b2-f9de7cd03cc9"
    other_order_id = "68eb5be8-d29f-4a6c-ac64-5be9740fb3f3"
    work_id = "60b5e09a-9d70-486e-a010-64f3504ce0a9"

    def _triage(self, order_id=None, **kwargs) -> DefectTriage:
        return DefectTriage.objects.create(order_id=order_id or self.order_id, **kwargs)

    def test_new_triage_defaults(self):
        triage = self._triage(comment="Коронка не садится")

        self.assertEqual(triage.state, DefectTriage.State.SUBMITTED)
        self.assertEqual(triage.proposal, {})
        self.assertEqual(triage.final, {})
        self.assertEqual(triage.revisions, 0)
        self.assertEqual(triage.decision, "")
        self.assertIsNone(triage.decided_at)
        self.assertEqual(triage.thread_id, str(triage.id))

    def test_triage_links_works_reporter_and_order(self):
        reporter = User.objects.get(email=self.physician_email)
        triage = self._triage(reported_by=reporter)
        triage.works.add(Work.objects.get(id=self.work_id))

        order = Order.objects.get(id=self.order_id)
        self.assertEqual(list(order.defect_triages.all()), [triage])
        self.assertEqual(list(triage.works.values_list("id", flat=True)), [Work.objects.get(id=self.work_id).id])
        self.assertEqual(list(reporter.reported_defect_triages.all()), [triage])

    def test_second_open_triage_for_the_same_order_is_rejected(self):
        for state in DefectTriage.OPEN_STATES:
            with self.subTest(state=state):
                DefectTriage.objects.all().delete()
                self._triage(state=state)
                with self.assertRaises(IntegrityError), transaction.atomic():
                    self._triage()

    def test_new_triage_is_allowed_after_the_previous_one_is_finished(self):
        for state in (DefectTriage.State.APPLIED, DefectTriage.State.REJECTED, DefectTriage.State.FAILED):
            with self.subTest(state=state):
                DefectTriage.objects.all().delete()
                self._triage(state=state)
                self._triage()  # does not raise

    def test_open_triages_of_different_orders_do_not_conflict(self):
        self._triage()
        self._triage(order_id=self.other_order_id)

        self.assertEqual(DefectTriage.objects.count(), 2)

    def test_constraint_matches_open_states(self):
        # The constraint lists plain strings (Meta cannot see State); keep them in sync with OPEN_STATES.
        constraint = next(c for c in DefectTriage._meta.constraints if c.name == "unique_open_defect_triage_per_order")
        (lookup, values), = constraint.condition.children

        self.assertEqual(lookup, "state__in")
        self.assertEqual(set(values), {state.value for state in DefectTriage.OPEN_STATES})

    def test_deleting_the_reporter_keeps_the_triage(self):
        reporter = User.objects.create(email="gone@mail.com", first_name="A", last_name="B")
        triage = self._triage(reported_by=reporter)

        reporter.delete()

        triage.refresh_from_db()
        self.assertIsNone(triage.reported_by)

    def test_case_is_created_without_embedding(self):
        case = DefectCase.objects.create(
            defect_type=DefectType.FIT,
            severity=DefectSeverity.MEDIUM,
            description="Коронка не садится на штампик",
            cause="Слишком плотные контактные пункты",
            search_text="Коронка не садится на штампик. Причина: слишком плотные контактные пункты",
        )

        case.refresh_from_db()
        self.assertIsNone(case.embedding)
        self.assertEqual(case.source, DefectCase.Source.TRIAGE)
        self.assertEqual(case.resolution, "")

    def test_case_stores_embedding_and_survives_triage_deletion(self):
        triage = self._triage()
        operation_type = OperationType.objects.first()
        case = DefectCase.objects.create(
            triage=triage,
            operation_type=operation_type,
            defect_type=DefectType.POROSITY,
            severity=DefectSeverity.LOW,
            description="Пузыри в керамике",
            cause="Слишком быстрый нагрев",
            search_text="Пузыри в керамике",
            embedding=[0.1] * 1024,
        )

        self.assertEqual(len(DefectCase.objects.get(id=case.id).embedding), 1024)
        self.assertEqual(triage.case, case)

        triage.delete()

        case.refresh_from_db()
        self.assertIsNone(case.triage)

    def test_case_has_no_customer_or_order_data(self):
        names = {field.name for field in DefectCase._meta.get_fields()}

        self.assertFalse(names & {"order", "customer", "user", "reported_by", "decided_by"})


class DefectAdminTest(TestCase):
    def test_models_are_registered_read_only(self):
        for model, model_admin in ((DefectTriage, DefectTriageAdmin), (DefectCase, DefectCaseAdmin)):
            with self.subTest(model=model.__name__):
                registered = admin.site._registry[model]
                self.assertIsInstance(registered, model_admin)
                self.assertFalse(registered.has_add_permission(None))
                self.assertFalse(registered.has_delete_permission(None))

    def test_embedding_is_hidden_in_admin(self):
        self.assertIn("embedding", DefectCaseAdmin.exclude)
        self.assertNotIn("embedding", DefectCaseAdmin.readonly_fields)
