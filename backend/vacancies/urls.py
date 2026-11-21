from rest_framework.routers import SimpleRouter

from .views import MyVacancyViewSet, VacancyViewSet

router = SimpleRouter()
# vacancies/my регистрируется раньше vacancies, чтобы "my" не принимался за id вакансии
router.register("vacancies/my", MyVacancyViewSet, basename="my-vacancy")
router.register("vacancies", VacancyViewSet, basename="vacancy")

urlpatterns = router.urls
