export const ROUTE_PATHS = {
  HOME: '/',

  AUTH: {
    LOGIN: '/login',
    SIGNUP: '/signup',
  },

  PROFILE: {
    INDEX: '/profile',
    SETTINGS: '/profile/settings',
  },

  ADMIN: {
    INDEX: '/admin',
    DASHBOARD: '/admin/dashboard',
    USERS: '/admin/users',
    SESSIONS: '/admin/sessions',
    SETTINGS: '/admin/settings',
  },
} as const;

export type AppRoutePath =
  | typeof ROUTE_PATHS.HOME
  | (typeof ROUTE_PATHS.AUTH)[keyof typeof ROUTE_PATHS.AUTH]
  | (typeof ROUTE_PATHS.PROFILE)[keyof typeof ROUTE_PATHS.PROFILE]
  | (typeof ROUTE_PATHS.ADMIN)[keyof typeof ROUTE_PATHS.ADMIN];
