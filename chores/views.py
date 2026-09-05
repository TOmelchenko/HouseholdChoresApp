from datetime import timedelta

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Assignment, Household, Roommate


def index(request):
    household_id = request.session.get("household_id")
    roommate_id = request.session.get("roommate_id")

    if household_id is not None and roommate_id is not None:
        try:
            Household.objects.get(id=household_id)
        except Household.DoesNotExist:
            pass
        else:
            return redirect("my_chores")

    if household_id is not None or roommate_id is not None:
        request.session.pop("household_id", None)
        request.session.pop("roommate_id", None)

    return render(request, "chores/landing.html")


def my_chores(request):
    household_id = request.session.get("household_id")
    roommate_id = request.session.get("roommate_id")

    if household_id is None or roommate_id is None:
        request.session.pop("household_id", None)
        request.session.pop("roommate_id", None)
        return redirect("index")

    if not Household.objects.filter(id=household_id).exists():
        request.session.pop("household_id", None)
        request.session.pop("roommate_id", None)
        return redirect("index")

    try:
        roommate = Roommate.objects.get(id=roommate_id, household_id=household_id)
    except Roommate.DoesNotExist:
        request.session.pop("household_id", None)
        request.session.pop("roommate_id", None)
        return redirect("index")

    assignments = Assignment.objects.filter(
        roommate_id=roommate_id, completed_at__isnull=True
    ).select_related("chore").order_by("due_date")

    recently_completed = Assignment.objects.filter(
        roommate_id=roommate_id,
        completed_at__gte=timezone.now() - timedelta(minutes=5),
    ).select_related("chore").order_by("-completed_at")

    return render(
        request,
        "chores/my_chores.html",
        {
            "roommate": roommate,
            "assignments": assignments,
            "today": timezone.localdate(),
            "recently_completed": recently_completed,
        },
    )


@require_POST
def complete_chore(request, assignment_id):
    household_id = request.session.get("household_id")
    roommate_id = request.session.get("roommate_id")

    if household_id is None or roommate_id is None:
        request.session.pop("household_id", None)
        request.session.pop("roommate_id", None)
        return redirect("index")

    if not Household.objects.filter(id=household_id).exists():
        request.session.pop("household_id", None)
        request.session.pop("roommate_id", None)
        return redirect("index")

    if not Roommate.objects.filter(id=roommate_id, household_id=household_id).exists():
        request.session.pop("household_id", None)
        request.session.pop("roommate_id", None)
        return redirect("index")

    assignment = get_object_or_404(Assignment, id=assignment_id, roommate_id=roommate_id)

    if assignment.completed_at is None:
        assignment.completed_at = timezone.now()
        assignment.save(update_fields=["completed_at"])

    return redirect("my_chores")


@require_POST
def undo_chore(request, assignment_id):
    household_id = request.session.get("household_id")
    roommate_id = request.session.get("roommate_id")

    if household_id is None or roommate_id is None:
        request.session.pop("household_id", None)
        request.session.pop("roommate_id", None)
        return redirect("index")

    if not Household.objects.filter(id=household_id).exists():
        request.session.pop("household_id", None)
        request.session.pop("roommate_id", None)
        return redirect("index")

    if not Roommate.objects.filter(id=roommate_id, household_id=household_id).exists():
        request.session.pop("household_id", None)
        request.session.pop("roommate_id", None)
        return redirect("index")

    assignment = get_object_or_404(Assignment, id=assignment_id, roommate_id=roommate_id)

    if assignment.completed_at is not None and assignment.completed_at >= timezone.now() - timedelta(minutes=5):
        assignment.completed_at = None
        assignment.save(update_fields=["completed_at"])

    return redirect("my_chores")


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
                # Case-insensitive, trimmed match resumes the existing roommate instead of
                # creating a duplicate identity (see #16/#17). The household row is locked
                # for the duration of the check-then-create so two concurrent requests for
                # the same brand-new name serialize instead of racing (see #18). On SQLite
                # select_for_update() has no row-level effect, so the Roommate.name
                # case-insensitive unique constraint is the backstop that actually catches
                # a race that slips through; a loser that hits it simply resumes the
                # winner's newly-created roommate instead of surfacing an IntegrityError.
                try:
                    with transaction.atomic():
                        household = Household.objects.select_for_update().get(
                            pk=household.pk
                        )
                        existing = Roommate.objects.filter(
                            household=household, name__iexact=name
                        ).order_by("id").first()
                        if existing is not None:
                            roommate = existing
                            is_returning = True
                        else:
                            roommate = Roommate.objects.create(
                                household=household, name=name
                            )
                            is_returning = False
                except IntegrityError:
                    # Lost the race: another request committed a roommate with the same
                    # case-insensitive name for this household first. Resume it.
                    roommate = Roommate.objects.filter(
                        household=household, name__iexact=name
                    ).order_by("id").first()
                    is_returning = True
                request.session["household_id"] = household.id
                request.session["roommate_id"] = roommate.id
                return render(
                    request,
                    "chores/household_joined.html",
                    {"household": household, "roommate": roommate, "is_returning": is_returning},
                )
    return render(request, "chores/join_household.html", {"error": error})
