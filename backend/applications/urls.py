from rest_framework.routers import SimpleRouter

from .views import EmployerApplicationViewSet, SeekerApplicationViewSet

router = SimpleRouter()
router.register("applications", SeekerApplicationViewSet, basename="application")
router.register("employer/applications", EmployerApplicationViewSet, basename="employer-application")

urlpatterns = router.urls
