from rest_framework.routers import SimpleRouter

from .views import SeekerApplicationViewSet

router = SimpleRouter()
router.register("applications", SeekerApplicationViewSet, basename="application")

urlpatterns = router.urls
