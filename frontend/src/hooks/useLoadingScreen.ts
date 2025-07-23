import { useState, useEffect } from 'react';

export const useLoadingScreen = (isLoading: boolean) => {
  const [showLoadingScreen, setShowLoadingScreen] = useState(isLoading);
  const [fadeOut, setFadeOut] = useState(false);

  useEffect(() => {
    if (!isLoading && showLoadingScreen) {
      // Start fade out animation
      setFadeOut(true);
      // Remove loading screen after animation
      const timer = setTimeout(() => {
        setShowLoadingScreen(false);
      }, 500); // Match the CSS transition duration
      
      return () => clearTimeout(timer);
    } else if (isLoading) {
      setShowLoadingScreen(true);
      setFadeOut(false);
    }
  }, [isLoading, showLoadingScreen]);

  return { showLoadingScreen, fadeOut };
};