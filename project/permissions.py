from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsCreator(BasePermission):
    """
    Ob'ektni faqat yaratuvchisi yoki admin foydalanuvchi ko'rish/modify qilishga ruxsat oladi.
    """
    def has_object_permission(self, request, view, obj):
        """
        Ob'ektga ruxsatni tekshiradi:
        - Agar foydalanuvchi ob'ekt yaratuvchisi bo'lsa yoki admin bo'lsa, True qaytaradi.
        """
        return request.user == obj.creator or bool(request.user and request.user.is_staff)


class IsCourseStudent(BasePermission):
    """
    Ob'ekt faqat kurs talabasi yoki admin foydalanuvchi uchun ko'rinadi.
    """
    def has_object_permission(self, request, view, obj):
        """
        Ob'ektga ruxsatni tekshiradi:
        - Agar foydalanuvchi kurs talabasi bo'lsa yoki admin bo'lsa, True qaytaradi.
        """
        return request.user in obj.course.students.all() or bool(request.user and request.user.is_staff)


class IsStudent(BasePermission):
    """
    Ob'ekt faqat talaba yoki admin foydalanuvchi uchun ko'rinadi.
    """
    def has_object_permission(self, request, view, obj):
        """
        Ob'ektga ruxsatni tekshiradi:
        - Agar foydalanuvchi talaba ro'yxatida bo'lsa yoki admin bo'lsa, True qaytaradi.
        """
        return request.user in obj.students.all() or bool(request.user and request.user.is_staff)
