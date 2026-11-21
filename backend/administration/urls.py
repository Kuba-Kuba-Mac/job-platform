from rest_framework.routers import SimpleRouter

from .views import AdminUserViewSet, CompanyModerationViewSet, VacancyModerationViewSet

router = SimpleRouter()
router.register("admin/users", AdminUserViewSet, basename="admin-user")
router.register("admin/moderation/vacancies", VacancyModerationViewSet, basename="moderation-vacancy")
router.register("admin/moderation/companies", CompanyModerationViewSet, basename="moderation-company")

urlpatterns = router.urls
