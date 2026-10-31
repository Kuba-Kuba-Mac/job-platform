import { Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import CompanyPage from "./pages/CompanyPage.jsx";
import ResumesPage from "./pages/ResumesPage.jsx";
import HomePage from "./pages/HomePage.jsx";

// F-06 на клиенте: прячем страницы чужой роли. Настоящая проверка — на сервере.
function RequireRole({ role, children }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="muted">Загрузка…</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (role && user.role !== role) return <p className="error">Эта страница недоступна для вашей роли.</p>;
  return children;
}

function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="header">
      <Link to="/" className="logo">
        Стажировки<span>KG</span>
      </Link>
      <nav>
        {user?.role === "seeker" && <Link to="/resumes">Мои резюме</Link>}
        {user?.role === "employer" && <Link to="/company">Моя компания</Link>}
        {user ? (
          <>
            <span className="muted small">{user.email}</span>
            <button
              className="link"
              onClick={async () => {
                await logout();
                navigate("/");
              }}
            >
              Выйти
            </button>
          </>
        ) : (
          <>
            <Link to="/login">Вход</Link>
            <Link to="/register" className="btn">
              Регистрация
            </Link>
          </>
        )}
      </nav>
    </header>
  );
}

export default function App() {
  return (
    <>
      <Header />
      <main className="container">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/company"
            element={
              <RequireRole role="employer">
                <CompanyPage />
              </RequireRole>
            }
          />
          <Route
            path="/resumes"
            element={
              <RequireRole role="seeker">
                <ResumesPage />
              </RequireRole>
            }
          />
          <Route path="*" element={<p>Страница не найдена</p>} />
        </Routes>
      </main>
    </>
  );
}
