import { routeTree } from '@/routeTree.gen';
import { createRouter } from '@tanstack/react-router';

export const router = createRouter({ routeTree });

// Register the router type
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
