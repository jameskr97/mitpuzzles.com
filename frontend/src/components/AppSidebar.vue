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
} from "@/components/ui/sidebar";
import { ACTIVE_EXPERIMENTS, ACTIVE_GAMES, DEV_TOOLS } from "@/constants";
import { useAuthStore } from "@/store/useAuthStore";
import AppLogo from "@/components/AppLogo.vue";
import AppFeedbackModal from "@/components/AppFeedbackModal.vue";
import AppSidebarUser from "@/components/AppSidebarUser.vue";
import UserLoginModal from "@/components/UserLoginModal.vue";

const user = useAuthStore();
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
        <SidebarGroupLabel>Games</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem v-for="game in Object.values(ACTIVE_GAMES)" :key="game.key">
              <SidebarMenuButton asChild :tooltip="game.name">
                <router-link :to="{ name: 'game-' + game.key }" class="text-xl" @click.capture="close_sidebar_on_mobile">
                  <span>{{ game.icon }}</span>
                  <span>{{ game.name }}</span>
                </router-link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>

      <SidebarGroup>
        <SidebarGroupLabel>Experiments</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem v-for="(value, index) in ACTIVE_EXPERIMENTS">
              <SidebarMenuButton asChild>
                <router-link :to="'/experiment/' + value.key" :key="value.key" class="text-xl" @click="close_sidebar_on_mobile">
                  <span>{{value.icon}}</span>
                  <span>{{value.title}}</span>
                </router-link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>

      <SidebarGroup v-if="user.isAdmin">
        <SidebarGroupLabel>Data Access</SidebarGroupLabel>
        <SidebarMenu>
          <SidebarMenuItem></SidebarMenuItem>
          <SidebarMenuButton asChild>
            <router-link to="/admin/data-download" class="text-xl">
              <span>🧮</span>
              <span>Data Download</span>
            </router-link>
          </SidebarMenuButton>
        </SidebarMenu>
      </SidebarGroup>

      <SidebarGroup v-if="user.isAdmin">
        <SidebarGroupLabel class="text-lg">Dev Tools (Admin Only)</SidebarGroupLabel>
        <SidebarMenu>
          <SidebarMenuItem v-for="tool in DEV_TOOLS" :key="tool.key">
            <SidebarMenuButton asChild :tooltip="tool.name" v-if="!tool.requires_admin">
              <router-link :to="{ name: 'dev-' + tool.key }" class="text-xl" @click.capture="close_sidebar_on_mobile">
                <span>{{ tool.icon }}</span>
                <span>{{ tool.name }}</span>
              </router-link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarGroup>
    </SidebarContent>
    <SidebarFooter>
      <SidebarGroup>
        <SidebarMenu>
          <!-- About Us Button -->
          <SidebarMenuButton>
            <router-link :to="{ name: 'about-us' }">
              <v-icon name="bi-info-circle-fill" />
              About Us
            </router-link>
          </SidebarMenuButton>

          <!-- Feedback Button -->
          <AppFeedbackModal>
            <SidebarMenuButton>
              <v-icon name="md-feedback-outlined" />
              Feedback
            </SidebarMenuButton>
          </AppFeedbackModal>

          <!-- Login Modal -->
          <UserLoginModal v-if="!user.isAuthenticated">
            <SidebarMenuButton>
              <v-icon name="fa-user" />
              Login
            </SidebarMenuButton>
          </UserLoginModal>
          <AppSidebarUser v-else :user="user" />
        </SidebarMenu>
      </SidebarGroup>
    </SidebarFooter>
  </Sidebar>
</template>
