// src/services/authService.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;

export const authService = {
  async login(email: string, password: string) {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const res = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData,
    });

    if (!res.ok) throw new Error("Credenciales inválidas");

    const data = await res.json();
    if (data.access_token) {
      document.cookie = `scada_token=${data.access_token}; max-age=3600; path=/; samesite=lax`;
      document.cookie = `scada_email=${email}; max-age=3600; path=/; samesite=lax`;
      if (typeof window !== "undefined" && data.user_info) {
        localStorage.setItem("scada_userName", data.user_info.full_name);
        localStorage.setItem("scada_userRole", data.user_info.role);
      }
    }
    return data;
  },

  logout() {
    // Revoca el token en el servidor (best-effort: la sesión local se cierra igual si falla)
    const token = `; ${document.cookie}`.split(`; scada_token=`).pop()?.split(';').shift() || "";
    if (token) {
      fetch(`${API_URL}/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        keepalive: true,
      }).catch(() => { /* sin acción */ });
    }
    document.cookie = "scada_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = "scada_email=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    if (typeof window !== "undefined") {
      localStorage.removeItem("scada_userName");
      localStorage.removeItem("scada_userRole");
      localStorage.removeItem("scada_userEmail");
    }
    // replace: la página protegida no queda en el historial
    window.location.replace("/login");
  }
};