from rest_framework import serializers


class MessageSerializer(serializers.Serializer):
    message = serializers.CharField()


class PaginationSerializer(serializers.Serializer):
    count = serializers.IntegerField(min_value=0)
    total_pages = serializers.IntegerField(min_value=0)
