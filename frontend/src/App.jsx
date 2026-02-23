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
  Globe
} from 'lucide-react';
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
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      // Connect to FastAPI Backend
      const response = await axios.post('http://localhost:8000/api/chat', {
        message: userMessage.content
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
        content: "I'm sorry, I'm having trouble connecting to the Semantic Kernel Swarm right now. Please check if the backend is running.",
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar glass-panel">
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
          <button className="glass-button icon-button">
            <Settings size={20} />
          </button>
          <div className="user-profile">
            <div className="avatar">
              <User size={16} />
            </div>
            <div className="user-info">
              <span className="user-name">CAM Clarke</span>
              <span className="user-role">Hardware Engineer</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="main-content">
        <header className="chat-header glass-panel">
          <div className="header-title">
            <h2>Regulatory Assessment</h2>
            <div className="status-indicator">
              <span className="status-dot"></span>
              <span className="status-text">Swarm Ready</span>
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
                    {/* Hacky markdown renderer for the proof of concept frontend phase */}
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
          <form className="input-form glass-panel" onSubmit={handleSubmit}>
            <button type="button" className="attachment-btn" title="Upload Specs (PDF/Image)">
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
              className={`send-button ${input.trim() ? 'active' : ''}`}
              disabled={!input.trim()}
            >
              <Send size={18} />
            </button>
          </form>
          <div className="input-footer">
            compliance.chat can make mistakes. Verify critical regulatory assertions with official documentation.
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
