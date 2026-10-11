import React from 'react';
import { LayoutDashboard, Settings, MessageSquare, ClipboardList, Phone, FlaskConical, Mic, PhoneCall } from 'lucide-react';

export type PageId = 'overview' | 'start-call' | 'config' | 'simulator' | 'checklist' | 'calls' | 'tests';

interface SidebarProps {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
  backendOnline: boolean;
}

const NAV_ITEMS: { id: PageId; label: string; icon: React.ReactNode; description: string }[] = [
  { id: 'overview', label: 'Overview', icon: <LayoutDashboard size={18} />, description: 'Dashboard & Analytics' },
  { id: 'start-call', label: 'Start Test Call', icon: <PhoneCall size={18} />, description: 'Customer Form & Retell Call' },
  { id: 'simulator', label: 'Simulator', icon: <MessageSquare size={18} />, description: 'Conversation Testing' },
  { id: 'calls', label: 'Call Logs', icon: <Phone size={18} />, description: 'Call History & Transcripts' },
  { id: 'config', label: 'Configuration', icon: <Settings size={18} />, description: 'Agent Settings & Prompt' },
  { id: 'checklist', label: 'Checklist', icon: <ClipboardList size={18} />, description: 'Eligibility Items' },
  { id: 'tests', label: 'Testing Center', icon: <FlaskConical size={18} />, description: 'Automated Test Suite' },
];


export const Sidebar: React.FC<SidebarProps> = ({ activePage, onNavigate, backendOnline }) => {
  const SidebarContent = () => (
    <>
      {/* Logo */}
      <div style={{
        padding: '1.5rem 1.25rem 1rem',
        borderBottom: '1px solid #e2e8f0',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'linear-gradient(135deg, #199473, #27ab83)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>
            <Mic size={18} color="white" />
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#102a43', lineHeight: 1.2 }}>
              Home Credit
            </div>
            <div style={{ fontSize: 11, color: '#627d98', fontWeight: 500 }}>
              LAP Voice Agent
            </div>
          </div>
        </div>
        {/* Backend status */}
        <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{
            width: 7, height: 7, borderRadius: '50%',
            background: backendOnline ? '#10b981' : '#ef4444',
            flexShrink: 0,
          }} />
          <span style={{ fontSize: 11, color: '#627d98' }}>
            {backendOnline ? 'Backend Online' : 'Backend Offline'}
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ padding: '0.75rem 0.75rem', flex: 1 }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', letterSpacing: '0.08em', marginBottom: 8, paddingLeft: 6 }}>
          NAVIGATION
        </div>
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            className={activePage === item.id ? 'nav-item nav-item-active' : 'nav-item nav-item-inactive'}
            onClick={() => onNavigate(item.id)}
          >
            {item.icon}
            <div>
              <div style={{ fontWeight: 500 }}>{item.label}</div>
            </div>
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div style={{
        padding: '1rem 1.25rem',
        borderTop: '1px solid #e2e8f0',
        fontSize: 11, color: '#94a3b8',
      }}>
        <div style={{ fontWeight: 600, marginBottom: 2 }}>Home Credit India</div>
        <div>LAP Qualification v1.0</div>
        <div style={{ marginTop: 4, color: '#cbd5e1' }}>Simulation & Demo Mode</div>
      </div>
    </>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="sidebar" style={{ display: 'none' }} id="desktop-sidebar">
        <SidebarContent />
      </aside>

      {/* Always-visible sidebar for larger screens */}
      <aside
        className="sidebar"
        style={{ position: 'sticky', top: 0, height: '100vh', overflowY: 'auto' }}
      >
        <SidebarContent />
      </aside>
    </>
  );
};
