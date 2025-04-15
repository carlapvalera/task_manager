from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class User(AbstractUser):
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
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_archived = models.BooleanField(default=False)
    leader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='projects_led')
    members = models.ManyToManyField(User, related_name='projects')

    def __str__(self):
        return self.name

class Task(models.Model):
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
