from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

User = get_user_model()

from .models import Comment, Course, Lesson, Rating


class RegisterSerializer(serializers.ModelSerializer):
    """
    Foydalanuvchini ro'yxatdan o'tkazish uchun serializer.
    """
    class Meta:
        model = User
        fields = ["email", "password"]

    def create(self, validated_data):
        """
        Tasdiqlangan ma'lumotlar asosida foydalanuvchini yaratadi.
        """
        return User.objects.create_user(email=validated_data["email"], password=validated_data["password"])


class LoginSerializer(serializers.Serializer):
    """
    Foydalanuvchini tizimga kirish uchun serializer.
    """
    email = serializers.EmailField()
    password = serializers.CharField()

    def get_user(self, request):
        """
        Kirish ma'lumotlari asosida foydalanuvchini autentifikatsiya qiladi.
        """
        return authenticate(request, email=self.validated_data["email"], password=self.validated_data["password"])


class StudentSerializer(serializers.ModelSerializer):
    """
    Talabalar haqida ma'lumot qaytarish uchun serializer.
    """
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email"]


class CommentSerializer(serializers.ModelSerializer):
    """
    Izohlarni qaytarish va yaratish uchun serializer.
    """
    creator = serializers.CharField(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "lesson", "creator", "text", "created_at"]


class LessonSerializer(serializers.ModelSerializer):
    """
    Darslar haqida ma'lumot qaytarish uchun serializer.
    """
    comments = CommentSerializer(many=True, read_only=True)
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ["id", "course", "name", "video", "created_at", "comments", "rating"]

    def get_rating(self, instance: Lesson):
        """
        Dars reytingini foizda hisoblaydi.
        """
        qs = instance.ratings.all()
        return qs.filter(liked=True).count() / qs.count() * 100 if qs.count() != 0 else 0


class CourseSerializer(serializers.ModelSerializer):
    """
    Kurslar haqida ma'lumot qaytarish uchun serializer.
    """
    students = StudentSerializer(many=True, read_only=True)
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ["id", "title", "description", "students", "lessons"]


class RatingSerializer(serializers.ModelSerializer):
    """
    Reytinglarni qaytarish va yaratish uchun serializer.
    """
    creator = serializers.CharField(read_only=True)

    class Meta:
        model = Rating
        fields = ["id", "lesson", "creator", "liked"]


class StudentIdSerializer(serializers.Serializer):
    """
    Talaba ID'sini qabul qilish uchun oddiy serializer.
    """
    student_id = serializers.IntegerField()


class EmailTextSerializer(serializers.Serializer):
    """
    Email uchun mavzu va matnni qabul qilish uchun serializer.
    """
    title = serializers.CharField()
    body = serializers.CharField()
    for_admin = serializers.BooleanField(default=False)
    for_student = serializers.BooleanField(default=False)
