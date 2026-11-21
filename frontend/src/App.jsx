import { useState } from "react";
import { Link, NavLink, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import CompanyPage from "./pages/CompanyPage.jsx";
import ResumesPage from "./pages/ResumesPage.jsx";
import HomePage from "./pages/HomePage.jsx";
import ChangePasswordPage from "./pages/ChangePasswordPage.jsx";
import VerifyEmailPage from "./pages/VerifyEmailPage.jsx";
import ForgotPasswordPage from "./pages/ForgotPasswordPage.jsx";
import ResetPasswordPage from "./pages/ResetPasswordPage.jsx";
import ProfilePage from "./pages/ProfilePage.jsx";
import MyVacanciesPage from "./pages/MyVacanciesPage.jsx";
import PortfolioPage from "./pages/PortfolioPage.jsx";
import SeekerPage from "./pages/SeekerPage.jsx";
import AdminUsersPage from "./pages/AdminUsersPage.jsx";
import ModerationPage from "./pages/ModerationPage.jsx";
import SearchPage from "./pages/SearchPage.jsx";
import VerifyEmailBanner from "./components/VerifyEmailBanner.jsx";
import { Loading } from "./components/States.jsx";

// F-06 на клиенте: прячем страницы чужой роли. Настоящая проверка — на сервере.
function RequireRole({ role, children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <Loading />;
  if (!user) return <Navigate to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`} replace />;
  if (role && user.role !== role) return <p className="error">Недоступно для вашей роли.</p>;
  return children;
}

// Меню по ролям (F-06). Порядок — по частоте использования.
const MENU = {
  guest: [["/vacancies", "Вакансии"]],
  seeker: [
    ["/vacancies", "Вакансии"],
    ["/resumes", "Мои резюме"],
    ["/portfolio", "Проекты и GitHub"],
  ],
  employer: [
    ["/company", "Моя компания"],
    ["/vacancies/my", "Мои вакансии"],
  ],
  admin: [
    ["/admin/moderation", "Модерация"],
    ["/admin/users", "Пользователи"],
  ],
};

// Маршруты: [путь, страница, роль]. role: undefined — для всех, "any" — любой вошедший.
const ROUTES = [
  ["/", HomePage],
  ["/login", LoginPage],
  ["/register", RegisterPage],
  ["/verify-email", VerifyEmailPage],
  ["/forgot-password", ForgotPasswordPage],
  ["/reset-password", ResetPasswordPage],
  ["/vacancies", SearchPage],
  ["/company", CompanyPage, "employer"],
  ["/vacancies/my", MyVacanciesPage, "employer"],
  ["/resumes", ResumesPage, "seeker"],
  ["/portfolio", PortfolioPage, "seeker"],
  ["/seekers/:id", SeekerPage, "any"],
  ["/profile", ProfilePage, "any"],
  ["/settings/password", ChangePasswordPage, "any"],
  ["/admin/users", AdminUsersPage, "admin"],
  ["/admin/moderation", ModerationPage, "admin"],
];

function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const items = MENU[user?.role ?? "guest"] ?? [];

  return (
    <header className="header">
      <Link to="/" className="logo">
        Стажировки<span>KG</span>
      </Link>
      <button
        type="button"
        className="menu-toggle"
        aria-expanded={open}
        aria-controls="main-nav"
        onClick={() => setOpen(!open)}
      >
        {open ? "Закрыть" : "Меню"}
      </button>
      <nav id="main-nav" className={open ? "open" : ""} onClick={() => setOpen(false)}>
        {items.map(([to, label]) => (
          <NavLink key={to} to={to} end>
            {label}
          </NavLink>
        ))}
        {user?.role === "admin" && (
          <a href="/admin/" target="_blank" rel="noreferrer">
            Админка Django
          </a>
        )}
        {user ? (
          <>
            <Link to="/profile" className="small user-link" title="Мой профиль">
              {user.full_name || user.email}
            </Link>
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
      <VerifyEmailBanner />
      <main className="container">
        <Routes>
          {ROUTES.map((route) => {
            const [path, Page, role] = route;
            const page = <Page />;
            return (
              <Route
                key={path}
                path={path}
                element={role ? <RequireRole role={role === "any" ? undefined : role}>{page}</RequireRole> : page}
              />
            );
          })}
          <Route path="*" element={<p>Страница не найдена</p>} />
        </Routes>
      </main>
    </>
  );
}
