import { useState, useRef, useEffect } from 'react';
import { ShieldCheck, FileText, CheckCircle2, AlertTriangle, Paperclip, Send, Info, User, LogOut, Settings as SettingsIcon, Menu, Plus, Mic, Bot } from 'lucide-react';
import { ChatMessage, Source } from '../types';
import { motion } from 'framer-motion';
import axios from 'axios';
import { useMsal } from '@azure/msal-react';
import { loginRequest } from '../authConfig';

interface ChatAreaProps {
  isSidebarCollapsed: boolean;
  toggleSidebar: () => void;
  handleLogout?: () => void;
  account?: any;
  activeThreadId?: string | null;
  setActiveThreadId?: (id: string | null) => void;
}

export default function ChatArea({ isSidebarCollapsed, toggleSidebar, handleLogout, account, activeThreadId, setActiveThreadId }: ChatAreaProps) {
  const initialMessage: ChatMessage = {
    id: '1',
    role: 'assistant',
    content: 'Hello! I am your Global Product Compliance Agent. I have full access to our proprietary database of importation laws, NOMs, and FCC regulations.\n\nHow can I accelerate your product launch today?',
    timestamp: new Date(),
    model: 'gpt-4o'
  };

  const [messages, setMessages] = useState<ChatMessage[]>([initialMessage]);
  const [currentModel, setCurrentModel] = useState<string>('gpt-4o');
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  
  const userMenuRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { instance } = useMsal();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    const fetchHistory = async () => {
      if (!activeThreadId) {
        setMessages([initialMessage]);
        return;
      }

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
        console.error("Failed to acquire token silently", err);
        return;
      }

      try {
        const response = await axios.get(`http://localhost:8000/api/history/${activeThreadId}`, {
          headers: { Authorization: `Bearer ${authHeaderToken}` }
        });
        if (response.data && response.data.messages) {
          const loadedMessages = response.data.messages.map((m: any) => ({
            ...m,
            timestamp: new Date(m.timestamp)
          }));
          setMessages(loadedMessages);
        }
      } catch (err) {
        console.error("Failed to load thread history", err);
      }
    };

    fetchHistory();
  }, [activeThreadId, account, instance]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() && !selectedFile) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      fileAttachment: selectedFile ? selectedFile.name : undefined,
      timestamp: new Date()
    };

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
      console.error("Failed to acquire token silently", err);
    }

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    const formData = new FormData();
    formData.append('message', userMessage.content || '');
    if (activeThreadId) {
      formData.append('thread_id', activeThreadId);
    }
    if (selectedFile) {
      formData.append('file', selectedFile);
    }

    setSelectedFile(null);

    try {
      const response = await axios.post('http://localhost:8000/api/chat', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${authHeaderToken}`
        }
      });

      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.reply,
        timestamp: new Date(),
        model: response.data.model || 'gpt-4o'
      };
      setMessages(prev => [...prev, aiMessage]);
      setCurrentModel(aiMessage.model || 'gpt-4o');

      if (!activeThreadId && response.data.thread_id && setActiveThreadId) {
        setActiveThreadId(response.data.thread_id);
      }
    } catch (error: any) {
      // Very basic handling of 429 quota inside chat stream for now
      if (error.response?.status === 429) {
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: "⚠️ You've reached your daily token limit. Please upgrade your subscription to continue using compliance.chat.",
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      } else {
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: "I'm sorry, I encountered an error while analyzing your request and document. " + (error.response?.data?.detail || error.message),
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-white h-screen">
      {/* Header */}
      <header className="h-12 lg:h-14 border-b border-slate-200 bg-white flex items-center justify-between px-4 lg:px-6 shadow-sm z-10 shrink-0">
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
              <div className="w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center text-slate-700 font-semibold text-xs border border-slate-200">
                <User size={14} />
              </div>
              <div className="hidden sm:flex flex-col items-start">
                <span className="text-xs font-semibold text-slate-700 leading-none">{account?.name || 'User'}</span>
                <span className="text-[10px] text-slate-500 leading-none mt-0.5">Entra ID</span>
              </div>
            </button>

            {isUserMenuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white border border-slate-200 rounded-lg shadow-lg py-1 z-50 animate-in fade-in zoom-in duration-150">
                <div className="px-4 py-2 border-b border-slate-100 mb-1">
                  <p className="text-xs font-semibold text-slate-900">{account?.name || 'User'}</p>
                  <p className="text-[10px] text-slate-500 truncate">{account?.username || 'user@enterprise.com'}</p>
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
      <div className="flex-1 overflow-y-auto px-4 lg:px-6 pt-4 lg:pt-6 pb-4 lg:pb-6 space-y-6 lg:space-y-8 custom-scrollbar">
        {messages.map((msg, index) => (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            key={msg.id} 
            className={`flex gap-3 lg:gap-4 max-w-4xl mx-auto ${msg.role === 'user' ? 'justify-end' : ''}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-white shrink-0 shadow-sm mt-1">
                <ShieldCheck size={18} />
              </div>
            )}
            
            <div className={`flex flex-col gap-2 max-w-[90%] md:max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div className={`px-4 lg:px-5 py-3 lg:py-4 rounded-2xl shadow-sm ${
                msg.role === 'user' 
                  ? 'bg-slate-700 text-white rounded-tr-sm' 
                  : 'bg-white border border-slate-200 text-slate-800 rounded-tl-sm'
              }`}>
                {msg.fileAttachment && (
                  <div className={`flex items-center gap-2 mb-3 text-sm p-2.5 rounded-lg border ${msg.role === 'user' ? 'bg-slate-800/50 border-slate-600 text-slate-200' : 'bg-slate-50 border-slate-200 text-slate-700'}`}>
                    <Paperclip size={14} className={msg.role === 'user' ? 'text-slate-400' : 'text-slate-400'} />
                    <span className="font-medium truncate max-w-[200px]">{msg.fileAttachment}</span>
                  </div>
                )}
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
                    return line ? <p key={i} className="mb-2 min-h-[1rem]">{line}</p> : <div key={i} className="h-4" />;
                  })}
                </div>
              </div>

              {/* RAG Sources & Metadata */}
              {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                <div className="w-full mt-2 space-y-3">
                  <div className="flex items-center gap-4 text-xs">
                    {msg.confidence && (
                      <div className="flex items-center gap-1.5 text-emerald-600 font-medium bg-emerald-50 px-2 py-1 rounded-md border border-emerald-200">
                        <CheckCircle2 size={14} />
                        {msg.confidence === 'high' ? 'High Confidence' : msg.confidence === 'medium' ? 'Medium Confidence' : 'Low Confidence'}
                      </div>
                    )}
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
              <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-slate-600 shrink-0 font-medium text-sm shadow-sm mt-1">
                <User size={16} />
              </div>
            )}
          </motion.div>
        ))}

        {isTyping && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-3 lg:gap-4 max-w-4xl mx-auto"
          >
            <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-white shrink-0 shadow-sm mt-1">
              <Bot size={18} />
            </div>
            <div className="flex flex-col gap-2 items-start">
              <div className="px-5 py-4 rounded-2xl shadow-sm bg-white border border-slate-200 text-slate-800 rounded-tl-sm flex items-center h-[52px]">
                <div className="flex gap-1 items-center">
                  <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                  <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                  <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} className="h-4" />
      </div>

      {/* Input Area */}
      <div className="px-4 lg:px-6 pb-4 lg:pb-6 pt-0 bg-white shrink-0">
        <div className="max-w-4xl mx-auto relative">
          {/* File Upload Preview Bubble */}
          {selectedFile && (
            <div className="absolute -top-12 left-0 right-0 flex justify-center z-10">
              <div className="flex items-center gap-2 bg-slate-800 text-white py-1.5 px-3 rounded-full text-xs shadow-md border border-slate-700 animate-in fade-in slide-in-from-bottom-2 duration-200">
                <FileText size={14} className="text-indigo-400" />
                <span className="truncate max-w-[200px] font-medium">{selectedFile.name}</span>
                <button 
                  type="button" 
                  onClick={removeFile}
                  className="ml-1 text-slate-400 hover:text-white focus:outline-none transition-colors"
                >
                  &times;
                </button>
              </div>
            </div>
          )}

          <div className="relative flex items-end gap-2 bg-[#f0f4f9] rounded-[32px] transition-all p-1.5 focus-within:bg-[#e9eef6] shadow-sm border border-slate-200 z-20">
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              onChange={handleFileSelect}
              accept="application/pdf,image/png,image/jpeg,image/jpg"
            />
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="p-2.5 text-slate-500 hover:text-slate-800 hover:bg-slate-200/50 rounded-full transition-colors shrink-0 mb-0.5 focus:outline-none"
              title="Upload file layout"
            >
              <Plus size={20} />
            </button>
            <textarea
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  if (input.trim() || selectedFile) {
                    handleSubmit();
                  }
                }
              }}
              placeholder="Ask a compliance question or upload a spec sheet..."
              className="w-full max-h-[200px] min-h-[44px] py-2.5 px-2 bg-transparent border-none focus:ring-0 focus:outline-none focus:border-transparent focus:shadow-none resize-none text-slate-800 placeholder:text-slate-500 text-base leading-relaxed custom-scrollbar"
              rows={1}
            />
            <div className="flex items-center gap-1 pr-1 pb-1 shrink-0 mb-0.5">
              {(!input.trim() && !selectedFile) ? (
                <button className="p-2 text-slate-400 cursor-not-allowed rounded-full transition-colors focus:outline-none">
                  <Mic size={20} />
                </button>
              ) : (
                <button 
                  onClick={handleSubmit}
                  className="p-2 text-white bg-indigo-600 hover:bg-indigo-700 rounded-full transition-colors focus:outline-none shadow-md"
                >
                  <Send size={18} className="translate-x-px translate-y-px" />
                </button>
              )}
            </div>
          </div>
          
          {/* Metadata Footer */}
          <div className="flex flex-col sm:flex-row items-center justify-end mt-3 px-2 gap-2 sm:gap-0">
            <div className="flex items-center gap-1.5 text-[10px] text-slate-400 uppercase tracking-wider font-medium">
              {currentModel}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
