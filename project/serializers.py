from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

from .models import Comment, Course, Lesson, Rating


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "password"]

    def create(self, validated_data):
        return User.objects.create_user(email=validated_data["email"], password=validated_data["password"])


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email"]


class CommentSerializer(serializers.ModelSerializer):
    creator = serializers.CharField(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "lesson", "creator", "text", "created_at"]


class LessonSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ["id", "course", "name", "video", "created_at", "comments", "rating"]

    def get_rating(self, instance: Lesson):
        qs = instance.ratings.all()
        return qs.filter(liked=True).count() / qs.count() * 100 if qs.count() != 0 else 0


class CourseSerializer(serializers.ModelSerializer):
    students = StudentSerializer(many=True, read_only=True)
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ["id", "title", "description", "students", "lessons"]


class RatingSerializer(serializers.ModelSerializer):
    creator = serializers.CharField(read_only=True)

    class Meta:
        model = Rating
        fields = ["id", "lesson", "creator", "liked"]


class StudentIdSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()


class EmailTextSerializer(serializers.Serializer):
    title = serializers.CharField()
    body = serializers.CharField()
    for_admin = serializers.BooleanField(default=False)
    for_student = serializers.BooleanField(default=False)