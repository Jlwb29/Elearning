from django import forms
from .models import Course, CourseFeedback,CourseMaterial

class DateInput(forms.DateInput):
    input_type = "date" 

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["title", "description", "start_date", "end_date", "capacity"]
        widgets = {
            "start_date": DateInput(),
            "end_date": DateInput(),
        }

class MultiEnrollForm(forms.Form):
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Select courses to enroll"
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Course.objects.all()
        if user is not None and getattr(user, "is_authenticated", False):
            from .models import Enrollment
            qs = qs.exclude(enrollments__user=user, enrollments__role="STUDENT").distinct()
            try:
                from .models import CourseBlock
                qs = qs.exclude(blocks__user=user)
            except Exception:
                pass
        self.fields["courses"].queryset = qs.order_by("title")

class CourseFeedbackForm(forms.ModelForm):
    class Meta:
        model = CourseFeedback
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5}),
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "What did you think of this course?"}),
        }
        labels = {"rating": "Rating (1-5)", "comment": "Comment (optional)"}

class CourseMaterialForm(forms.ModelForm):
    class Meta:
        model = CourseMaterial
        fields = ["title", "description", "file", "url"]