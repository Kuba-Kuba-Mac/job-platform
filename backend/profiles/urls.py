from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import MyProfileView, MyProjectViewSet, SeekerProfileDetailView

router = SimpleRouter()
router.register("profiles/me/projects", MyProjectViewSet, basename="my-project")

urlpatterns = [
    path("profiles/me/", MyProfileView.as_view(), name="profile-me"),
    path("profiles/<int:user_id>/", SeekerProfileDetailView.as_view(), name="profile-detail"),
    *router.urls,
]
