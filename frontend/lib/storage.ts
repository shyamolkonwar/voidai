// Storage utility for Next.js compatibility
export const sessionStorage = {
  getItem: (key: string): string | null => {
    if (typeof window !== 'undefined') {
      return window.sessionStorage.getItem(key);
    }
    return null;
  },
  setItem: (key: string, value: string): void => {
    if (typeof window !== 'undefined') {
      window.sessionStorage.setItem(key, value);
    }
  },
  removeItem: (key: string): void => {
    if (typeof window !== 'undefined') {
      window.sessionStorage.removeItem(key);
    }
  },
};