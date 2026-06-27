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

    if (!res.ok) {
      throw new Error("Credenciales inválidas");
    }

    const data = await res.json();
    console.log("Respuesta del login:", data);

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
    // 1. Borramos la cookie del token
    document.cookie = "scada_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = "scada_email=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    
    // 2. Borramos el nombre guardado
    if (typeof window !== "undefined") {
      localStorage.removeItem("scada_userName");
      localStorage.removeItem("scada_userEmail");
    }
    // 3. Redirigimos al login
    window.location.href = "/login";
  }
};