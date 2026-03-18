import { defineStore } from 'pinia';
import { api } from '@/core/services/client';

export const usePushStore = defineStore('push', {
  state: () => ({
    is_supported: 'serviceWorker' in navigator && 'PushManager' in window,
    is_subscribed: false,
    is_loading: false,
    error: '',
  }),

  actions: {
    // Convert VAPID public key from base64 to Uint8Array
    urlBase64ToUint8Array(base64String: string) {
      const padding = '='.repeat((4 - base64String.length % 4) % 4);
      const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');

      const rawData = window.atob(base64);
      const outputArray = new Uint8Array(rawData.length);

      for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
      }
      return outputArray;
    },

    // Helper function to convert ArrayBuffer to base64
    arrayBufferToBase64(buffer: ArrayBuffer | null): string {
      if (!buffer) return '';
      const bytes = new Uint8Array(buffer);
      let binary = '';
      for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
      }
      return window.btoa(binary);
    },

    async check_subscription_status() {
      if (!this.is_supported) return;
      const { data, error } = await api.GET('/api/push/subscription-status');
      if (error) return;
      this.is_subscribed = data.subscribed;
    },

    async subscribe() {
      if (!this.is_supported) {
        this.error = 'Push notifications are not supported in this browser';
        return false;
      }

      if (Notification.permission === 'denied') {
        this.error = 'Notification permission was previously denied. Please enable it in browser settings.';
        return false;
      } else {
        this.error = 'Please click the switch again to grant notification permission';
        return false;
      }

      this.is_loading = true;
      this.error = '';

      // get VAPID key from backend
      const { data: vapidData, error: vapidError } = await api.GET('/api/push/vapid-public-key');
      if (vapidError) {
        this.error = 'Failed to get push notification key';
        this.is_loading = false;
        return false;
      }

      // browser push API — can throw
      let subscription: PushSubscription;
      try {
        const registration = await navigator.serviceWorker.ready;
        subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: this.urlBase64ToUint8Array(vapidData.public_key),
        });
      } catch (err) {
        console.error('Browser push subscription failed:', err);
        this.error = 'Failed to subscribe to push notifications';
        this.is_loading = false;
        return false;
      }

      // send subscription to backend
      const { error } = await api.POST('/api/push/subscribe', {
        body: {
          endpoint: subscription.endpoint,
          keys: {
            p256dh: this.arrayBufferToBase64(subscription.getKey('p256dh')),
            auth: this.arrayBufferToBase64(subscription.getKey('auth')),
          },
        },
      });
      if (error) {
        this.error = error.message;
        this.is_loading = false;
        return false;
      }

      this.is_subscribed = true;
      this.is_loading = false;
      return true;
    },

    async unsubscribe() {
      if (!this.is_supported) return false;

      this.is_loading = true;
      this.error = '';

      // browser push API — can throw
      let subscription: PushSubscription | null;
      try {
        const registration = await navigator.serviceWorker.ready;
        subscription = await registration.pushManager.getSubscription();
        if (subscription) await subscription.unsubscribe();
      } catch (err) {
        console.error('Browser push unsubscribe failed:', err);
        this.error = 'Failed to unsubscribe from push notifications';
        this.is_loading = false;
        return false;
      }

      // remove subscription from backend
      if (subscription) {
        const { error } = await api.DELETE('/api/push/unsubscribe', {
          body: {
            endpoint: subscription.endpoint,
            keys: {
              p256dh: this.arrayBufferToBase64(subscription.getKey('p256dh')),
              auth: this.arrayBufferToBase64(subscription.getKey('auth')),
            },
          },
        });
        if (error) {
          this.error = error.message;
          this.is_loading = false;
          return false;
        }
      }

      this.is_subscribed = false;
      this.is_loading = false;
      return true;
    },
  },
});
