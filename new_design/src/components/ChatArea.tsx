import { useState, useRef, useEffect } from 'react';
import { ShieldCheck, FileText, CheckCircle2, AlertTriangle, Paperclip, Send, Info, User, LogOut, Settings as SettingsIcon, Menu, Plus, Mic } from 'lucide-react';
import { ChatMessage, Source } from '../types';
import { motion } from 'framer-motion';

const MOCK_MESSAGES: ChatMessage[] = [
  {
    id: '1',
    role: 'user',
    content: 'Can you review our current Data Retention Policy against SOC 2 Type II requirements? Specifically looking at the section on customer data deletion.',
    timestamp: new Date(Date.now() - 1000 * 60 * 5),
  },
  {
    id: '2',
    role: 'assistant',
    content: 'I have reviewed your Data Retention Policy against SOC 2 Type II criteria (specifically CC6.1 and CC6.2 regarding logical access and data disposal).\n\nYour current policy states that customer data is deleted "within 90 days of contract termination." However, SOC 2 requires more specific procedures for verifiable data destruction.\n\n**Key Findings:**\n1. **Missing Verification:** The policy lacks a verifiable process for confirming data destruction (e.g., certificates of destruction from cloud providers).\n2. **Backup Retention:** It does not explicitly address how long customer data remains in encrypted backups after the 90-day active deletion period.\n\n**Recommendation:** Update Section 4.2 to include a requirement for automated deletion logs and specify the maximum retention period for backup archives (typically 30-60 additional days).',
    timestamp: new Date(Date.now() - 1000 * 60 * 4),
    confidence: 'high'
  }
];

interface ChatAreaProps {
  isSidebarCollapsed: boolean;
  toggleSidebar: () => void;
  handleLogout?: () => void;
  account?: any;
}

export default function ChatArea({ isSidebarCollapsed, toggleSidebar, handleLogout, account }: ChatAreaProps) {
  const [input, setInput] = useState('');
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="flex-1 flex flex-col bg-white h-screen">
      {/* Header */}
      <header className="h-12 lg:h-14 border-b border-slate-200 bg-white flex items-center justify-between px-4 lg:px-6 shadow-sm z-10">
        <div className="flex items-center gap-2 lg:gap-4">
          <button 
            onClick={toggleSidebar}
            className="p-1.5 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-md transition-colors"
            title={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <Menu size={18} />
          </button>
          <div className="flex flex-col items-end">
            <span className="font-poppins font-normal text-[#636464] text-xs lg:text-sm leading-none tracking-wide">compliance</span>
            <span className="font-poppins font-black text-[#ec580d] text-xl lg:text-2xl leading-none tracking-tighter mt-0.5">.CHAT</span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 lg:gap-3">
          <div className="relative" ref={userMenuRef}>
            <button 
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center gap-2 p-1 lg:pr-2 rounded-full hover:bg-slate-100 transition-colors border border-transparent hover:border-slate-200"
            >
              <div className="absolute right-0 mt-2 w-48 bg-white border border-slate-200 rounded-lg shadow-lg py-1 z-50 animate-in fade-in zoom-in duration-150">
                <div className="px-4 py-2 border-b border-slate-100 mb-1">
                  <p className="text-xs font-semibold text-slate-900">{account?.name || 'John Doe'}</p>
                  <p className="text-[10px] text-slate-500 truncate">{account?.username || 'john.doe@enterprise.com'}</p>
                </div>
                <button className="w-full flex items-center gap-2 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 transition-colors">
                  <SettingsIcon size={14} />
                  <span>Settings</span>
                </button>
                <button 
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut size={14} />
                  <span>Log out</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto px-4 lg:px-6 pt-4 lg:pt-6 pb-4 lg:pb-6 space-y-6 lg:space-y-8">
        {MOCK_MESSAGES.map((msg, index) => (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.1 }}
            key={msg.id} 
            className={`flex gap-3 lg:gap-4 max-w-4xl mx-auto ${msg.role === 'user' ? 'justify-end' : ''}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-white shrink-0 shadow-sm">
                <ShieldCheck size={18} />
              </div>
            )}
            
            <div className={`flex flex-col gap-2 max-w-[90%] md:max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div className={`px-4 lg:px-5 py-3 lg:py-4 rounded-2xl shadow-sm ${
                msg.role === 'user' 
                  ? 'bg-slate-700 text-white rounded-tr-sm' 
                  : 'bg-white border border-slate-200 text-slate-800 rounded-tl-sm'
              }`}>
                <div className="prose prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-slate-800 prose-pre:text-slate-100">
                  {msg.content.split('\n').map((line, i) => {
                    if (line.startsWith('**') && line.endsWith('**')) {
                      return <strong key={i} className="block mt-4 mb-2 text-slate-900">{line.replace(/\*\*/g, '')}</strong>;
                    }
                    if (line.startsWith('**') && line.includes(':**')) {
                      const [bold, rest] = line.split(':**');
                      return <p key={i} className="mb-2"><strong className="text-slate-900">{bold.replace(/\*\*/g, '')}:</strong>{rest}</p>;
                    }
                    if (line.match(/^\d+\./)) {
                      return <p key={i} className="ml-4 mb-2">{line}</p>;
                    }
                    return line ? <p key={i} className="mb-2">{line}</p> : null;
                  })}
                </div>
              </div>

              {/* RAG Sources & Metadata */}
              {msg.role === 'assistant' && msg.sources && (
                <div className="w-full mt-2 space-y-3">
                  <div className="flex items-center gap-4 text-xs">
                    <div className="flex items-center gap-1.5 text-emerald-600 font-medium bg-emerald-50 px-2 py-1 rounded-md border border-emerald-200">
                      <CheckCircle2 size={14} />
                      High Confidence
                    </div>
                    <div className="text-slate-500 flex items-center gap-1">
                      <FileText size={14} />
                      {msg.sources.length} Sources Cited
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {msg.sources.map((source) => (
                      <div key={source.id} className="bg-white border border-slate-200 rounded-lg p-3 shadow-sm hover:border-slate-300 transition-colors cursor-pointer group">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="p-1.5 bg-slate-50 text-slate-700 rounded">
                              <FileText size={14} />
                            </div>
                            <span className="text-sm font-medium text-slate-700 truncate max-w-[180px]" title={source.title}>
                              {source.title}
                            </span>
                          </div>
                          <span className="text-xs font-medium text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                            {source.relevance}% Match
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed italic border-l-2 border-slate-200 pl-2">
                          "{source.snippet}"
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-slate-600 shrink-0 font-medium text-sm shadow-sm">
                JD
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Input Area */}
      <div className="px-4 lg:px-6 pb-4 lg:pb-6 pt-0 bg-transparent">
        <div className="max-w-4xl mx-auto">
          <div className="relative flex items-end gap-2 bg-[#f0f4f9] rounded-[32px] transition-all p-1.5 focus-within:bg-[#e9eef6] shadow-sm border border-slate-200">
            <button className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-200/50 rounded-full transition-colors shrink-0 mb-0.5 focus:outline-none">
              <Plus size={20} />
            </button>
            <textarea
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
              }}
              placeholder="Ask a compliance question..."
              className="w-full max-h-[200px] min-h-[40px] py-2 px-2 bg-transparent border-none focus:ring-0 focus:outline-none focus:border-transparent focus:shadow-none resize-none text-slate-800 placeholder:text-slate-500 text-base leading-relaxed custom-scrollbar"
              rows={1}
            />
            <div className="flex items-center gap-1 pr-1 pb-0.5 shrink-0 mb-0.5">
              {!input.trim() ? (
                <button className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-200/50 rounded-full transition-colors focus:outline-none">
                  <Mic size={20} />
                </button>
              ) : (
                <button className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-200/50 rounded-full transition-colors focus:outline-none">
                  <Send size={20} className="translate-x-0.5 -translate-y-0.5" />
                </button>
              )}
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row items-center justify-between mt-3 px-2 gap-2 sm:gap-0">
            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-3 lg:gap-4 text-[10px] lg:text-xs text-slate-500">
              <button className="flex items-center gap-1.5 hover:text-slate-700 transition-colors">
                <FileText size={14} />
                <span>Knowledge Base</span>
              </button>
              <span className="hidden sm:inline w-1 h-1 rounded-full bg-slate-300"></span>
              <button className="flex items-center gap-1.5 hover:text-slate-700 transition-colors">
                <ShieldCheck size={14} />
                <span>Strict Mode</span>
              </button>
            </div>
            <div className="flex items-center gap-1.5 text-[10px] text-slate-400 uppercase tracking-wider font-medium">
              <Info size={12} />
              gpt‑5.1
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
