from django.shortcuts import redirect
from rest_framework.decorators import api_view


@api_view(["GET"])
def index(request):
    return redirect("/admin")
