import React from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'
import { MsalProvider } from '@azure/msal-react'
import { msalInstance } from './authConfig'

// Initialize the MSAL instance before rendering
msalInstance.initialize().then(() => {
  // Required in React apps using redirects to catch the response code
  msalInstance.handleRedirectPromise().then((response) => {
    if (response) {
      console.log("Redirect sign-in successful:", response);
    }
  }).catch((e) => {
    console.error("Redirect sign-in error:", e);
  });

  const container = document.getElementById('root');
  const root = createRoot(container);

  root.render(
    <React.StrictMode>
      <MsalProvider instance={msalInstance}>
        <App />
      </MsalProvider>
    </React.StrictMode>
  );
});
