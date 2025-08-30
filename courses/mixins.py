from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden

class TeacherRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.groups.filter(name="Teacher").exists():
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

class StudentRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.groups.filter(name="Student").exists():
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)
