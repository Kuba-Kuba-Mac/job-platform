// Подписи для значений, которые backend хранит кодами (vacancies/models.py)
export const EXPERIENCE = {
  none: "Без опыта",
  "1-3": "1–3 года",
  "3-6": "3–6 лет",
  "6+": "Более 6 лет",
};

export const EMPLOYMENT_TYPE = {
  full: "Полная занятость",
  part: "Частичная занятость",
  project: "Проектная работа",
};

export const SCHEDULE = {
  full_day: "Полный день",
  shift: "Сменный график",
  flexible: "Гибкий график",
  remote: "Удалённая работа",
};

export const MODERATION = { pending: "На модерации", approved: "Одобрена", rejected: "Отклонена" };

export const ROLE = { seeker: "Соискатель", employer: "Работодатель", admin: "Администратор" };

const money = (n) => n.toLocaleString("ru-RU");

export function formatSalary(from, to) {
  if (from && to) return `${money(from)} – ${money(to)} сом`;
  if (from) return `от ${money(from)} сом`;
  if (to) return `до ${money(to)} сом`;
  return "Зарплата по договорённости";
}

export const splitList = (s) =>
  s
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
