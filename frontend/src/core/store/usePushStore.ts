import { defineStore } from 'pinia';
import axios from 'axios';

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

    // Check current subscription status
    async check_subscription_status() {
      if (!this.is_supported) return;

      try {
        const response = await axios.get('/api/push/subscription-status');
        this.is_subscribed = response.data.subscribed;
      } catch (err: any) {
        console.error('Failed to check subscription status:', err);
      }
    },

    // Subscribe to push notifications
    async subscribe() {
      if (!this.is_supported) {
        this.error = 'Push notifications are not supported in this browser';
        return false;
      }

      if (Notification.permission === 'denied') {
        this.error = 'Notification permission was previously denied. Please enable it in browser settings.';
        return false;
      } else {
        // Permission is 'default' - need to request it
        // This MUST be called synchronously from a user gesture
        this.error = 'Please click the switch again to grant notification permission';
        return false;
      }

      this.is_loading = true;
      this.error = '';

      try {
        // Get the service worker registration
        const registration = await navigator.serviceWorker.ready;

        // Get VAPID public key from backend
        const vapidResponse = await axios.get('/api/push/vapid-public-key');
        const vapid_public_key = vapidResponse.data.public_key;

        // Subscribe to push notifications
        const subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: this.urlBase64ToUint8Array(vapid_public_key),
        });

        // Send subscription to backend
        await axios.post('/api/push/subscribe', {
          endpoint: subscription.endpoint,
          keys: {
            p256dh: this.arrayBufferToBase64(subscription.getKey('p256dh')),
            auth: this.arrayBufferToBase64(subscription.getKey('auth')),
          },
        });

        this.is_subscribed = true;
        this.is_loading = false;
        return true;

      } catch (err: any) {
        console.error('Failed to subscribe to push notifications:', err);
        this.error = err.response?.data?.detail || 'Failed to subscribe to push notifications';
        this.is_loading = false;
        return false;
      }
    },

    // Unsubscribe from push notifications
    async unsubscribe() {
      if (!this.is_supported) return false;

      this.is_loading = true;
      this.error = '';

      try {
        // Get the service worker registration
        const registration = await navigator.serviceWorker.ready;

        // Get current subscription
        const subscription = await registration.pushManager.getSubscription();

        if (subscription) {
          // Unsubscribe from push manager
          await subscription.unsubscribe();

          // Remove subscription from backend
          await axios.delete('/api/push/unsubscribe', {
            data: {
              endpoint: subscription.endpoint,
              keys: {
                p256dh: this.arrayBufferToBase64(subscription.getKey('p256dh')),
                auth: this.arrayBufferToBase64(subscription.getKey('auth')),
              },
            },
          });
        }

        this.is_subscribed = false;
        this.is_loading = false;
        return true;

      } catch (err: any) {
        console.error('Failed to unsubscribe from push notifications:', err);
        this.error = err.response?.data?.detail || 'Failed to unsubscribe from push notifications';
        this.is_loading = false;
        return false;
      }
    },
  },
});
