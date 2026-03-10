import { Plus, MessageSquare, ShieldCheck, Settings, LogOut, MoreVertical, Sun, Moon } from 'lucide-react';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { loginRequest } from '../authConfig';
import { useMsal } from '@azure/msal-react';
import { InteractionRequiredAuthError } from '@azure/msal-browser';
import { motion, AnimatePresence } from 'framer-motion';

interface SidebarProps {
  isCollapsed: boolean;
  onClose?: () => void;
  handleLogout?: () => void;
  account?: any;
  activeThreadId?: string | null;
  setActiveThreadId?: (id: string | null) => void;
}

export default function Sidebar({ isCollapsed, onClose, handleLogout, account, activeThreadId, setActiveThreadId }: SidebarProps) {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [threads, setThreads] = useState<any[]>([]);
  const { instance } = useMsal();

  useEffect(() => {
    const fetchThreads = async () => {
      let authHeaderToken = '';
      try {
        if (account) {
          const tokenResponse = await instance.acquireTokenSilent({
            ...loginRequest,
            account: account
          });
          authHeaderToken = tokenResponse.idToken;
        }
      } catch (err) {
        if (err instanceof InteractionRequiredAuthError) {
          instance.loginRedirect(loginRequest).catch(e => console.error(e));
          return;
        }
        console.error("Failed to acquire token", err);
        return;
      }

      try {
        const response = await axios.get('http://localhost:8000/api/history', {
          headers: { Authorization: `Bearer ${authHeaderToken}` }
        });
        setThreads(response.data.threads || []);
      } catch (err: any) {
        if (err.response?.status === 401) {
          instance.loginRedirect(loginRequest).catch(e => console.error(e));
          return;
        }
        console.error("Failed to fetch threads", err);
      }
    };

    fetchThreads();
  }, [account, instance, activeThreadId]); // re-fetch when activeThreadId changes (e.g. new thread created)

  return (
    <>
      {/* Mobile Overlay */}
      <AnimatePresence>
        {!isCollapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      <motion.div 
        initial={false}
        animate={{ 
          width: isCollapsed ? 0 : 256,
          x: isCollapsed ? -256 : 0,
          opacity: isCollapsed ? 0 : 1
        }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="fixed lg:relative z-50 bg-slate-900 text-slate-300 flex flex-col h-screen border-r border-slate-800 overflow-hidden shrink-0 shadow-2xl lg:shadow-none"
      >
        <div className="w-64 flex flex-col h-full">
          {/* New Chat Button */}
      <div className="p-4 pt-6">
        <button 
          onClick={() => setActiveThreadId?.(null)}
          className="w-full flex items-center gap-2 bg-slate-700 hover:bg-slate-800 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition-colors shadow-sm"
        >
          <Plus size={16} />
          New chat
        </button>
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-6 custom-scrollbar">
        <div>
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Recent Chats</div>
          <div className="space-y-1">
            {threads.map((thread) => (
              <button 
                key={thread.id}
                onClick={() => setActiveThreadId?.(thread.id)}
                className={`group w-full flex items-center justify-between px-3 py-2 rounded-md text-sm transition-colors ${
                  activeThreadId === thread.id 
                    ? 'bg-slate-800 text-white' 
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center gap-3 overflow-hidden">
                  <MessageSquare size={14} className="shrink-0" />
                  <span className="truncate text-left">{thread.title || 'Untitled Chat'}</span>
                </div>
                <div className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-slate-700 rounded-full transition-all shrink-0">
                  <MoreVertical size={14} className="text-slate-400 hover:text-white" />
                </div>
              </button>
            ))}
            {threads.length === 0 && (
              <div className="text-sm text-slate-500 px-3 py-2">No past threads found.</div>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-slate-800 space-y-3">
        <div className="flex items-center justify-between px-3 py-2 rounded-md bg-slate-800/30 border border-slate-800">
          <div className="flex items-center gap-3 text-sm text-slate-400">
            {isDarkMode ? <Moon size={16} /> : <Sun size={16} />}
            <span>{isDarkMode ? 'Dark Mode' : 'Light Mode'}</span>
          </div>
          <button 
            onClick={() => setIsDarkMode(!isDarkMode)}
            className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none ${
              isDarkMode ? 'bg-slate-700' : 'bg-slate-600'
            }`}
          >
            <span
              className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${
                isDarkMode ? 'translate-x-5' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
        <button 
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 transition-colors"
        >
          <LogOut size={16} />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
    </motion.div>
    </>
  );
}
