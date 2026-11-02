const API_URL = "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(data?.detail || "Произошла ошибка");
  }

  return data;
}

export const reportsApi = {
  list(params = {}) {
    const query = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value) query.set(key, value);
    });

    const suffix = query.toString() ? `?${query}` : "";
    return request(`/reports/${suffix}`);
  },

  get(id) {
    return request(`/reports/${id}/`);
  },

  create(data) {
    return request("/reports/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  update(id, data) {
    return request(`/reports/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },
};