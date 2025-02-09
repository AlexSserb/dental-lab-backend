from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from orders.models import Order
from products.models import Product
from operations.models import OperationStatus, Operation
from orders.serializers import ProductSerializer, ProductAndOperationsSerializer


class ProductService:
    @staticmethod
    def get_for_order(order_id: str) -> Response:
        products = Product.objects.filter(order=order_id)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    @staticmethod
    def get_products_with_operations(order_id):
        """
        View is called once during the formation of the order by the administrator.
        An operation list is generated for each item if it has not been generated previously.
        """
        order = get_object_or_404(Order, id=order_id)
        products = order.products.all()
        for product in products:
            if product.operations.count() == 0:
                for operation_type, through in zip(
                    product.product_type.operation_types.all(),
                    product.product_type.operation_types.through.objects.all(),
                ):
                    try:
                        Operation.objects.create(
                            product=product,
                            operation_type=operation_type,
                            operation_status=OperationStatus.get_default_status(),
                            ordinal_number=through.ordinal_number,
                        )
                    except:
                        pass

        serializer = ProductAndOperationsSerializer(order.products, many=True)
        return Response(serializer.data)
