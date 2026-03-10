/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';

export default function App() {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true);

  useEffect(() => {
    // On desktop, show sidebar by default
    if (window.innerWidth >= 1024) {
      setIsSidebarCollapsed(false);
    }
  }, []);

  return (
    <div className="flex h-screen w-full bg-white font-sans overflow-hidden">
      <Sidebar 
        isCollapsed={isSidebarCollapsed} 
        onClose={() => setIsSidebarCollapsed(true)}
      />
      <ChatArea 
        isSidebarCollapsed={isSidebarCollapsed} 
        toggleSidebar={() => setIsSidebarCollapsed(!isSidebarCollapsed)} 
      />
    </div>
  );
}
