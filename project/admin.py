from django.contrib import admin
from django.utils.html import format_html

from .models import Comment, Course, Lesson, Rating, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["pk", "get_full_name", "email", "is_staff", "is_superuser"]
    list_display_links = ["pk", "get_full_name"]
    search_fields = ["email", "first_name", "last_name"]
    list_per_page = 10
    list_filter = ["is_staff", "is_superuser", "date_joined"]
    ordering = ["date_joined"]

    fieldsets = (
        ("Foydalanuvchi ma'lumotlari", {"fields": ("email", "first_name", "last_name")}),
        ("Ruxsatlar", {"fields": ("is_staff", "is_superuser", "is_active")}),
        ("Parol", {"fields": ("password",)}),
    )
    readonly_fields = ["last_login", "date_joined"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["pk", "title", "description", "get_students"]
    search_fields = ["title", "description"]
    list_filter = ["students"]
    list_per_page = 10
    list_display_links = ["title"]

    def get_students(self, obj):
        return ", ".join([student.email for student in obj.students.all()])

    get_students.short_description = "Foydalanuvchilar"


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "course", "created_at", "view_video"]
    search_fields = ["name", "course__title"]
    list_filter = ["course", "created_at"]
    list_display_links = ["name"]

    def view_video(self, obj):
        if obj.video:
            return format_html(f'<a href="{obj.video.url}" target="_blank">Videoni ko\'rish</a>')
        return "Video mavjud emas"

    view_video.allow_tags = True
    view_video.short_description = "Video"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["pk", "creator", "lesson", "short_text", "created_at"]
    search_fields = ["creator__email", "text", "lesson__name"]
    list_filter = ["lesson", "created_at"]

    def short_text(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

    short_text.short_description = "Izoh"


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ["pk", "lesson", "creator", "liked"]
    search_fields = ["lesson__name", "creator__email"]
    list_filter = ["liked", "lesson"]
