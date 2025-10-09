from django.contrib.auth.backends import ModelBackend
from student.models import Student  # adjust import to where Student lives

class ClassScopedBackend(ModelBackend):
    def authenticate(self, request, code=None, username=None, password=None, **kwargs):
        if not (code and username and password):
            return None

        # normalize if you want case-insensitive usernames:
        code = code.strip()
        username = username.strip()

        try:
            student = (Student.objects.get(code=code, username=username))
        except Student.DoesNotExist:
            return None

        user = student.user
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None