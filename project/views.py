from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Comment, Course, Lesson, Rating
from .permissions import IsAdminUser, IsCourseStudent, IsCreator, IsStudent
from .serializers import CommentSerializer, CourseSerializer, LessonSerializer, RatingSerializer, RegisterSerializer, StudentIdSerializer, StudentSerializer

User = get_user_model()


class AuthViewset(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @action(methods=["POST"], detail=False)
    def register(self, request: Request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({"message": "User created successfully", "access": access_token, "refresh": str(refresh)})

    @action(methods=["POST"], detail=False, url_path="login")
    def login(self, request: Request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            raise ValidationError("Email va parolni to'ldiring.")

        user = authenticate(request, email=email, password=password)

        if not user:
            raise AuthenticationFailed("Login yoki parol noto'g'ri.")

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({"message": "Login successful", "access": access_token, "refresh": str(refresh), "user": {"id": user.id, "email": user.email, "full_name": user.get_full_name()}})

    @action(methods=["POST"], detail=False, url_path="refresh")
    def refresh_token(self, request: Request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            raise ValidationError("Refresh tokenni yuborish shart.")

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            return Response({"message": "Token yangilandi", "access": access_token, "refresh": str(refresh)})
        except Exception as e:
            raise AuthenticationFailed("Refresh token noto'g'ri yoki muddati o'tgan.")

    @swagger_auto_schema(request_body=None, responses={200: StudentSerializer})
    @action(methods=["GET"], detail=False, permission_classes=[permissions.IsAuthenticated])
    def whoami(self, request):
        return Response(StudentSerializer(request.user, context={"request": request}).data)


class CourseViewset(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):

        if self.request.user.is_staff:
            return super().get_queryset()

        return super().get_queryset().filter(students=self.request.user)

    @swagger_auto_schema(request_body=StudentIdSerializer, responses={200: CourseSerializer})
    @action(methods=["POST"], detail=True, permission_classes=[IsAdminUser], url_path="add-student", url_name="add_student")
    def add_student(self, request, pk):
        course = self.get_object()

        user_id = request.data.get("student_id", None)
        student = get_object_or_404(User, pk=user_id)

        if student in course.students.all():
            raise ValidationError("Talaba allaqachon kursga qo'shilgan.")

        course.students.add(student)

        return Response(self.get_serializer(course).data)

    @swagger_auto_schema(request_body=StudentIdSerializer, responses={200: CourseSerializer})
    @action(methods=["POST"], detail=True, permission_classes=[IsAdminUser], url_path="remove-student", url_name="remove_student")
    def remove_student(self, request, pk):
        course = self.get_object()

        user_id = request.data.get("student_id", None)
        student = get_object_or_404(User, pk=user_id)

        if student not in course.students.all():
            raise ValidationError("Talaba kursga  qo'shilmagan.")

        course.students.remove(student)

        return Response(self.get_serializer(course).data)


class LessonViewset(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsCourseStudent]

    def get_queryset(self):
        return super().get_queryset().filter(course__students=self.request.user)


class CommentViewset(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsCreator]

    def perform_create(self, serializer):
        serializer.save(creator_id=self.request.user.id)

    def perform_update(self, serializer):
        serializer.save(creator_id=self.request.user.id)


class RatingViewset(viewsets.ModelViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [IsCreator]

    # def get_queryset(self):
    #     return super().get_queryset().filter(creator=self.request.user)

    def perform_create(self, serializer):
        serializer.save(creator_id=self.request.user.id)

    def perform_update(self, serializer):
        serializer.save(creator_id=self.request.user.id)
