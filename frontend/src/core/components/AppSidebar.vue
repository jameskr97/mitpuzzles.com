<script setup lang="ts">
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  useSidebar,
} from "@/core/components/ui/sidebar";
import { ACTIVE_EXPERIMENTS, ACTIVE_GAMES, ADMIN_TOOLS } from "@/constants.ts";
import { useAuthStore } from "@/core/store/useAuthStore.ts";
import AppLogo from "@/core/components/AppLogo.vue";
import AppFeedbackModal from "@/core/components/AppFeedbackModal.vue";
import AppSidebarUser from "@/core/components/AppSidebarUser.vue";
import { useAppStore } from "@/core/store/useAppStore.ts";

const user = useAuthStore();
const appStore = useAppStore();
const sidebar = useSidebar();

const close_sidebar_on_mobile = () => {
  if (sidebar.isMobile.value) {
    sidebar.toggleSidebar();
  }
};
</script>

<template>
  <Sidebar variant="floating" collapsible="icon">
    <SidebarRail />
    <SidebarHeader>
      <AppLogo img-class="p-3" @click="close_sidebar_on_mobile" />
    </SidebarHeader>
    <SidebarContent>
      <SidebarGroup>
        <SidebarGroupLabel>{{ $t("ui:nav.games") }}</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton asChild tooltip="Daily Puzzle">
                <router-link
                  :to="{ name: 'game-daily'}"
                  class="text-xl"
                  @click.capture="close_sidebar_on_mobile"
                >
                  <span>🗓</span>
                  <span>Daily Puzzle</span>
                </router-link>
              </SidebarMenuButton>
            </SidebarMenuItem>
            <SidebarMenuItem v-for="game in Object.values(ACTIVE_GAMES)" :key="game.key">
              <SidebarMenuButton asChild :tooltip="game.name">
                <router-link
                  :to="{ name: 'game-' + game.key }"
                  class="text-xl"
                  @click.capture="close_sidebar_on_mobile"
                >
                  <span>{{ game.icon }}</span>
                  <span>{{ game.name }}</span>
                </router-link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>

      <SidebarGroup>
        <SidebarGroupLabel>{{ $t("ui:nav.experiments") }}</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem v-for="value in ACTIVE_EXPERIMENTS">
              <SidebarMenuButton asChild>
                <router-link
                  :to="'/experiment/' + value.key"
                  :key="value.key"
                  class="text-xl"
                  @click="close_sidebar_on_mobile"
                >
                  <span>{{ value.icon }}</span>
                  <span>{{ value.title }}</span>
                </router-link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>

      <SidebarGroup v-if="user.isAdmin">
        <SidebarGroupLabel>Data Access</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem v-for="tool in Object.values(ADMIN_TOOLS)" :key="tool.key">
              <SidebarMenuButton asChild :tooltip="tool.name">
                <router-link :to="tool.route_path" class="text-xl" @click.capture="close_sidebar_on_mobile">
                  <span>{{ tool.icon }}</span>
                  <span>{{ tool.name }}</span>
                </router-link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
    </SidebarContent>
    <SidebarFooter>
      <SidebarGroup>
        <SidebarMenu>
          <!-- About Us Button -->
          <SidebarMenuButton asChild>
            <router-link :to="{ name: 'about-us' }" @click.capture="close_sidebar_on_mobile">
              <v-icon name="bi-info-circle-fill" />
              {{ $t("ui:nav.about_us") }}
            </router-link>
          </SidebarMenuButton>

          <!-- Feedback Button -->
          <AppFeedbackModal>
            <SidebarMenuButton>
              <v-icon name="md-feedback-outlined" />
              {{ $t("ui:nav.feedback") }}
            </SidebarMenuButton>
          </AppFeedbackModal>

          <SidebarMenuButton asChild>
            <router-link :to="{ name: 'privacy-policy' }" @click.capture="close_sidebar_on_mobile">
              <v-icon name="bi-shield-lock-fill" />
              {{ $t("ui:nav.privacy_policy") }}
            </router-link>
          </SidebarMenuButton>

          <!-- Login Button -->
          <SidebarMenuButton
            v-if="!user.isAuthenticated"
            data-testid="btn-open-login"
            @click="appStore.open_login_modal()"
          >
            <v-icon name="fa-user" />
            {{ $t("ui:action.login") }}
          </SidebarMenuButton>
          <AppSidebarUser v-else :user="user" />
        </SidebarMenu>
      </SidebarGroup>
    </SidebarFooter>
  </Sidebar>
</template>
