from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """
    Foydalanuvchilarni boshqarish uchun maxsus manager.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Oddiy foydalanuvchi yaratadi.
        """
        if not email:
            raise ValueError("Email majburiy maydon.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Superuser (admin) yaratadi.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser uchun is_staff=True bo'lishi kerak.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser uchun is_superuser=True bo'lishi kerak.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Maxsus foydalanuvchi modeli, unda username o'rniga email ishlatiladi.
    """
    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"  # Kirish uchun email ishlatiladi
    REQUIRED_FIELDS = []  # Paroldan boshqa majburiy maydon yo'q

    objects = UserManager()

    def __str__(self):
        """
        Foydalanuvchining emailini qaytaradi.
        """
        return self.email

    @classmethod
    def get_user(cls, email, password):
        """
        Email va parol yordamida foydalanuvchini topadi.
        """
        try:
            user = cls.objects.get(email=email)
            if user.check_password(password):
                return user
        except cls.DoesNotExist:
            return None


class Course(models.Model):
    """
    Kurslar modeli.
    """
    title = models.CharField(max_length=255)
    description = models.TextField()
    students = models.ManyToManyField(User, blank=True)

    def __str__(self):
        """
        Kurs nomini qaytaradi.
        """
        return self.title


class Lesson(models.Model):
    """
    Kursdagi darslar modeli.
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    name = models.CharField(max_length=256)
    video = models.FileField(upload_to="videos/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        Dars nomini qaytaradi.
        """
        return self.name


class Comment(models.Model):
    """
    Darslarga izohlar modeli.
    """
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="comments")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        Izohni yaratgan foydalanuvchi to'liq ismini qaytaradi.
        """
        return self.creator.get_full_name()


class Rating(models.Model):
    """
    Darslarga baholar modeli.
    """
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="ratings")
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    liked = models.BooleanField()

    def __str__(self):
        """
        Foydalanuvchi va baho holatini qaytaradi.
        """
        return f"{self.creator.get_full_name()} {'yoqdi' if self.liked else 'yoqmadi'}"
