from django.shortcuts import render, redirect

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
