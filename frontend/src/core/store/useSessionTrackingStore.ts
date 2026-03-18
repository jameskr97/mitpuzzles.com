import { defineStore } from "pinia";
import { v7 as uuidv7 } from 'uuid';
import { useAppStore } from './useAppStore.ts';
import { useAuthStore } from './useAuthStore.ts';
import { api } from '@/core/services/client';
import { createLogger } from '@/core/services/logger.ts';
const log = createLogger('session_tracker');

const SESSION_ID_KEY = 'session_id';
const LAST_ACTIVITY_KEY = 'last_activity';
const HEARTBEAT_INTERVAL = 15000; // 15 seconds
const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes in ms

interface HeartbeatPayload {
  session_id: string;
  device_id: string;
  user_id?: string | null;
  active_duration_delta: number;
  initial_referrer?: string | null;
}

export const useSessionTrackingStore = defineStore("session_tracking", {
  state: () => ({
    session_id: '',
    is_tracking: false,
    is_visible: true,
    heartbeat_timer: null as NodeJS.Timeout | null,
    visible_start_time: null as number | null,
    accumulated_visible_time: 0,
    initial_referrer: null as string | null,
  }),

  getters: {
    is_session_active: (state) => !!state.session_id && state.is_tracking,
    device_id(): string | null { return useAppStore().device_id; },
    user_id(): string | null { return useAuthStore().user?.id || null; },
  },

  actions: {
    /**
     * initialize session tracking
     * call this after device fingerprinting is complete
     */
    initialize(): void {
      if (!this.is_local_storage_available()) {
        console.warn('SessionTracker: localStorage not available, tracking disabled');
        return;
      }

      this.initial_referrer = document.referrer || null;
      this.initialize_session();
      this.setup_visibility_tracking();

      if (this.device_id) {
        this.start_tracking();
        this.send_heartbeat();
        log('Initialized with session %s', this.session_id);
      } else {
        // device_id not ready yet — watch for it
        const appStore = useAppStore();
        const unwatch = appStore.$subscribe(() => {
          if (appStore.device_id) {
            unwatch();
            this.start_tracking();
            this.send_heartbeat();
            log('Initialized with session %s (after device_id ready)', this.session_id);
          }
        });
      }
    },

    /**
     * Stop tracking and cleanup
     */
    stop(): void {
      if (this.heartbeat_timer) {
        clearInterval(this.heartbeat_timer);
        this.heartbeat_timer = null;
      }

      // Remove event listeners
      document.removeEventListener('visibilitychange', this.handle_visibility_change);
      window.removeEventListener('focus', this.handle_visibility_change);
      window.removeEventListener('blur', this.handle_visibility_change);
      window.removeEventListener('pagehide', this.handle_page_hide);

      this.is_tracking = false;
      log('Stopped');
    },

    is_local_storage_available(): boolean {
      try {
        const test = '__localStorage_test__';
        localStorage.setItem(test, test);
        localStorage.removeItem(test);
        return true;
      } catch {
        return false;
      }
    },

    initialize_session(): void {
      const stored_session_id = localStorage.getItem(SESSION_ID_KEY);
      const stored_last_activity = localStorage.getItem(LAST_ACTIVITY_KEY);
      const now = Date.now();

      // Check if existing session is still valid
      if (stored_session_id && stored_last_activity) {
        const last_activity = parseInt(stored_last_activity, 10);
        const time_since_last_activity = now - last_activity;

        if (time_since_last_activity < SESSION_TIMEOUT) {
          // Reuse existing session
          this.session_id = stored_session_id;
          log('Resuming existing session %s', stored_session_id);
          this.update_last_activity();
          return;
        }
      }

      // Create new session
      this.session_id = uuidv7();
      localStorage.setItem(SESSION_ID_KEY, this.session_id);
      this.update_last_activity();
      log('Created new session %s', this.session_id);
    },

    update_last_activity(): void {
      localStorage.setItem(LAST_ACTIVITY_KEY, Date.now().toString());
    },

    setup_visibility_tracking(): void {
      // Set initial visibility state - must be both visible AND focused (active tab)
      this.is_visible = document.visibilityState === 'visible' && document.hasFocus();

      if (this.is_visible) {
        this.visible_start_time = Date.now();
      }

      // Add event listeners
      document.addEventListener('visibilitychange', this.handle_visibility_change);
      window.addEventListener('focus', this.handle_visibility_change);
      window.addEventListener('blur', this.handle_visibility_change);
      window.addEventListener('pagehide', this.handle_page_hide); // Fallback for older browsers
    },

    handle_visibility_change(): void {
      const now = Date.now();
      const was_visible = this.is_visible;
      // Check both visibility AND focus - only track the active tab
      this.is_visible = document.visibilityState === 'visible' && document.hasFocus();

      if (was_visible && !this.is_visible) {
        // Page became hidden/unfocused - accumulate visible time
        let accumulated_time = 0;
        if (this.visible_start_time) {
          const visible_duration = now - this.visible_start_time;
          this.accumulated_visible_time += visible_duration;
          accumulated_time = this.accumulated_visible_time;
          this.visible_start_time = null;
        }

        // Send final heartbeat when page becomes hidden
        this.send_beacon_heartbeat();

        log('Page hidden/unfocused, accumulated %dms', accumulated_time);
      } else if (!was_visible && this.is_visible) {
        // Page became visible and focused - start tracking again
        this.visible_start_time = now;
        log('Page visible and focused again');
      }
    },

    handle_page_hide(): void {
      // Fallback for browsers that don't support visibilitychange
      // This should only fire if visibilitychange didn't already handle it
      if (this.is_visible) {
        this.handle_visibility_change();
      }
    },

    start_tracking(): void {
      if (this.heartbeat_timer) {
        clearInterval(this.heartbeat_timer);
      }

      this.heartbeat_timer = setInterval(() => {
        // Only send heartbeat if page is visible
        if (this.is_visible) {
          this.send_heartbeat();
        }
      }, HEARTBEAT_INTERVAL);

      this.is_tracking = true;
    },

    calculate_active_duration(): number {
      const now = Date.now();
      let total_visible_time = this.accumulated_visible_time;

      // Add current visible time if page is currently visible
      if (this.is_visible && this.visible_start_time) {
        const current_visible_time = now - this.visible_start_time;
        total_visible_time += current_visible_time;
      }

      // Convert to seconds and reset accumulated time
      const active_seconds = Math.floor(total_visible_time / 1000);
      this.accumulated_visible_time = 0;

      // Reset visible start time if page is visible
      if (this.is_visible) {
        this.visible_start_time = now;
      }

      return active_seconds;
    },

    async send_heartbeat(): Promise<void> {
      if (!this.device_id || !this.session_id) {
        console.warn('SessionTracker: Cannot send heartbeat - missing device_id or session_id');
        return;
      }

      const active_duration = this.calculate_active_duration();

      const payload: HeartbeatPayload = {
        session_id: this.session_id,
        device_id: this.device_id,
        user_id: this.user_id,
        active_duration_delta: active_duration,
        initial_referrer: this.initial_referrer,
      };

      try {
        await api.POST("/api/tracking/heartbeat", { body: payload });
        this.update_last_activity();
        log('Heartbeat sent, active_duration: %d', active_duration);
      } catch (error) {
        console.warn('SessionTracker: Heartbeat request failed:', error);
        // don't reset counters on failure - will retry next interval
        this.accumulated_visible_time += active_duration * 1000;
      }
    },

    send_beacon_heartbeat(): void {
      if (!this.device_id || !this.session_id) {
        return;
      }

      const active_duration = this.calculate_active_duration();

      const payload: HeartbeatPayload = {
        session_id: this.session_id,
        device_id: this.device_id,
        user_id: this.user_id,
        active_duration_delta: active_duration,
        initial_referrer: this.initial_referrer,
      };

      // Use sendBeacon for reliability when page is being hidden
      if (navigator.sendBeacon) {
        const blob = new Blob([JSON.stringify(payload)], {
          type: 'application/json',
        });

        const success = navigator.sendBeacon('/api/tracking/heartbeat', blob);
        log('Beacon sent %s, active_duration: %d', success ? 'successfully' : 'failed', active_duration);
      } else {
        // fallback for browsers without sendBeacon
        api.POST("/api/tracking/heartbeat", { body: payload }).catch(() => {});
      }
    },
  },
});
