from django.conf import settings
from django.contrib.auth import get_user_model, logout
from django.core.mail import EmailMultiAlternatives
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404, redirect, resolve_url
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Comment, Course, Lesson, Rating
from .permissions import IsAdminUser, IsCourseStudent, IsCreator, IsStudent
from .serializers import CommentSerializer, CourseSerializer, EmailTextSerializer, LessonSerializer, LoginSerializer, RatingSerializer, RegisterSerializer, StudentIdSerializer, StudentSerializer

User = get_user_model()


class AuthViewset(viewsets.GenericViewSet):
    """
    AuthViewset

    Authentication bilan bog'liq amallarni boshqarish uchun javobgar. Ushbu viewset foydalanuvchilarni ro'yxatdan o'tkazish, tizimga kirish, tokenlarni yangilash va joriy foydalanuvchi ma'lumotlarini olish imkoniyatlarini ta'minlaydi.

    Methods:
        - register: Yangi foydalanuvchini ro'yxatdan o'tkazish.
        - login: Foydalanuvchini tizimga kirishini ta'minlash.
        - refresh_token: JWT tokenni yangilash.
        - whoami: Joriy foydalanuvchi ma'lumotlarini qaytaradi.
    """

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser]
    pagination_class = None
    filter_backends = []
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    @swagger_auto_schema(request_body=RegisterSerializer)
    @action(methods=["POST"], detail=False)
    def register(self, request: Request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({"message": "User created successfully", "access": access_token, "refresh": str(refresh)})

    @swagger_auto_schema(request_body=LoginSerializer)
    @action(methods=["POST"], detail=False, url_path="login")
    def login(self, request: Request, *args, **kwargs):

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.get_user(request)

        if not user:
            raise AuthenticationFailed("Login yoki parol noto'g'ri.")

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response(
            {
                "message": "Login successful",
                "access": access_token,
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.get_full_name(),
                },
            },
        )

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
    """
    CourseViewset

    Kurslar bilan bog'liq CRUD amallarni boshqaruvchi viewset. Ushbu viewset orqali kurslarni yaratish, o'chirish, yangilash va ko'rish mumkin. Shuningdek, kursga talabalarni qo'shish yoki olib tashlash imkoniyati mavjud.

    Methods:
        - add_student: Kursga talaba qo'shish.
        - remove_student: Kursdan talabani olib tashlash.
        - list: Kurslar ro'yxatini olish (keshlangan).
        - retrieve: Bitta kurs ma'lumotlarini olish (keshlangan).
    """

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    search_fields = ["title", "description"]

    def get_queryset(self):
        return super().get_queryset().filter(students=self.request.user) if not self.request.user.is_staff else super().get_queryset()

    @swagger_auto_schema(request_body=StudentIdSerializer, responses={200: CourseSerializer})
    @action(methods=["POST"], detail=True, permission_classes=[IsAdminUser], url_path="add-student", url_name="add_student", serializer_class=StudentIdSerializer)
    def add_student(self, request, pk):
        """
        Kursga talaba qo'shadi.

        Params:
        - `student_id`: Talabaning ID'si.

        Exceptions:
        - Agar talaba allaqachon kursga qo'shilgan bo'lsa, `ValidationError` qaytaradi.

        Returns:
        - Yangilangan kurs ma'lumotlarini qaytaradi.
        """
        course = self.get_object()

        user_id = request.data.get("student_id", None)
        student = get_object_or_404(User, pk=user_id)

        if student in course.students.all():
            raise ValidationError("Talaba allaqachon kursga qo'shilgan.")

        course.students.add(student)

        return Response(CourseSerializer(course).data)

    @swagger_auto_schema(request_body=StudentIdSerializer, responses={200: CourseSerializer})
    @action(methods=["POST"], detail=True, permission_classes=[IsAdminUser], url_path="remove-student", url_name="remove_student", serializer_class=StudentIdSerializer)
    def remove_student(self, request, pk):
        """
        Talabani kursdan o'chiradi.

        Params:
        - `student_id`: Talabaning ID'si.

        Exceptions:
        - Agar talaba kursga qo'shilmagan bo'lsa, `ValidationError` qaytaradi.

        Returns:
        - Yangilangan kurs ma'lumotlarini qaytaradi.
        """
        course = self.get_object()

        user_id = request.data.get("student_id", None)
        student = get_object_or_404(User, pk=user_id)

        if student not in course.students.all():
            raise ValidationError("Talaba kursga  qo'shilmagan.")

        course.students.remove(student)

        return Response(CourseSerializer(course).data)

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 5))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action in ["remove_student", "add_student"]:
            return StudentIdSerializer

        return self.serializer_class


class LessonViewset(viewsets.ModelViewSet):
    """
    LessonViewset

    Darslar bilan bog'liq CRUD amallarni boshqaruvchi viewset. Ushbu viewset orqali darslarni yaratish, yangilash, o'chirish va ko'rish mumkin. Foydalanuvchi faqat o'zi ro'yxatda bo'lgan kursning darslarini ko'rishi mumkin.

    Methods:
        - list: Darslar ro'yxatini olish (keshlangan).
        - retrieve: Bitta dars ma'lumotlarini olish (keshlangan).
    """

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated, IsCourseStudent]
    filterset_fields = ["course", "created_at"]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at", "pk"]

    def get_queryset(self):
        return super().get_queryset().filter(course__students=self.request.user) if not self.request.user.is_staff else super().get_queryset()

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 5))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class CommentViewset(viewsets.ModelViewSet):
    """
    CommentViewset

    Foydalanuvchi tomonidan yozilgan izohlarni boshqarish uchun viewset. Ushbu viewset izohlarni yaratish, yangilash, o'chirish va ko'rish imkoniyatlarini taqdim etadi. Foydalanuvchi faqat o'zi yaratgan izohlarni boshqara oladi.

    Methods:
        - list: Izohlar ro'yxatini olish (keshlangan).
        - retrieve: Bitta izoh ma'lumotlarini olish (keshlangan).
    """

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsCreator]
    search_fields = ["text"]
    filterset_fields = ["lesson", "creator"]
    ordering_fields = ["created_at"]

    def perform_create(self, serializer):
        serializer.save(creator_id=self.request.user.id)

    def perform_update(self, serializer):
        serializer.save(creator_id=self.request.user.id)

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 5))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class RatingViewset(viewsets.ModelViewSet):
    """
    RatingViewset

    Kurs yoki dars uchun reytinglar boshqaruvi. Ushbu viewset orqali foydalanuvchilar reytinglarni yaratishi, o'zgartirishi yoki o'chirishi mumkin. Foydalanuvchi faqat o'zi yaratgan reytinglarni boshqara oladi.

    Methods:
        - list: Reytinglar ro'yxatini olish (keshlangan).
        - retrieve: Bitta reyting ma'lumotlarini olish (keshlangan).
    """

    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated, IsCreator]

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 5))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(creator_id=self.request.user.id)

    def perform_update(self, serializer):
        serializer.save(creator_id=self.request.user.id)


class EmailAPIView(GenericAPIView):
    """
    EmailAPIView

    Administrator tomonidan foydalanuvchilarga xabarlarni elektron pochta orqali yuborish uchun API. Xabarlar barcha foydalanuvchilarga, faqat administratorlarga yoki faqat talabalarga yuborilishi mumkin.

    Methods:
        - post: Elektron pochta xabarlarini yuborish.
    """

    parser_classes = [FormParser, JSONParser]
    serializer_class = EmailTextSerializer
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        response = {}

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        title = serializer.validated_data.get("title")
        body = serializer.validated_data.get("body")
        for_admin = serializer.validated_data.get("for_admin", False)
        for_student = serializer.validated_data.get("for_student", False)

        users = User.objects.all()

        if for_admin and not for_student:
            users = User.objects.filter(is_staff=True)

        elif for_student and not for_admin:
            users = User.objects.filter(is_staff=False)

        for user in users:
            msg = EmailMultiAlternatives(
                subject="EduGround",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )

            context = {
                "title": title % model_to_dict(user),
                "body": body % model_to_dict(user),
            }

            msg_html = render_to_string(
                "emails/message.html",
                context=context,
            )

            msg.attach_alternative(msg_html, "text/html")

            response[user.email] = bool(msg.send(fail_silently=True))

        return Response(response)


def logout_view(request):
    """
    logout_view(request)

    Foydalanuvchini tizimdan chiqarish va ko'rsatilgan yoki standart sahifaga qayta yo'naltirish.

    Args:
        request (HttpRequest): Foydalanuvchi so'rovi.

    Returns:
        HttpResponse: Foydalanuvchini tizimdan chiqarib, qayta yo'naltirilgan javob.
    """

    next_page = request.GET.get("next", "/api/")
    logout(request)
    return redirect(next_page)
