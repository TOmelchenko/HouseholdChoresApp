from django.shortcuts import render

from .models import Household, Roommate


def create_household(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            household = Household.objects.create()
            roommate = Roommate.objects.create(household=household, name=name)
            request.session["household_id"] = household.id
            request.session["roommate_id"] = roommate.id
            return render(request, "chores/household_created.html", {"household": household, "roommate": roommate})
    return render(request, "chores/create_household.html")


def join_household(request):
    error = None
    if request.method == "POST":
        code = request.POST.get("code", "").strip().upper()
        name = request.POST.get("name", "").strip()
        if code and name:
            try:
                household = Household.objects.get(code=code)
            except Household.DoesNotExist:
                error = "No household found with that code."
            else:
                roommate = Roommate.objects.create(household=household, name=name)
                request.session["household_id"] = household.id
                request.session["roommate_id"] = roommate.id
                return render(request, "chores/household_joined.html", {"household": household, "roommate": roommate})
    return render(request, "chores/join_household.html", {"error": error})
