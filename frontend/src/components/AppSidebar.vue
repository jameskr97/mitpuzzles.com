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
  SidebarSeparator,
  useSidebar,
} from "@/components/ui/sidebar";
import { ACTIVE_GAMES, DEV_TOOLS } from "@/constants";
import { useAuthStore } from "@/store/auth.ts";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useVisitorStore } from "@/store/visitor.ts";
import AppLogo from "@/components/AppLogo.vue";
import DialogAnonChangeUsername from "@/components/ui/DialogAnonChangeUsername.vue";
import AppThemeButton from "@/components/AppThemeButton.vue";
import AppFeedbackModal from "@/components/AppFeedbackModal.vue";
import AppThemeIcon from "@/AppThemeIcon.vue";

const isDev = import.meta.env.DEV;
const user = useAuthStore();
const sidebar = useSidebar();
const visitor = useVisitorStore();

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
        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem v-for="game in Object.values(ACTIVE_GAMES)">
              <SidebarMenuButton asChild :tooltip="game.name">
                <router-link :to="{ name: 'game-' + game.key }" class="text-xl" @click="close_sidebar_on_mobile">
                  <span>{{ game.icon }}</span>
                  <span>{{ game.name }}</span>
                </router-link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>

      <SidebarGroup v-if="isDev || user.isAdmin">
        <SidebarGroupLabel class="text-lg">Dev Tools</SidebarGroupLabel>
        <SidebarMenu>
          <SidebarMenuItem v-for="tool in DEV_TOOLS" :key="tool.key">
            <SidebarMenuButton asChild :tooltip="tool.name" v-if="user.isAdmin || !tool.requires_admin">
              <router-link :to="{ name: 'dev-' + tool.key }" class="text-xl" @click="close_sidebar_on_mobile">
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

          <AppThemeButton>
            <SidebarMenuButton>
              <AppThemeIcon />
              Dark Mode
            </SidebarMenuButton>
          </AppThemeButton>
        </SidebarMenu>
      </SidebarGroup>
      <SidebarSeparator />
      <SidebarMenu>
        <SidebarMenuItem>
          <DropdownMenu>
            <DropdownMenuTrigger as-child>
              <SidebarMenuButton
                size="lg"
                class="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
              >
                <Avatar class="h-8 w-8 rounded-lg">
                  <AvatarImage src="https://placecats.com/100/100" alt="Placeholder Cat Image" />
                  <AvatarFallback class="rounded-lg"
                    >{{ visitor.generated_username.substring(0, 2).toUpperCase() }}
                  </AvatarFallback>
                </Avatar>
                <div class="grid flex-1 text-left text-sm leading-tight">
                  <span class="truncate font-semibold">{{ visitor.generated_username }}</span>
                  <span class="truncate text-xs">Anonymous User</span>
                </div>
                <v-icon name="bi-chevron-double-up" />
              </SidebarMenuButton>
            </DropdownMenuTrigger>
            <DropdownMenuContent class="w-56 rounded-lg" align="end">
              <DropdownMenuLabel class="text-xs">
                All users are assigned a randomly generated username. Your username will be
                <span class="font-bold">{{ visitor.generated_username }}</span> on any leaderboards.
              </DropdownMenuLabel>
              <DropdownMenuSeparator />

              <DropdownMenuLabel>
                <DialogAnonChangeUsername>
                  <template #trigger>
                    <div class="flex flex-row">
                      <v-icon name="hi-pencil-alt" :scale="1.5" />
                      <SidebarMenuButton> Change Username</SidebarMenuButton>
                    </div>
                  </template>
                </DialogAnonChangeUsername>
              </DropdownMenuLabel>
            </DropdownMenuContent>
          </DropdownMenu>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarFooter>
  </Sidebar>
</template>
