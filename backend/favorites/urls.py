from rest_framework.routers import SimpleRouter

from .views import FavoriteViewSet

router = SimpleRouter()
router.register("favorites", FavoriteViewSet, basename="favorite")

urlpatterns = router.urls
