import { create } from 'zustand';
import { parseApiError, settingsAPI } from '../services/api';

export const useSettingsStore = create((set) => ({
  profile: null,
  preferences: null,
  notifications: null,
  resume: null,
  loading: false,
  error: '',

  setError: (error) => set({ error }),

  loadSettings: async () => {
    try {
      set({ loading: true, error: '' });
      const [profileRes, prefRes, notifRes, resumeRes] = await Promise.all([
        settingsAPI.getProfile(),
        settingsAPI.getPreferences(),
        settingsAPI.getNotifications(),
        settingsAPI.getResume()
      ]);

      set({
        profile: profileRes?.data || null,
        preferences: prefRes?.data || null,
        notifications: notifRes?.data || null,
        resume: resumeRes?.data || null,
        loading: false,
        error: ''
      });
    } catch (err) {
      set({ loading: false, error: parseApiError(err, 'Failed to load settings.') });
    }
  },

  updateProfile: async (payload) => {
    const response = await settingsAPI.updateProfile(payload);
    set({ profile: response?.data || null });
    return response?.data;
  },

  changePassword: async (payload) => {
    const response = await settingsAPI.changePassword(payload);
    return response?.data;
  },

  updatePreferences: async (payload) => {
    const response = await settingsAPI.updatePreferences(payload);
    set({ preferences: response?.data || null });
    return response?.data;
  },

  uploadResume: async (file) => {
    const response = await settingsAPI.uploadResume(file);
    set({ resume: response?.data || null });
    return response?.data;
  },

  refreshResume: async () => {
    const response = await settingsAPI.getResume();
    set({ resume: response?.data || null });
    return response?.data;
  },

  deleteResume: async () => {
    await settingsAPI.deleteResume();
    set({ resume: { file_name: null, extracted_skills: [], uploaded_at: null } });
  },

  updateNotifications: async (payload) => {
    const response = await settingsAPI.updateNotifications(payload);
    set({ notifications: response?.data || null });
    return response?.data;
  },

  deleteAccount: async () => {
    const response = await settingsAPI.deleteAccount();
    return response?.data;
  }
}));
