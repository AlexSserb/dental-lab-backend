from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from orders.models import Order
from .models import Work
from operations.models import OperationStatus, Operation
from .serializers import WorkSerializer, WorkAndOperationsSerializer


class WorkService:
    @staticmethod
    def get_for_order(order_id: str) -> Response:
        works = Work.objects.filter(order=order_id)
        serializer = WorkSerializer(works, many=True)
        return Response(serializer.data)

    @staticmethod
    def get_works_with_operations(order_id):
        """
        View is called once during the formation of the order by the administrator.
        An operation list is generated for each item if it has not been generated previously.
        """
        order = get_object_or_404(Order, id=order_id)
        works = order.works.all()
        for work in works:
            if work.operations.count() == 0:
                for operation_type, through in zip(
                    work.work_type.operation_types.all(),
                    work.work_type.operation_types.through.objects.all(),
                ):
                    try:
                        Operation.objects.create(
                            work=work,
                            operation_type=operation_type,
                            operation_status=OperationStatus.get_default_status(),
                            ordinal_number=through.ordinal_number,
                        )
                    except:
                        pass

        serializer = WorkAndOperationsSerializer(order.works, many=True)
        return Response(serializer.data)
