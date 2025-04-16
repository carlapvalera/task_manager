from rest_framework import serializers
from .models import Project, Task, User

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.

    This serializer is used to convert User model instances into JSON format
    and vice versa. It includes the following fields:
    - id: The unique identifier of the user.
    - username: The username of the user.
    - first_name: The first name of the user.
    - last_name: The last name of the user.
    - email: The email address of the user.
    - is_active: A boolean indicating whether the user account is active.
    - date_joined: The date and time when the user account was created.
    """
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active',
            'date_joined'
        ]

class RegisterUserSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a new user.
    This serializer is used to validate and create a new user instance. It includes
    fields for the user's username, first name, last name, email, and password. The
    password field is write-only for security purposes.
    Methods:
        create(validated_data):
            Creates and returns a new user instance with the provided validated data.
            The password is hashed before saving the user.
    Meta:
        model: User
            The model associated with this serializer.
        fields: list
            The fields to include in the serialized representation.
        extra_kwargs: dict
            Additional keyword arguments for specific fields (e.g., making the password write-only).
    """
    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'password'
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user



class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for the Project model.
    This serializer is used to convert Project model instances into JSON format
    and vice versa. It includes the following fields:
    - `id`: The unique identifier of the project.
    - `name`: The name of the project.
    - `description`: A brief description of the project.
    - `is_archived`: A boolean indicating whether the project is archived.
    - `leader`: A read-only nested representation of the project's leader using the UserSerializer.
    - `members`: A read-only nested representation of the project's members using the UserSerializer.
    Attributes:
        leader (UserSerializer): A nested serializer for the leader of the project.
        members (UserSerializer): A nested serializer for the members of the project.
    Meta:
        model (Project): The model that this serializer is based on.
        fields (list): The fields to include in the serialized representation.
    """
    leader = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'is_archived', 'leader', 'members']

class TaskSerializer(serializers.ModelSerializer):
    """
    TaskSerializer is a serializer for the Task model. It serializes the fields
    of the Task model and includes related fields for project and assigned_to.
    Attributes:
        project (StringRelatedField): A read-only field that represents the related
            project as a string.
        assigned_to (UserSerializer): A read-only nested serializer for the user
            assigned to the task.
    Meta:
        model (Task): The model that this serializer is based on.
        fields (list): The list of fields to include in the serialized output,
            which are 'id', 'name', 'status', 'priority', 'project', and 'assigned_to'.
    """
    project = serializers.StringRelatedField(read_only=True)
    assigned_to = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'name', 'status', 'priority', 'project', 'assigned_to']
