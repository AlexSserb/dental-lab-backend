import enum
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from operations.models import Operation
from orders.models import Order
from works.models import Work


class OrderStatuses(enum.StrEnum):
    READY = "3912b571-4f2d-4158-ab12-a260fe96438e"
    ORDER_FORMED = "40182114-bf8a-4e78-a5d3-491c778611eb"
    DEFECT_FOUND = "591d46af-362f-4ddd-933f-c00ae17ddc9b"
    CANCELLED = "614e7fcd-37cb-4984-b6a3-df3a8d81b538"
    SENT_FOR_FORMING = "65da8938-9777-46df-be9e-1bdf94015041"
    IN_PROCESS = "a759097c-91a9-4749-a1e9-93edeb07fc0b"


class WorkStatuses(enum.StrEnum):
    DEFECT_FOUND = "3710f296-d25e-4833-8a46-6e1321b7844e"
    WAITING = "45580d30-0dd4-489d-869f-791bd991b2e5"
    IN_PROCESS = "6cbdb7a5-f7fc-4b7f-96bb-a21caf55045b"
    READY = "caa4c903-ae62-414b-9b27-21dc38f326ce"


class OperationStatuses(enum.StrEnum):
    NOT_STARTED = "2c91175c-2036-4152-a917-a4fcb5054f03"
    IN_WORK = "d36c536b-7c07-495c-a34e-8cb0a5ccc3f1"
    COMPLETED = "efee01cc-e81b-4936-8580-33e778ae0f67"


class OperationTypes(enum.StrEnum):
    MODELS = "842cb14e-a654-4081-8334-b87917a62040"
    CAD_CAM = "61e5d3e3-f999-4fd6-be1a-778cc1ce3332"
    CERAMICS = "b44d904a-9e53-417a-ba1c-9047e302d6a8"
    PROTES = "c643d713-ff30-419f-858f-6756a14cfaaa"


class WorkTypes(enum.StrEnum):
    WORK_1 = "a038f028-cfda-4e8b-b971-44cf7d5b84ae"
    WORK_2 = "6622d6e9-b655-4894-acab-885bf17fa6a7"
    WORK_3 = "ce26c7f9-9afb-44cd-87ae-adb1b9f135d4"


class Techs(enum.StrEnum):
    MODELS_1 = "29992e9d-9411-4878-b34d-8fea1169fc86"
    MODELS_2 = "f4ae7284-ae01-471c-ac99-ad41ca5b6792"
    MODELS_3 = "93bc57e2-3cd5-41ff-a4ab-3b5e7668bf60"
    CAD_CAM_1 = "4d02e9e6-7c7f-4f54-8942-6074c671be5f"
    CAD_CAM_2 = "b2859181-5be4-472d-8dab-922228d58054"
    CAD_CAM_3 = "4afa008d-9f53-4d7f-a81c-f021e7769827"
    CERAMICS_1 = "b7a6e126-f48b-465f-842d-0e3b7e630e7e"
    CERAMICS_2 = "998ed10d-0572-4615-a4bc-e09ae2a0a0de"
    CERAMICS_3 = "2b7880af-4c0e-4c49-b34b-d79230b1978f"
    PROTES_1 = "18904e24-f32c-4c54-9fe7-58f5e7747c58"
    PROTES_2 = "6f3f3dd7-36d2-4e24-a35d-7804a85afc67"


CUSTOMER_ID = "a2203146-68ba-411f-ba45-815a52ef7236"

DOCTOR_ID = "4852bf52-dced-4e76-87a0-e8f67462dbc1"


class WORKS(enum.StrEnum):
    WORK_1 = "2b1fa828-44aa-42d3-bb5c-6802c52097c3"
    WORK_2 = "60b5e09a-9d70-486e-a010-64f3504ce0a9"
    WORK_3 = "8186b733-ff3f-4e28-8361-9701cb63e5e5"


class Command(BaseCommand):
    def handle(self, **options):
        now = timezone.now()
        start = datetime(year=now.year, month=now.month, day=now.day, hour=4, minute=0, second=0, microsecond=0)

        print("Start loading data")

        Operation.objects.all().delete()
        Work.objects.all().delete()
        Order.objects.all().delete()

        # region order 1
        order1 = Order(
            user_id=DOCTOR_ID,
            status_id=OrderStatuses.IN_PROCESS,
            order_date=start - timedelta(days=1),
            deadline=start + timedelta(days=4),
            discount=5,
            comment="",
            customer_id=CUSTOMER_ID,
            tooth_color="A1",
        )
        order1.save()

        work1 = Work(
            work_type_id=WorkTypes.WORK_1,
            work_status_id=WorkStatuses.IN_PROCESS,
            order_id=order1.id,
            amount=5,
            discount=0,
            teeth=[21, 24, 25, 26, 27],
        )
        work1.save()

        work2 = Work(
            work_type_id=WorkTypes.WORK_2,
            work_status_id=WorkStatuses.IN_PROCESS,
            order_id=order1.id,
            amount=4,
            discount=0,
            teeth=[44, 45, 46, 47],
        )
        work2.save()

        work3 = Work(
            work_type_id=WorkTypes.WORK_3,
            work_status_id=WorkStatuses.IN_PROCESS,
            order_id=order1.id,
            amount=2,
            discount=6,
            teeth=[41, 42],
        )
        work3.save()

        # endregion order 1

        # region order 2
        order2 = Order(
            user_id=DOCTOR_ID,
            status_id=OrderStatuses.IN_PROCESS,
            order_date=start - timedelta(days=1),
            deadline=start + timedelta(days=4),
            discount=5,
            comment="",
            customer_id=CUSTOMER_ID,
            tooth_color="C2",
        )
        order2.save()

        work4 = Work(
            work_type_id=WorkTypes.WORK_1,
            work_status_id=WorkStatuses.IN_PROCESS,
            order_id=order2.id,
            amount=5,
            discount=7,
            teeth=[11, 14, 15, 32, 33],
        )
        work4.save()

        work5 = Work(
            work_type_id=WorkTypes.WORK_2,
            work_status_id=WorkStatuses.IN_PROCESS,
            order_id=order2.id,
            amount=4,
            discount=0,
            teeth=[11, 12, 32, 33],
        )
        work5.save()

        work6 = Work(
            work_type_id=WorkTypes.WORK_3,
            work_status_id=WorkStatuses.IN_PROCESS,
            order_id=order2.id,
            amount=2,
            discount=6,
            teeth=[41, 42],
        )
        work6.save()
        # endregion

        # region order 3
        order3 = Order(
            user_id=DOCTOR_ID,
            status_id=OrderStatuses.IN_PROCESS,
            order_date=start - timedelta(days=1),
            deadline=start + timedelta(days=4),
            discount=5,
            comment="",
            customer_id=CUSTOMER_ID,
            tooth_color="D2",
        )
        order3.save()

        work7 = Work(
            work_type_id=WorkTypes.WORK_1,
            work_status_id=WorkStatuses.IN_PROCESS,
            order_id=order3.id,
            amount=5,
            discount=7,
            teeth=[11, 14, 15, 32, 33],
        )
        work7.save()

        work8 = Work(
            work_type_id=WorkTypes.WORK_2,
            work_status_id=WorkStatuses.IN_PROCESS,
            order_id=order3.id,
            amount=4,
            discount=0,
            teeth=[11, 12, 32, 33],
        )
        work8.save()

        work9 = Work(
            work_type_id=WorkTypes.WORK_3,
            work_status_id=WorkStatuses.IN_PROCESS,
            order_id=order3.id,
            amount=2,
            discount=6,
            teeth=[41, 42],
        )
        work9.save()
        # endregion

        # region order 4 DEFECT
        order4 = Order(
            user_id=DOCTOR_ID,
            status_id=OrderStatuses.DEFECT_FOUND,
            order_date=start - timedelta(days=5),
            deadline=start + timedelta(days=1),
            discount=0,
            comment="",
            customer_id=CUSTOMER_ID,
            comment_after_accept="Коронка для зуба 13 выполнена не в том цвете.",
            tooth_color="A3",
        )
        order4.save()

        work10 = Work(
            work_type_id=WorkTypes.WORK_1,
            work_status_id=WorkStatuses.DEFECT_FOUND,
            order_id=order4.id,
            amount=5,
            discount=7,
            teeth=[11, 12, 13, 14, 15],
        )
        work10.save()

        work11 = Work(
            work_type_id=WorkTypes.WORK_2,
            work_status_id=WorkStatuses.READY,
            order_id=order4.id,
            amount=1,
            discount=7,
            teeth=[11],
        )
        work11.save()
        # endregion

        # region order 5 COMPLETED
        order5 = Order(
            user_id=DOCTOR_ID,
            status_id=OrderStatuses.READY,
            order_date=start - timedelta(days=5),
            deadline=start + timedelta(days=1),
            discount=4,
            comment="",
            customer_id=CUSTOMER_ID,
            comment_after_accept="",
            tooth_color="B1",
        )
        order5.save()

        work12 = Work(
            work_type_id=WorkTypes.WORK_3,
            work_status_id=WorkStatuses.READY,
            order_id=order5.id,
            amount=1,
            discount=7,
            teeth=[44],
        )
        work12.save()

        work13 = Work(
            work_type_id=WorkTypes.WORK_2,
            work_status_id=WorkStatuses.READY,
            order_id=order5.id,
            amount=2,
            discount=7,
            teeth=[11, 12],
        )
        work13.save()
        # endregion

        # region order 6 FRESH
        order6 = Order(
            user_id=DOCTOR_ID,
            status_id=OrderStatuses.SENT_FOR_FORMING,
            order_date=start - timedelta(days=5),
            deadline=start + timedelta(days=1),
            discount=0,
            comment="",
            customer_id=CUSTOMER_ID,
            comment_after_accept="",
            tooth_color="D4",
        )
        order6.save()

        work14 = Work(
            work_type_id=WorkTypes.WORK_3,
            work_status_id=WorkStatuses.READY,
            order_id=order6.id,
            amount=3,
            discount=0,
            teeth=[44, 45, 46],
        )
        work14.save()

        work15 = Work(
            work_type_id=WorkTypes.WORK_2,
            work_status_id=WorkStatuses.READY,
            order_id=order6.id,
            amount=1,
            discount=0,
            teeth=[22],
        )
        work15.save()

        work16 = Work(
            work_type_id=WorkTypes.WORK_1,
            work_status_id=WorkStatuses.READY,
            order_id=order6.id,
            amount=3,
            discount=0,
            teeth=[35, 36, 37],
        )
        work16.save()
        # endregion

        # operations
        datas = [
            # region work 1
            Operation(
                operation_type_id=OperationTypes.MODELS,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work1.id,
                tech_id=Techs.MODELS_1,
                created_at=start - timedelta(days=1),
                ordinal_number=1,
                exec_start=start,
                is_exec_start_editable=True,
            ),
            Operation(
                operation_type_id=OperationTypes.CAD_CAM,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work1.id,
                tech_id=Techs.CAD_CAM_1,
                created_at=start - timedelta(days=1),
                ordinal_number=2,
                exec_start=start + timedelta(hours=1, minutes=20),
                is_exec_start_editable=True,
            ),
            Operation(
                operation_type_id=OperationTypes.CERAMICS,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work1.id,
                tech_id=Techs.CERAMICS_2,
                created_at=start - timedelta(days=1),
                ordinal_number=3,
                exec_start=start + timedelta(hours=2, minutes=25),
                is_exec_start_editable=True,
            ),
            # endregion
            # region work 2
            Operation(
                operation_type_id=OperationTypes.PROTES,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work2.id,
                tech_id=Techs.CERAMICS_1,
                created_at=start - timedelta(days=1),
                ordinal_number=1,
                exec_start=start + timedelta(hours=0, minutes=50),
                is_exec_start_editable=True,
            ),
            Operation(
                operation_type_id=OperationTypes.CERAMICS,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work2.id,
                tech_id=Techs.PROTES_1,
                created_at=start - timedelta(days=1),
                ordinal_number=2,
                exec_start=start + timedelta(hours=0, minutes=5),
                is_exec_start_editable=True,
            ),
            # endregion
            # region work 3
            Operation(
                operation_type_id=OperationTypes.MODELS,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work3.id,
                tech_id=Techs.MODELS_2,
                created_at=start - timedelta(days=1),
                ordinal_number=1,
                exec_start=start + timedelta(hours=1, minutes=20),
                is_exec_start_editable=True,
            ),
            Operation(
                operation_type_id=OperationTypes.CERAMICS,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work3.id,
                tech_id=Techs.CERAMICS_1,
                created_at=start - timedelta(days=1),
                ordinal_number=2,
                exec_start=start + timedelta(hours=3, minutes=0),
                is_exec_start_editable=True,
            ),
            Operation(
                operation_type_id=OperationTypes.PROTES,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work3.id,
                tech_id=Techs.PROTES_1,
                created_at=start - timedelta(days=1),
                ordinal_number=3,
                exec_start=start + timedelta(hours=5, minutes=5),
                is_exec_start_editable=True,
            ),
            # endregion
            # region work 4
            Operation(
                operation_type_id=OperationTypes.MODELS,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work4.id,
                tech_id=Techs.MODELS_2,
                created_at=start - timedelta(days=1),
                ordinal_number=1,
                exec_start=start,
                is_exec_start_editable=True,
            ),
            Operation(
                operation_type_id=OperationTypes.CERAMICS,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work4.id,
                tech_id=Techs.CERAMICS_2,
                created_at=start - timedelta(days=1),
                ordinal_number=2,
                exec_start=start + timedelta(minutes=50),
                is_exec_start_editable=True,
            ),
            Operation(
                operation_type_id=OperationTypes.PROTES,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work4.id,
                tech_id=Techs.PROTES_1,
                created_at=start - timedelta(days=1),
                ordinal_number=3,
                exec_start=start + timedelta(hours=1, minutes=50),
                is_exec_start_editable=True,
            ),
            # endregion
            # region work 5
            Operation(
                operation_type_id=OperationTypes.MODELS,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work5.id,
                tech_id=Techs.MODELS_3,
                created_at=start - timedelta(days=1),
                ordinal_number=1,
                exec_start=start + timedelta(hours=0, minutes=30),
                is_exec_start_editable=True,
            ),
            Operation(
                operation_type_id=OperationTypes.CERAMICS,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work5.id,
                tech_id=Techs.CERAMICS_3,
                created_at=start - timedelta(days=1),
                ordinal_number=2,
                exec_start=start + timedelta(hours=0, minutes=50),
                is_exec_start_editable=True,
            ),
            Operation(
                operation_type_id=OperationTypes.CAD_CAM,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work5.id,
                tech_id=Techs.CAD_CAM_3,
                created_at=start - timedelta(days=1),
                ordinal_number=3,
                exec_start=start + timedelta(hours=0, minutes=50),
                is_exec_start_editable=True,
            ),
            Operation(
                operation_type_id=OperationTypes.PROTES,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work5.id,
                tech_id=Techs.PROTES_2,
                created_at=start - timedelta(days=1),
                ordinal_number=4,
                exec_start=start + timedelta(hours=1, minutes=5),
                is_exec_start_editable=True,
            ),
            # endregion
            # region work 6
            Operation(
                operation_type_id=OperationTypes.MODELS,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work6.id,
                tech_id=Techs.MODELS_3,
                created_at=start - timedelta(days=1),
                ordinal_number=1,
                exec_start=start,
                is_exec_start_editable=True,
            ),
            Operation(
                operation_type_id=OperationTypes.CAD_CAM,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work6.id,
                tech_id=Techs.CAD_CAM_3,
                created_at=start - timedelta(days=1),
                ordinal_number=2,
                exec_start=start + timedelta(hours=1, minutes=50),
                is_exec_start_editable=True,
            ),
            Operation(
                operation_type_id=OperationTypes.CERAMICS,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work6.id,
                tech_id=Techs.CERAMICS_3,
                created_at=start - timedelta(days=1),
                ordinal_number=3,
                exec_start=start + timedelta(hours=1, minutes=50),
                is_exec_start_editable=True,
            ),
            Operation(
                operation_type_id=OperationTypes.PROTES,
                operation_status_id=OperationStatuses.NOT_STARTED,
                work_id=work6.id,
                tech_id=Techs.PROTES_2,
                created_at=start - timedelta(days=1),
                ordinal_number=4,
                exec_start=start + timedelta(hours=2, minutes=5),
                is_exec_start_editable=True,
            ),
            # endregion
        ]
        Operation.objects.bulk_create(datas)

        print("Finish loading data")
