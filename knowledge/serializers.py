from rest_framework import serializers

OPERATION_TYPES = ("Модели", "CAD/CAM", "Керамика", "Протезирование")


class KnowledgeAskRequestSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=500, trim_whitespace=True)
    operation_type = serializers.ChoiceField(choices=OPERATION_TYPES, required=False, allow_null=True)


class KnowledgeSourceSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    document_path = serializers.CharField()
    document_title = serializers.CharField()
    doc_type = serializers.CharField()
    operation_type = serializers.CharField()
    fragment = serializers.CharField()
    distance = serializers.FloatField()
    cited = serializers.BooleanField()


class KnowledgeAskResponseSerializer(serializers.Serializer):
    answered = serializers.BooleanField()
    answer = serializers.CharField()
    sources = KnowledgeSourceSerializer(many=True)
