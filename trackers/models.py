from django.db import models
from django.contrib.auth.models import AbstractUser
from trackers.utils.saufQL import parse_query, ast_to_django

# Create your models here.

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
    

class Issue(models.Model):
    class Priority(models.TextChoices):
        MINOR = 'MIN', 'Minor'
        MAJOR = 'MAJ', 'Major'
        CRITICAL = 'CRI', 'Critical'
        BLOCKER = 'BLO', 'Blocker'

    class Status(models.TextChoices):
        OPEN = 'OP', 'Open'
        IN_PROGRESS = 'IP', 'In Progress'
        RESOLVED = 'RES', 'Resolved'
        CLOSED = 'CLO', 'Closed'

    class Type(models.TextChoices):
        BUG = 'BUG', 'Bug'
        SRS = 'SRS', 'Software Requirements Specification'
        CRS = 'CRS', 'Customer Requirements Specification'
        TASK = 'TASK', 'Task'
        SDD = 'SDD', 'Software Design Document'
        SAD = 'SAD', 'Software Architecture Document'
        CHANGE_REQUEST = 'CHANGE_REQUEST', 'Change Request'
        DOCUMENTATION = 'DOCUMENTATION', 'Documentation'

    key = models.CharField(primary_key=True, max_length=20, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=30, choices=Type.choices)
    title = models.CharField(max_length=100)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=Priority.choices)
    status = models.CharField(max_length=10, choices=Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fix_version = models.ForeignKey(Version, on_delete=models.SET_NULL, null=True, blank=True)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_issues')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_issues')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    estimated_time = models.DurationField(null=True, blank=True)
    time_spent = models.DurationField(null=True, blank=True)
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.key:
            last_issue = Issue.objects.filter(project=self.project).order_by('-created_at').first()
            if last_issue and last_issue.key.startswith(f"{self.project.key}-"):
                try:
                    last_number = int(last_issue.key.split('-')[1])
                except (IndexError, ValueError):
                    last_number = 0
            else:
                last_number = 0
            self.key = f"{self.project.key}-{last_number + 1}"
        super().save(*args, **kwargs)

    @classmethod
    def saufQL(cls, query, *args, **kwargs):
        ast = parse_query(query)
        qs = ast_to_django(ast, cls)
        return qs

    def __str__(self):
        return self.key
    

class Worklog(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='worklogs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='worklogs')
    time_spent = models.DurationField()
    date = models.DateField()

    def __str__(self):
        return f"{self.user} - {self.issue} - {self.time_spent}"

    def save(self, *args, **kwargs):
        self.issue.refresh_from_db()
        if self.time_spent is not None:
            if self.issue.time_spent:
                self.issue.time_spent += self.time_spent
            else:
                self.issue.time_spent = self.time_spent
            self.issue.save(update_fields=['time_spent', 'updated_at'])
        super().save(*args, **kwargs)
