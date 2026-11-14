import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, errorText } from "../api.js";
import { useAuth } from "../auth.jsx";
import { Empty, ErrorState, Loading } from "../components/States.jsx";
import { SCHEDULE, formatSalary } from "../labels.js";

const FRESH_COUNT = 6;

// E-02: последние опубликованные вакансии. Поиск с фильтрами (S-02) — на следующем этапе.
function FreshVacancies() {
  const [vacancies, setVacancies] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setError("");
    api("/vacancies/")
      .then((data) => setVacancies(data.results.slice(0, FRESH_COUNT)))
      .catch((err) => setError(errorText(err)));
  }, []);

  useEffect(load, [load]);

  return (
    <section>
      <h2>Свежие вакансии</h2>
      {error && <ErrorState message={error} onRetry={load} />}
      {!error && !vacancies && <Loading />}
      {vacancies?.length === 0 && <Empty>Пока нет опубликованных вакансий.</Empty>}
      <ul className="vacancy-grid">
        {vacancies?.map((v) => (
          <li key={v.id} className="card vacancy-card">
            <h3>{v.title}</h3>
            <p className="muted small">
              {v.company.name} · {v.city}
            </p>
            <p className="salary">{formatSalary(v.salary_from, v.salary_to)}</p>
            <div className="tags">
              {v.is_internship && <span className="tag accent">Стажировка</span>}
              <span className="tag">{SCHEDULE[v.schedule]}</span>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function HomePage() {
  const { user } = useAuth();
  return (
    <>
      <section className="hero">
        <h1>Стажировки и первая работа в Кыргызстане</h1>
        <p className="muted">
          Студенты и выпускники создают резюме и портфолио, компании публикуют вакансии. Поиск с фильтрами появится на
          следующем этапе.
        </p>
        {!user && (
          <div className="row">
            <Link to="/register" className="btn">
              Создать аккаунт
            </Link>
            <Link to="/login">Уже есть аккаунт</Link>
          </div>
        )}
        {user?.role === "seeker" && (
          <Link to="/resumes" className="btn">
            Перейти к резюме
          </Link>
        )}
        {user?.role === "employer" && (
          <Link to="/vacancies/my" className="btn">
            Мои вакансии
          </Link>
        )}
      </section>
      <FreshVacancies />
    </>
  );
}
