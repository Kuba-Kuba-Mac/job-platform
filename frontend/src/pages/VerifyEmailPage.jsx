import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, errorText } from "../api.js";
import { useAuth } from "../auth.jsx";
import { Loading } from "../components/States.jsx";

// F-04: страница из письма — /verify-email?uid=…&token=…
export default function VerifyEmailPage() {
  const [params] = useSearchParams();
  const { user, refreshUser } = useAuth();
  const [state, setState] = useState({ status: "loading", message: "" });
  // Ссылка одноразовая: не отправляем запрос второй раз (StrictMode вызывает эффекты дважды)
  const sent = useRef(false);

  const uid = params.get("uid");
  const token = params.get("token");

  useEffect(() => {
    if (sent.current) return;
    sent.current = true;
    if (!uid || !token) {
      setState({ status: "error", message: "В ссылке не хватает данных. Откройте ссылку из письма целиком." });
      return;
    }
    api("/auth/verify-email/", { method: "POST", body: { uid, token } })
      .then(() => {
        setState({ status: "ok", message: "" });
        if (user) refreshUser().catch(() => {});
      })
      .catch((err) => setState({ status: "error", message: errorText(err) }));
  }, [uid, token, user, refreshUser]);

  return (
    <section className="card narrow">
      <h2>Подтверждение email</h2>
      {state.status === "loading" && <Loading text="Проверяем ссылку…" />}
      {state.status === "ok" && (
        <>
          <p className="success">Email подтверждён. Спасибо!</p>
          <Link to={user ? "/profile" : "/login"} className="btn">
            {user ? "Перейти в профиль" : "Войти"}
          </Link>
        </>
      )}
      {state.status === "error" && (
        <>
          <p className="error pre">{state.message}</p>
          <p className="muted small">
            {user
              ? "Новое письмо можно запросить в плашке вверху страницы."
              : "Войдите в аккаунт — там можно запросить новое письмо."}
          </p>
        </>
      )}
    </section>
  );
}
