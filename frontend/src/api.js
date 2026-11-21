// Обёртка над fetch: подставляет JWT, при 401 один раз обновляет access-токен.
const TOKENS_KEY = "jp_tokens";

export function getTokens() {
  try {
    return JSON.parse(localStorage.getItem(TOKENS_KEY)) || null;
  } catch {
    return null;
  }
}

export function setTokens(tokens) {
  if (tokens) localStorage.setItem(TOKENS_KEY, JSON.stringify(tokens));
  else localStorage.removeItem(TOKENS_KEY);
}

export class ApiError extends Error {
  constructor(status, data) {
    super(formatErrors(data) || `Ошибка ${status}`);
    this.status = status;
    this.data = data;
  }
}

function formatErrors(data) {
  if (!data || typeof data !== "object") return "";
  if (data.detail) return [].concat(data.detail).join(" ");
  return Object.entries(data)
    .map(([field, msgs]) => `${field}: ${[].concat(msgs).join(" ")}`)
    .join("\n");
}

// Текст ошибки для формы: сообщения сервера уже на русском и понятны без имени поля
export function errorText(err) {
  if (!(err instanceof ApiError)) return "Не удалось связаться с сервером. Проверьте подключение и попробуйте ещё раз.";
  if (err.status >= 500) return "На сервере произошла ошибка. Попробуйте позже.";
  if (!err.data || typeof err.data !== "object" || err.data.detail) return err.message;
  return Object.values(err.data).flat().join("\n");
}

async function refreshAccess() {
  const tokens = getTokens();
  if (!tokens?.refresh) return false;
  const resp = await fetch("/api/auth/refresh/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: tokens.refresh }),
  });
  if (!resp.ok) {
    // сессия отозвана (выход на другом устройстве, смена пароля, блокировка — A-01)
    setTokens(null);
    window.dispatchEvent(new Event("auth:expired"));
    return false;
  }
  const data = await resp.json();
  setTokens({ access: data.access, refresh: data.refresh || tokens.refresh });
  return true;
}

export async function api(path, { method = "GET", body, retry = true } = {}) {
  const headers = {};
  const tokens = getTokens();
  if (tokens?.access) headers.Authorization = `Bearer ${tokens.access}`;

  let payload;
  if (body instanceof FormData) payload = body;
  else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const resp = await fetch(`/api${path}`, { method, headers, body: payload });

  if (resp.status === 401 && retry && tokens?.refresh && (await refreshAccess())) {
    return api(path, { method, body, retry: false });
  }

  const text = await resp.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    // не JSON (например, страница ошибки прокси) — покажем общий текст ошибки
  }
  if (!resp.ok) throw new ApiError(resp.status, data);
  return data;
}
