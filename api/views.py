from rest_framework import generics, permissions
from .models import Project, Task
from .serializers import ProjectSerializer, TaskSerializer
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import User, Project, Task  # Asegúrate de importar User desde tu modelo personalizado si existe
from .serializers import ProjectSerializer, TaskSerializer

class IsProjectLeader(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.leader == request.user

class IsTaskOwnerOrProjectLeader(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET']:
            return True  # Cualquiera puede ver las tareas
        elif request.user == obj.assigned_to or request.user == obj.project.leader:
            return True  # Solo el asignado o el líder pueden editar/eliminar
        return False

class ProjectList(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectLeader]

class TaskList(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        return Task.objects.filter(project_id=project_id)

    def perform_create(self, serializer):
        project_id = self.kwargs.get('project_id')
        project = Project.objects.get(id=project_id)
        
        if project.is_archived:
            raise Exception("No se pueden crear tareas en proyectos archivados")
        
        assigned_to_id = self.request.data.get('assigned_to')
        assigned_to = User.objects.get(id=assigned_to_id)
        
        if assigned_to not in project.members.all() and assigned_to != project.leader:
            raise Exception("El usuario asignado no es miembro del proyecto")
        
        serializer.save(project=project, assigned_to=assigned_to)

class TaskDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskOwnerOrProjectLeader]

class RemoveLeaderView(APIView):
    def post(self, request, project_id):
        project = Project.objects.get(id=project_id)
        
        # Verificar si el líder actual es el usuario que realiza la acción
        if project.leader != request.user:
            return Response({"error": "Solo el líder actual puede ser reemplazado"}, status=status.HTTP_403_FORBIDDEN)
        
        # Obtener la opción de reasignación del liderazgo
        reassign_option = request.data.get('reassign_option')
        
        if reassign_option == 'automatic':
            # Reasignar el liderazgo automáticamente al primer miembro del proyecto
            new_leader = project.members.first()
            
            if new_leader:
                project.leader = new_leader
                project.save()
                
                # Transferir tareas del líder anterior al nuevo líder
                tasks = Task.objects.filter(project=project, assigned_to=request.user)
                tasks.update(assigned_to=new_leader)
                
                return Response({"message": "Liderazgo transferido automáticamente"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "No hay otros miembros en el proyecto para reasignar el liderazgo"}, status=status.HTTP_400_BAD_REQUEST)
        
        elif reassign_option == 'manual':
            # Obtener el ID del nuevo líder seleccionado manualmente
            new_leader_id = request.data.get('new_leader_id')
            new_leader = User.objects.get(id=new_leader_id)
            
            # Verificar si el nuevo líder es miembro del proyecto
            if new_leader in project.members.all():
                project.leader = new_leader
                project.save()
                
                # Transferir tareas del líder anterior al nuevo líder
                tasks = Task.objects.filter(project=project, assigned_to=request.user)
                tasks.update(assigned_to=new_leader)
                
                return Response({"message": "Liderazgo transferido manualmente"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "El usuario seleccionado no es miembro del proyecto"}, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            return Response({"error": "Opción de reasignación inválida"}, status=status.HTTP_400_BAD_REQUEST)

class RemoveUserFromProjectView(APIView):
    def post(self, request, project_id, user_id):
        project = Project.objects.get(id=project_id)
        user = User.objects.get(id=user_id)
        
        if user in project.members.all():
            project.members.remove(user)
            
            # Transferir tareas del usuario a otro miembro o al líder
            tasks = Task.objects.filter(project=project, assigned_to=user)
            if tasks.exists():
                new_assignee = project.members.first() or project.leader
                tasks.update(assigned_to=new_assignee)
            
            return Response({"message": "Usuario removido del proyecto"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "El usuario no es miembro del proyecto"}, status=status.HTTP_400_BAD_REQUEST)



from django.http import HttpResponse

def home_view(request):
    return HttpResponse("Bienvenido a Task Manager")


from .models import User
from .serializers import RegisterUserSerializer

class RegisterUserView(APIView):
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Usuario registrado exitosamente"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
