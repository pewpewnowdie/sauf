from django.db import models
from django.contrib.auth.models import AbstractUser
from trackers.utils.saufQL import parse_query, ast_to_django
from django.db import transaction


class User(AbstractUser):
    pass


class Project(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = 'NS', 'Not Started'
        IN_PROGRESS = 'IP', 'In Progress'
        COMPLETED = 'C', 'Completed'

    key = models.CharField(primary_key=True, max_length=16)
    name = models.CharField(max_length=30)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    issue_types = models.ManyToManyField("IssueType", related_name="projects")

    @classmethod
    def saufQL(cls, query, *args, **kwargs):
        ast = parse_query(query)
        qs = ast_to_django(ast, cls)
        return qs

    def __str__(self):
        return self.name
    

class Version(models.Model):
    key = models.CharField(primary_key=True, max_length=16)
    description = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='versions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.key:
            self.key = self.project.key + "-v" + self.key
        super().save(*args, **kwargs)

    def __str__(self):
        return self.key


class User_Project(models.Model):
    class Role(models.TextChoices):
        DEVELOPER = 'DEV', 'Developer'
        MANAGER = 'MGR', 'Manager'
        QA = 'QA', 'Quality Assurance'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_projects')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_assignees')
    role = models.CharField(max_length=30, choices=Role.choices)

    class Meta:
        unique_together = ('user', 'project')


class Sprint(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = 'NS', 'Not Started'
        IN_PROGRESS = 'IP', 'In Progress'
        COMPLETED = 'C', 'Completed'

    key = models.CharField(primary_key=True, max_length=16)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices)

    def save(self, *args, **kwargs):
        if self.key:
            self.key = self.project.key + "-s" + self.key
        super().save(*args, **kwargs)

    def __str__(self):
        return self.key
    

class IssueType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class IssueField(models.Model):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    ENUM = "enum"

    FIELD_TYPES = [
        (TEXT, "Text"),
        (NUMBER, "Number"),
        (DATE, "Date"),
        (BOOLEAN, "Boolean"),
        (ENUM, "Enum"),
    ]

    issue_type = models.ForeignKey(IssueType, on_delete=models.CASCADE, related_name="fields")
    name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=50, choices=FIELD_TYPES)
    is_required = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.issue_type.name} - {self.name}"


class Issue(models.Model):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"

    STATUS_CHOICES = [
        (OPEN, "Open"),
        (IN_PROGRESS, "In Progress"),
        (CLOSED, "Closed"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="issues")
    issue_type = models.ForeignKey(IssueType, on_delete=models.PROTECT, related_name="issues")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    
    fix_versions = models.ManyToManyField("Version", blank=True, related_name="fixed_issues")
    occured_version = models.ForeignKey("Version", null=True, blank=True, on_delete=models.SET_NULL, related_name="bugs_occured")
    sprint = models.ForeignKey("Sprint", null=True, blank=True, on_delete=models.SET_NULL, related_name="issues")


    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="reported_issues")
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_issues")

    def __str__(self):
        return f"[{self.project.name}] {self.title}"


class IssueFieldValue(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="field_values")
    field = models.ForeignKey(IssueField, on_delete=models.CASCADE, related_name="values")

    value_text = models.TextField(null=True, blank=True)
    value_number = models.DecimalField(max_digits=20, decimal_places=5, null=True, blank=True)
    value_date = models.DateTimeField(null=True, blank=True)
    value_boolean = models.BooleanField(null=True, blank=True)

    class Meta:
        unique_together = ("issue", "field")

    def __str__(self):
        return f"{self.issue.title} - {self.field.name}"


class Worklog(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='worklogs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='worklogs')
    time_spent = models.DurationField()
    date = models.DateField()

    def __str__(self):
        return f"{self.user} - {self.issue} - {self.time_spent}"

    def save(self, *args, **kwargs):
      with transaction.atomic():
          issue = Issue.objects.select_for_update().get(pk=self.issue.pk)
          super().save(*args, **kwargs)
          if self.time_spent:
              if issue.time_spent:
                  issue.time_spent += self.time_spent
              else:
                  issue.time_spent = self.time_spent
              issue.save(update_fields=['time_spent', 'updated_at'])
