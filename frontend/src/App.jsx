import React, { useState, useEffect } from 'react';
import { useMsal, AuthenticatedTemplate, UnauthenticatedTemplate } from '@azure/msal-react';
import { loginRequest } from './authConfig';
import { ShieldCheck } from 'lucide-react';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import './index.css';

function App() {
  const { instance, accounts } = useMsal();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true);
  const [activeThreadId, setActiveThreadId] = useState(null);

  useEffect(() => {
    // On desktop, show sidebar by default
    if (window.innerWidth >= 1024) {
      setIsSidebarCollapsed(false);
    }
  }, []);

  const handleLogin = () => {
    instance.loginRedirect(loginRequest).catch(e => {
      console.error(e);
    });
  };

  const handleLogout = () => {
    instance.logoutRedirect({
      postLogoutRedirectUri: "/",
    });
  };

  return (
    <div className="flex h-screen w-full bg-white font-sans overflow-hidden">
      <UnauthenticatedTemplate>
        <div className="w-full flex items-center justify-center bg-slate-50 relative">
          <div className="absolute inset-0 z-0">
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-50 to-slate-100 opacity-80" />
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob" />
            <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000" />
            <div className="absolute -bottom-8 left-1/2 w-96 h-96 bg-pink-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000" />
          </div>

          <div className="relative z-10 max-w-md w-full p-8 md:p-10 bg-white/70 backdrop-blur-xl rounded-3xl shadow-xl border border-white/40 group overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-white/40 to-white/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            
            <div className="relative flex flex-col items-centertext-center">
              <div className="w-20 h-20 mb-6 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 p-0.5 shadow-lg shadow-indigo-500/20">
                <div className="w-full h-full bg-white rounded-[14px] flex items-center justify-center">
                  <ShieldCheck size={40} className="text-indigo-600" />
                </div>
              </div>

              <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 mb-2">
                compliance<span className="text-indigo-600">.chat</span>
              </h1>
              <p className="text-slate-500 mb-8 font-medium">Enterprise Regulatory Assessment Swarm</p>

              <button 
                onClick={handleLogin}
                className="w-full relative py-3 px-6 rounded-xl font-semibold text-white overflow-hidden group/btn shadow-md hover:shadow-lg transition-all"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-indigo-600 to-purple-600 transition-transform duration-300 group-hover/btn:scale-105" />
                <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-purple-500 opacity-0 group-hover/btn:opacity-100 transition-opacity duration-300" />
                <span className="relative z-10 flex items-center justify-center gap-2">
                  Sign In to Continue
                  <svg className="w-4 h-4 transition-transform group-hover/btn:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </span>
              </button>
            </div>
          </div>
        </div>
      </UnauthenticatedTemplate>

      <AuthenticatedTemplate>
        {/* Pass down mocked methods and state */}
        <Sidebar 
          isCollapsed={isSidebarCollapsed} 
          onClose={() => setIsSidebarCollapsed(true)}
          handleLogout={handleLogout}
          account={accounts[0]}
          activeThreadId={activeThreadId}
          setActiveThreadId={setActiveThreadId}
        />
        <ChatArea 
          isSidebarCollapsed={isSidebarCollapsed} 
          toggleSidebar={() => setIsSidebarCollapsed(!isSidebarCollapsed)} 
          handleLogout={handleLogout}
          account={accounts[0]}
          activeThreadId={activeThreadId}
          setActiveThreadId={setActiveThreadId}
        />
      </AuthenticatedTemplate>
    </div>
  );
}

export default App;
