from rest_framework.routers import DefaultRouter

from .views import AuthViewset, CommentViewset, CourseViewset, LessonViewset, RatingViewset

router = DefaultRouter()

router.register("auth", AuthViewset)
router.register("course", CourseViewset)
router.register("lesson", LessonViewset)
router.register("comment", CommentViewset)
router.register("rating", RatingViewset)
