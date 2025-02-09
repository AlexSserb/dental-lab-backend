from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsLabAdmin, IsTech
from operations.serializers import *
from .service import OperationService


class OperationTypeList(APIView):
    serializer_class = OperationTypeSerializer
    permission_classes = [IsLabAdmin | IsTech]

    def get(self, request, *args, **kwargs):
        operation_types = OperationType.objects.all()
        serializer = self.serializer_class(operation_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OperationTypeDetail(APIView):
    """
    Retrieve, update or delete an operation type instance.
    """

    permission_classes = [IsLabAdmin]
    serializer_class = OperationTypeSerializer

    def get_object(self, pk):
        try:
            return OperationType.objects.get(pk=pk)
        except OperationType.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        oper_type = self.get_object(pk)
        serializer = self.serializer_class(oper_type)
        return Response(serializer.data)

    def put(self, request, pk):
        oper_type = self.get_object(pk)
        serializer = self.serializer_class(oper_type, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        oper_type = self.get_object(pk)
        oper_type.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(responses=OperationSerializer)
@api_view(["GET"])
@permission_classes([IsTech])
def get_operations_for_tech(request):
    return OperationService.get_for_tech(request)


@extend_schema(responses=OperationForProductSerializer)
@api_view(["GET"])
@permission_classes([IsLabAdmin])
def get_operations_for_product(request, product_id):
    return OperationService.get_for_product(product_id)


@extend_schema(responses=OperationForScheduleSerializer)
@api_view(["GET"])
@permission_classes([IsTech | IsLabAdmin])
def get_operations_for_schedule(request, date: str, user_email: str):
    operation_service = OperationService()
    return operation_service.get_for_schedule(user_email, date)


@extend_schema()
@api_view(["PATCH"])
@permission_classes([IsLabAdmin])
def set_operation_exec_start(request, id: str, exec_start: str):
    return OperationService.set_execution_start(id, exec_start)


@extend_schema(request=AssignOperationSerializer)
@api_view(["PATCH"])
@permission_classes([IsLabAdmin])
def assign_operation(request):
    serializer = AssignOperationSerializer(data=request.data)
    if serializer.is_valid():
        return OperationService.assign(serializer)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OperationDetail(APIView):
    """
    Retrieve, update or delete an operation instance.
    """

    permission_classes = [IsTech]
    serializer_class = OperationSerializer

    def get_object(self, pk):
        try:
            return Operation.objects.get(pk=pk)
        except Operation.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        operation = self.get_object(pk)
        serializer = self.serializer_class(operation)
        return Response(serializer.data)

    @extend_schema(request=UpdateOperationStatusSerializer)
    def patch(self, request, pk, format=None):
        """
        Allows only the status of an operation to be changed via the status field
        """
        serializer = UpdateOperationStatusSerializer(data=request.data)
        if serializer.is_valid():
            operation = get_object_or_404(Operation, id=pk)
            operation.operation_status = serializer.validated_data["status"]
            operation.save()
            return Response(self.serializer_class(operation).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        operation = self.get_object(pk)
        operation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OperationStatusesList(ListAPIView):
    queryset = OperationStatus.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = OperationStatusSerializer
