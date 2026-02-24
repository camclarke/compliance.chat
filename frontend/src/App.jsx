import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldCheck,
  Send,
  Paperclip,
  Bot,
  User,
  Settings,
  Menu,
  FileText,
  AlertTriangle,
  Globe,
  LogOut
} from 'lucide-react';
import { useMsal, AuthenticatedTemplate, UnauthenticatedTemplate } from '@azure/msal-react';
import { loginRequest } from './authConfig';
import './App.css';

function App() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: 'Hello! I am your Global Product Compliance Agent. I have full access to our proprietary database of importation laws, NOMs, and FCC regulations.\n\nHow can I accelerate your product launch today?',
      timestamp: new Date().toISOString()
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const { instance, accounts } = useMsal();
  const activeAccount = accounts[0];

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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() && !selectedFile) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: input,
      fileAttachment: selectedFile ? selectedFile.name : null,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    // Create form data to support file uploads
    const formData = new FormData();
    formData.append('message', userMessage.content || '');
    if (selectedFile) {
      formData.append('file', selectedFile);
    }

    // Clear the selected file immediately after showing it in UI
    const fileToUpload = selectedFile;
    setSelectedFile(null);

    try {
      const response = await axios.post('http://localhost:8000/api/chat', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      const aiMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.reply,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: "I'm sorry, I encountered an error while analyzing your request and document. " + (error.response?.data?.detail || error.message),
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="app-container">
      <UnauthenticatedTemplate>
        <div className="login-screen">
          <div className="login-card glass-panel">
            <div className="logo-icon animate-pulse-glow" style={{ marginBottom: '1rem', width: '64px', height: '64px' }}>
              <ShieldCheck size={40} color="#6366f1" />
            </div>
            <h1>compliance.chat</h1>
            <p>Enterprise Regulatory Assessment Swarm</p>
            <button className="login-button" onClick={handleLogin}>
              Sign In to Continue
            </button>
          </div>
        </div>
      </UnauthenticatedTemplate>

      <AuthenticatedTemplate>
        {/* Mobile Sidebar Overlay */}
        {isSidebarOpen && (
          <div className="sidebar-overlay" onClick={() => setIsSidebarOpen(false)}></div>
        )}

        {/* Sidebar */}
        <aside className={`sidebar glass-panel ${isSidebarOpen ? 'open' : ''}`}>
          <div className="sidebar-header">
            <div className="logo-container">
              <div className="logo-icon animate-pulse-glow">
                <ShieldCheck size={24} color="#6366f1" />
              </div>
              <h1 className="logo-text">compliance.chat</h1>
            </div>
          </div>

          <div className="sidebar-content">
            <h3 className="nav-section-title">Active Swarm</h3>
            <nav className="nav-list">
              <a href="#" className="nav-item active">
                <Bot size={18} />
                <span>Assessor Agent</span>
              </a>
              <a href="#" className="nav-item">
                <FileText size={18} />
                <span>RAG Database</span>
                <span className="badge">1.5k Chunks</span>
              </a>
              <a href="#" className="nav-item">
                <Globe size={18} />
                <span>Web Crawler</span>
                <span className="badge-live">Live</span>
              </a>
            </nav>
          </div>

          <div className="sidebar-footer">
            <button className="glass-button icon-button" onClick={handleLogout} title="Sign Out">
              <LogOut size={20} />
            </button>
            <div className="user-profile">
              <div className="avatar">
                <User size={16} />
              </div>
              <div className="user-info">
                <span className="user-name">{activeAccount?.name || 'Engineer'}</span>
                <span className="user-role">{activeAccount?.username || 'user'}</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Chat Area */}
        <main className="main-content">
          <header className="chat-header glass-panel">
            <div className="header-title">
              <button
                className="mobile-menu-btn glass-button icon-button"
                onClick={() => setIsSidebarOpen(true)}
              >
                <Menu size={20} />
              </button>
              <div className="header-text-group">
                <h2>Regulatory Assessment</h2>
                <div className="status-indicator">
                  <span className="status-dot"></span>
                  <span className="status-text">Swarm Ready</span>
                </div>
              </div>
            </div>
            <button className="glass-button outline-button">
              <AlertTriangle size={16} />
              New Assessment
            </button>
          </header>

          <div className="chat-scroll-area">
            <div className="messages-container">
              <AnimatePresence>
                {messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
                    className={`message-wrapper ${msg.role === 'user' ? 'message-user' : 'message-ai'}`}
                  >
                    <div className="message-avatar">
                      {msg.role === 'user' ? <User size={16} /> : <ShieldCheck size={18} color="#fff" />}
                    </div>
                    <div className={`message-bubble ${msg.role === 'user' ? 'bubble-user' : 'bubble-ai glass-panel'}`}>
                      {msg.fileAttachment && (
                        <div className="message-attachment">
                          <Paperclip size={14} />
                          <span>{msg.fileAttachment}</span>
                        </div>
                      )}
                      <div className="prose">
                        {msg.content.split('\n').map((line, i) => (
                          <p key={i}>{line}</p>
                        ))}
                      </div>
                      <div className="message-timestamp">
                        {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {isTyping && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="message-wrapper message-ai"
                >
                  <div className="message-avatar">
                    <Bot size={18} color="#fff" />
                  </div>
                  <div className="message-bubble bubble-ai glass-panel typing-indicator">
                    <span className="dot"></span>
                    <span className="dot"></span>
                    <span className="dot"></span>
                  </div>
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          <div className="chat-input-area">
            {selectedFile && (
              <div className="file-preview-pill">
                <FileText size={14} />
                <span className="file-name">{selectedFile.name}</span>
                <button type="button" className="remove-file-btn" onClick={removeFile}>&times;</button>
              </div>
            )}
            <form className="input-form glass-panel" onSubmit={handleSubmit}>
              <input
                type="file"
                ref={fileInputRef}
                style={{ display: 'none' }}
                onChange={handleFileSelect}
                accept="application/pdf,image/png,image/jpeg,image/jpg"
              />
              <button
                type="button"
                className="attachment-btn"
                title="Upload Specs (PDF/Image)"
                onClick={() => fileInputRef.current?.click()}
              >
                <Paperclip size={20} />
              </button>
              <textarea
                className="chat-textarea"
                placeholder="Ask about FCC, NOMs, CE requirements, or drop a spec sheet here..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                rows={1}
              />
              <button
                type="submit"
                className={`send-button ${(input.trim() || selectedFile) ? 'active' : ''}`}
                disabled={!input.trim() && !selectedFile}
              >
                <Send size={18} />
              </button>
            </form>
            <div className="input-footer">
              compliance.chat can make mistakes. Verify critical regulatory assertions with official documentation.
            </div>
          </div>
        </main>
      </AuthenticatedTemplate>
    </div>
  );
}

export default App;
