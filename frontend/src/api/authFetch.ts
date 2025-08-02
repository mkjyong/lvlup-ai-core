/*
 * authFetch – lightweight fetch wrapper with automatic Bearer token attach & 401 refresh retry.
 */
export async function authFetch(
  input: RequestInfo | URL,
  init?: RequestInit & { retry?: boolean },
): Promise<Response> {
  const token = localStorage.getItem("token");
  const headers = new Headers(init?.headers || {});
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const cfg: RequestInit = { ...init, headers, credentials: "include" };

  const resp = await fetch(input, cfg);
  if (resp.status !== 401 || init?.retry) return resp;

  // try refresh once
  try {
    const refreshResp = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    if (refreshResp.ok) {
      const { access_token }: { access_token: string } = await refreshResp.json();
      localStorage.setItem("token", access_token);
      const retryHeaders = new Headers(headers);
      retryHeaders.set("Authorization", `Bearer ${access_token}`);
      return fetch(input, { ...init, headers: retryHeaders, credentials: "include", retry: true });
    }
  } catch {
    // ignore; fallthrough to unauthorized
  }
  return resp;
}
