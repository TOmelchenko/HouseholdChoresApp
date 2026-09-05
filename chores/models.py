import uuid

from django.db import models


class Household(models.Model):
    code = models.CharField(max_length=8, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code


class Roommate(models.Model):
    household = models.ForeignKey(
        Household, on_delete=models.CASCADE, related_name="roommates"
    )
    # Uniqueness within a household is enforced at the application layer (case-insensitive,
    # trimmed matching in join_household), deliberately with no DB-level constraint — see #17/#18.
    name = models.CharField(max_length=100)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Chore(models.Model):
    name = models.CharField(max_length=200)
    frequency_days = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class Assignment(models.Model):
    chore = models.ForeignKey(
        Chore, on_delete=models.CASCADE, related_name="assignments"
    )
    roommate = models.ForeignKey(
        Roommate, on_delete=models.CASCADE, related_name="assignments"
    )
    due_date = models.DateField()
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.chore} → {self.roommate} (due {self.due_date})"
