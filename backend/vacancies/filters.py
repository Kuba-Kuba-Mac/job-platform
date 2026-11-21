"""S-02: фильтры поиска вакансий. Все параметры приходят из строки запроса и попадают в URL страницы."""

from django.db.models import Exists, F, OuterRef, Q
from django.db.models.functions import Coalesce
from rest_framework.exceptions import ValidationError

from resumes.models import Skill

from .models import EmploymentType, Experience, Schedule, Vacancy

MULTI_FILTERS = {
    "experience": Experience.values,
    "employment_type": EmploymentType.values,
    "schedule": Schedule.values,
}
ORDERINGS = {
    "new": ["-created_at", "-id"],
    "salary": [F("salary_max").desc(nulls_last=True), "-created_at"],
}


def _choices(name, raw, allowed):
    values = [v for v in (x.strip() for x in raw.split(",")) if v]
    unknown = [v for v in values if v not in allowed]
    if unknown:
        raise ValidationError({name: f"Неизвестное значение: {', '.join(unknown)}."})
    return values


def filter_vacancies(qs, params):
    """Применяет фильтры S-02 к выборке опубликованных вакансий."""
    qs = qs.annotate(salary_max=Coalesce("salary_to", "salary_from"))

    if q := " ".join(params.get("q", "").split()):
        skill_match = Vacancy.skills.through.objects.filter(vacancy_id=OuterRef("pk"), skill__name=Skill.normalize(q))
        qs = qs.filter(
            Q(title__icontains=q) | Q(description__icontains=q) | Q(company__name__icontains=q) | Q(Exists(skill_match))
        )

    if city := params.get("city", "").strip():
        qs = qs.filter(city__iexact=city)

    if salary := params.get("salary", "").strip():
        if not salary.isdigit():
            raise ValidationError({"salary": "Укажите зарплату целым числом в сомах."})
        # «зарплата от X»: вилка вакансии дотягивается до X; без указанной зарплаты — не показываем
        qs = qs.filter(salary_max__gte=int(salary))

    for name, allowed in MULTI_FILTERS.items():
        if raw := params.get(name, "").strip():
            qs = qs.filter(**{f"{name}__in": _choices(name, raw, allowed)})

    if params.get("internship") == "true":
        qs = qs.filter(is_internship=True)

    ordering = params.get("ordering", "new")
    if ordering not in ORDERINGS:
        raise ValidationError({"ordering": "Допустимо: new, salary."})
    return qs.order_by(*ORDERINGS[ordering])
