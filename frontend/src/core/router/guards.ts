import type { Router } from "vue-router";
import { useAuthStore } from "@/core/store/useAuthStore.ts";

export function setup_auth_guard(router: Router) {
  const auth_store = useAuthStore();

  router.beforeEach(async (to, from, next) => {
    console.log(`Navigating to ${to.fullPath} from ${from.fullPath}`);
    const is_admin = auth_store.isAdmin;
    const is_authenticated = auth_store.isAuthenticated;
    const requires_admin = to.meta.requiresAdmin || false;
    const require_logged_in = to.meta.requireLoggedIn || false;

    if (requires_admin && !is_admin) {
      console.log("Access denied: Admins only");
      next({ name: "Home" });
    } else if (require_logged_in && !is_authenticated) {
      console.log("Access denied: Login required");
      next({ name: "Home" });
    } else {
      next();
    }
  });
}

export async function check_initial_route(router: Router) {
  const auth_store = useAuthStore();
  const current_route = router.currentRoute.value;

  if (current_route.meta.requiresAdmin && !auth_store.isAdmin) {
    console.log("Initial route requires admin, redirecting to Home");
    await router.replace({ name: "Home" });
  }
  if (current_route.meta.requireLoggedIn && !auth_store.isAuthenticated) {
    console.log("Initial route requires login, redirecting to Home");
    await router.replace({ name: "Home" });
  }
}
