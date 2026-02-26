import { create } from 'zustand';

export const useIntelligenceStore = create((set) => ({
  intelligence: null,
  lastUpdatedAt: null,
  setIntelligence: (payload) =>
    set({
      intelligence: payload || null,
      lastUpdatedAt: Date.now()
    }),
  clearIntelligence: () =>
    set({
      intelligence: null,
      lastUpdatedAt: null
    })
}));
