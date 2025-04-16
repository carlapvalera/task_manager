from rest_framework import generics, permissions
from .models import Project, Task
from .serializers import ProjectSerializer, TaskSerializer
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import User, Project, Task  # Asegúrate de importar User desde tu modelo personalizado si existe
from .serializers import ProjectSerializer, TaskSerializer

class IsProjectLeader(permissions.BasePermission):
    """
    Permission class to check if the requesting user is the leader of the project.

    Methods:
        has_object_permission(request, view, obj):
            Determines if the user making the request is the leader of the project
            associated with the object.

            Args:
                request: The HTTP request object.
                view: The view that is being accessed.
                obj: The object being accessed.

            Returns:
                bool: True if the user is the leader of the project, False otherwise.
    """
    def has_object_permission(self, request, view, obj):
        return obj.leader == request.user

class IsTaskOwnerOrProjectLeader(permissions.BasePermission):
    """
    Custom permission class to check if the user has the required permissions
    to access or modify a task object.

    Permissions:
    - Any user can view tasks (GET requests are always allowed).
    - Only the user assigned to the task or the leader of the project 
      associated with the task can edit or delete it.

    Methods:
    - has_object_permission(request, view, obj):
        Determines if the requesting user has the appropriate permissions
        based on the HTTP method and their relationship to the task or project.

    Args:
        request: The HTTP request object.
        view: The view being accessed.
        obj: The task object being accessed.

    Returns:
        bool: True if the user has the required permissions, False otherwise.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET']:
            return True  # Cualquiera puede ver las tareas
        elif request.user == obj.assigned_to or request.user == obj.project.leader:
            return True  # Solo el asignado o el líder pueden editar/eliminar
        return False

class ProjectList(generics.ListCreateAPIView):
    """
    API view for listing and creating Project instances.

    This view provides the following functionalities:
    - List all existing Project instances.
    - Create a new Project instance.

    Attributes:
        queryset (QuerySet): The queryset containing all Project instances.
        serializer_class (Serializer): The serializer class used for Project instances.
        permission_classes (list): A list of permission classes that restrict access to authenticated users only.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, or deleting a specific project.

    This view allows authenticated users with the appropriate permissions 
    to perform the following actions on a project:
    - Retrieve the details of a specific project.
    - Update the details of a specific project.
    - Delete a specific project.

    Attributes:
        queryset (QuerySet): The set of Project objects to retrieve, update, or delete.
        serializer_class (Serializer): The serializer class used to validate and 
            serialize the Project data.
        permission_classes (list): A list of permission classes that determine 
            whether the user has access to this view. Requires the user to be 
            authenticated and to have the `IsProjectLeader` permission.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectLeader]

class TaskList(generics.ListCreateAPIView):
    """
    TaskList is a view that handles listing and creating tasks for a specific project.
    Methods:
        get_queryset(self):
            Retrieves the queryset of tasks filtered by the project ID provided in the URL.
            Returns:
                QuerySet: A queryset of Task objects associated with the specified project.
        perform_create(self, serializer):
            Handles the creation of a new task. Ensures that:
                - Tasks cannot be created in archived projects.
                - The assigned user is either a member of the project or the project leader.
            Parameters:
                serializer (Serializer): The serializer instance used to save the task.
            Raises:
                Exception: If the project is archived or the assigned user is not a valid member.
    """
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
    """
    API view for retrieving, updating, or deleting a specific task.

    This view allows authenticated users to perform the following actions on a task:
    - Retrieve the details of a specific task.
    - Update the details of a specific task.
    - Delete a specific task.

    Permissions:
    - The user must be authenticated.
    - The user must either be the owner of the task or a project leader.

    Attributes:
    - queryset: The set of Task objects to retrieve from the database.
    - serializer_class: The serializer used to convert Task objects to and from JSON.
    - permission_classes: A list of permission classes that determine access to this view.
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskOwnerOrProjectLeader]

class RemoveLeaderView(APIView):
    """
    API view to handle the removal and reassignment of a project leader.
    Methods:
        post(request, project_id):
            Handles the POST request to remove the current leader of a project
            and optionally reassign the leadership to another member.
    POST Parameters:
        - reassign_option (str): The option for reassigning leadership. 
          Can be 'automatic' or 'manual'.
        - new_leader_id (int, optional): The ID of the new leader if 
          'manual' option is selected.
    Args:
        request (Request): The HTTP request object containing user and data.
        project_id (int): The ID of the project whose leader is to be removed.
    Returns:
        Response:
            - 200 OK: If the leadership is successfully reassigned.
            - 400 Bad Request: If the reassignment option is invalid or 
              there are no members to reassign leadership.
            - 403 Forbidden: If the user making the request is not the current leader.
    Behavior:
        - If the `reassign_option` is 'automatic', the leadership is reassigned
          to the first member of the project.
        - If the `reassign_option` is 'manual', the leadership is reassigned
          to the user specified by `new_leader_id`.
        - Tasks assigned to the current leader are transferred to the new leader.
    """
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
    """
    API view to handle the removal of a user from a project.
    Methods:
        post(request, project_id, user_id):
            Removes a user from the specified project. If the user has tasks
            assigned within the project, those tasks are reassigned to another
            member of the project or the project leader.
    Args:
        request (Request): The HTTP request object.
        project_id (int): The ID of the project from which the user will be removed.
        user_id (int): The ID of the user to be removed.
    Returns:
        Response: A JSON response with a success message and HTTP 200 status if the
                  user is successfully removed, or an error message with HTTP 400
                  status if the user is not a member of the project.
    """
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
    """
    API view to handle user registration.

    Methods:
        post(request):
            Handles POST requests to register a new user. Validates the input
            data using the RegisterUserSerializer. If the data is valid, the
            user is saved and a success response is returned. Otherwise, an
            error response with validation details is returned.

    Responses:
        201 Created:
            - Message: "Usuario registrado exitosamente"
            - Description: Returned when the user is successfully registered.
        400 Bad Request:
            - Errors: Validation errors from the serializer.
            - Description: Returned when the input data is invalid.
    """
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Usuario registrado exitosamente"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
