from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAdminUser


class IsCreator(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.creator or bool(request.user and request.user.is_staff)


class IsCourseStudent(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user in obj.course.students.all() or bool(request.user and request.user.is_staff)


class IsStudent(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user in obj.students.all() or bool(request.user and request.user.is_staff)
