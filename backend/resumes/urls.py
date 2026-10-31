from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ResumeViewSet, SkillListView

router = DefaultRouter()
router.register("resumes", ResumeViewSet, basename="resume")

urlpatterns = [
    path("skills/", SkillListView.as_view(), name="skill-list"),
    *router.urls,
]
