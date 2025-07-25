import { useEffect } from 'react';

/**
 * Hook to listen for project changes and execute a callback
 * @param callback Function to execute when project changes
 * @param deps Dependencies array for the callback
 */
export const useProjectChange = (callback: (project: any) => void, deps: React.DependencyList = []) => {
  useEffect(() => {
    const handleProjectChange = (event: CustomEvent) => {
      callback(event.detail);
    };

    window.addEventListener('projectChanged', handleProjectChange as any);

    return () => {
      window.removeEventListener('projectChanged', handleProjectChange as any);
    };
  }, deps);
};