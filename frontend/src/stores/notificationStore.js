import { create } from 'zustand';
import { notificationsAPI, parseApiError } from '../services/api';

export const useNotificationStore = create((set, get) => ({
  notifications: [],
  unreadCount: 0,
  loading: false,
  error: '',

  fetchNotifications: async () => {
    try {
      set({ loading: true, error: '' });
      const response = await notificationsAPI.list();
      const notifications = response?.data?.notifications || [];
      set({ notifications, loading: false });
      set({ unreadCount: notifications.filter((item) => !item.read).length });
    } catch (error) {
      set({ loading: false, error: parseApiError(error, 'Failed to load notifications.') });
    }
  },

  fetchUnreadCount: async () => {
    try {
      const response = await notificationsAPI.unreadCount();
      set({ unreadCount: Number(response?.data?.unread_count || 0) });
    } catch {
      // Keep silent in polling mode.
    }
  },

  markAsRead: async (notificationId) => {
    await notificationsAPI.markRead(notificationId);
    set((state) => ({
      notifications: state.notifications.map((item) =>
        item.id === notificationId ? { ...item, read: true } : item
      ),
      unreadCount: Math.max(0, state.unreadCount - 1)
    }));
  },

  markAllRead: async () => {
    await notificationsAPI.markAllRead();
    set((state) => ({
      notifications: state.notifications.map((item) => ({ ...item, read: true })),
      unreadCount: 0
    }));
  },

  deleteNotification: async (notificationId) => {
    const target = get().notifications.find((item) => item.id === notificationId);
    await notificationsAPI.delete(notificationId);
    set((state) => ({
      notifications: state.notifications.filter((item) => item.id !== notificationId),
      unreadCount: target && !target.read ? Math.max(0, state.unreadCount - 1) : state.unreadCount
    }));
  }
}));

export default useNotificationStore;
