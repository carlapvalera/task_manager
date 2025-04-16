from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class User(AbstractUser):
    """
    User model extending AbstractUser.

    Attributes:
        groups (ManyToManyField): A many-to-many relationship to the Group model.
            - `related_name='custom_user_set'`: Custom related name to avoid conflicts.
            - `blank=True`: Field is optional.
            - `help_text`: Description of the groups this user belongs to.
            - `verbose_name='groups'`: Human-readable name for the field.
            - `related_query_name='user'`: Name to use for reverse queries.

        user_permissions (ManyToManyField): A many-to-many relationship to the Permission model.
            - `related_name='custom_user_set'`: Custom related name to avoid conflicts.
            - `blank=True`: Field is optional.
            - `help_text`: Description of specific permissions for this user.
            - `verbose_name='user permissions'`: Human-readable name for the field.
            - `related_query_name='user'`: Name to use for reverse queries.
    """
    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',  # Cambia el related_name para evitar conflicto
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_set',  # Cambia el related_name para evitar conflicto
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
        related_query_name='user',
    )


class Project(models.Model):
    """
    Represents a project within the task management system.
    Attributes:
        name (str): The name of the project, limited to 100 characters.
        description (str): A detailed description of the project.
        is_archived (bool): Indicates whether the project is archived. Defaults to False.
        leader (User): The user who leads the project. Can be null if no leader is assigned.
        members (QuerySet[User]): A many-to-many relationship representing the users who are members of the project.
    Methods:
        __str__(): Returns the name of the project as its string representation.
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_archived = models.BooleanField(default=False)
    leader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='projects_led')
    members = models.ManyToManyField(User, related_name='projects')

    def __str__(self):
        return self.name

class Task(models.Model):
    """
    Task model represents a task within a project management system.
    Attributes:
        STATUS_CHOICES (list of tuple): Defines the possible statuses for a task:
            - 'pending': Task is pending.
            - 'in_progress': Task is in progress.
            - 'completed': Task is completed.
        PRIORITY_CHOICES (list of tuple): Defines the possible priority levels for a task:
            - 'low': Low priority.
            - 'medium': Medium priority.
            - 'high': High priority.
        name (CharField): The name of the task, with a maximum length of 200 characters.
        status (CharField): The current status of the task, chosen from STATUS_CHOICES. Defaults to 'pending'.
        priority (CharField): The priority level of the task, chosen from PRIORITY_CHOICES. Defaults to 'medium'.
        project (ForeignKey): A reference to the associated Project. Deleting the project will delete its tasks.
        assigned_to (ForeignKey): A reference to the User assigned to the task. Can be null, and defaults to None. If the user is deleted, the field is set to null.
    Methods:
        __str__(): Returns the name of the task as its string representation.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada')
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta')
    ]

    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, default=None)

    def __str__(self):
        return self.name

@receiver(pre_delete, sender=User)
def transfer_leadership(sender, instance, **kwargs):
    projects_led = instance.projects_led.all()
    
    for project in projects_led:
        # Reasignar el liderazgo a otro miembro del proyecto
        new_leader = project.members.first()  # Selecciona al primer miembro como nuevo líder
        
        if new_leader:
            project.leader = new_leader
            project.save()
            
            # Transferir tareas del líder eliminado al nuevo líder
            tasks = Task.objects.filter(project=project, assigned_to=instance)
            tasks.update(assigned_to=new_leader)

@receiver(pre_delete, sender=User)
def transfer_tasks_to_leader(sender, instance, **kwargs):
    tasks = Task.objects.filter(assigned_to=instance)
    
    for task in tasks:
        project = task.project
        
        if instance != project.leader:  # Evita transferir si el usuario es el líder
            task.assigned_to = project.leader
            task.save()
