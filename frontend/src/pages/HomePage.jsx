import { Link } from "react-router-dom";
import { useAuth } from "../auth.jsx";

export default function HomePage() {
  const { user } = useAuth();
  return (
    <section className="hero">
      <h1>Стажировки и первая работа в Кыргызстане</h1>
      <p className="muted">
        Студенты и выпускники создают резюме, компании публикуют вакансии. Поиск вакансий появится на следующем этапе.
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
        <Link to="/company" className="btn">
          Профиль компании
        </Link>
      )}
    </section>
  );
}
