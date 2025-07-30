import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import './styles/aicos-theme.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

// Prevent any visibility change handlers from causing reloads
if (typeof document !== 'undefined') {
  const originalAddEventListener = document.addEventListener;
  document.addEventListener = function(type: string, listener: any, options?: any) {
    // Log visibility change listeners for debugging
    if (type === 'visibilitychange') {
      console.log('Visibility change listener blocked:', listener.toString().substring(0, 100));
      return;
    }
    return originalAddEventListener.call(this, type, listener, options);
  };
}

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
