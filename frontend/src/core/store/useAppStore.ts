import { defineStore } from "pinia";
import { Thumbmark } from "@thumbmarkjs/thumbmarkjs";
import { api } from "@/core/services/axios.ts";

const CACHE_VERSION = 1;
const CACHE_STORAGE_KEY = 'mitlogic.cache.version';
const CONSENT_STORAGE_KEY = 'mitlogic.privacy.consent';

export const useAppStore = defineStore("mitlogic.appconfig", {
  state: () => ({
    thumbmark: {} as Record<string, any>,
    device_id: null as string | null,
    lastCacheVersion: 0,
    login_modal_open: false,
    has_consented: false,
  }),
  getters: {
    needsCacheInvalidation: (state) => state.lastCacheVersion < CACHE_VERSION,
  },
  actions: {
    open_login_modal() { this.login_modal_open = true; },
    close_login_modal() { this.login_modal_open = false; },

    async updateDeviceFingerprint() {
      this.thumbmark = await(new Thumbmark()).get();
      try {
        const response = await api.put("/api/device", { thumbmark: this.thumbmark  });
        this.device_id = response.data.device_id;
      } catch (error: any) {}
    },

    async invalidateAllCaches() {
      // Clear Workbox-managed caches
      await Promise.all([
        caches.delete('puzzle-catalog'),
        caches.delete('puzzle-definitions'),
        caches.delete('leaderboards'),
        caches.delete('daily-definitions'),
        caches.delete('daily-status'),
        caches.delete('daily-leaderboards'),
      ]);

      // Clear localStorage caches
      localStorage.removeItem('mitlogic.puzzle.scales');

      this.lastCacheVersion = CACHE_VERSION;
      localStorage.setItem(CACHE_STORAGE_KEY, CACHE_VERSION.toString());
    },

    initCacheVersion() {
      const storedVersion = localStorage.getItem(CACHE_STORAGE_KEY);
      this.lastCacheVersion = storedVersion ? parseInt(storedVersion) : 0;

      if (this.lastCacheVersion < CACHE_VERSION)
        this.invalidateAllCaches();
    },

    init_consent() {
      this.has_consented = localStorage.getItem(CONSENT_STORAGE_KEY) === 'true';
    },

    accept_consent() {
      this.has_consented = true;
      localStorage.setItem(CONSENT_STORAGE_KEY, 'true');
    },

  },
});
