import { Link } from "react-router-dom";
import { EXPERIENCE, SCHEDULE, formatSalary } from "../labels.js";

// Карточка опубликованной вакансии: главная, поиск (S-02), избранное (S-06)
export default function VacancyCard({ vacancy: v, actions }) {
  return (
    <li className="card vacancy-card">
      <div className="row between">
        <h3>
          <Link to={`/vacancies/${v.id}`}>{v.title}</Link>
        </h3>
        {actions}
      </div>
      <p className="muted small">
        {v.company.name} · {v.city}
      </p>
      <p className="salary">{formatSalary(v.salary_from, v.salary_to)}</p>
      <div className="tags">
        {v.is_internship && <span className="tag accent">Стажировка</span>}
        <span className="tag">{SCHEDULE[v.schedule]}</span>
        <span className="tag">{EXPERIENCE[v.experience]}</span>
      </div>
    </li>
  );
}
