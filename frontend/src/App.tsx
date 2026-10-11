import { useState, useEffect } from 'react'
import './index.css'
import { Sidebar } from './components/Sidebar'
import type { PageId } from './components/Sidebar'
import { OverviewPage } from './pages/OverviewPage'
import { StartTestCallPage } from './pages/StartTestCallPage'
import { ConfigPage } from './pages/ConfigPage'
import { SimulatorPage } from './pages/SimulatorPage'
import { ChecklistPage } from './pages/ChecklistPage'
import { CallLogsPage } from './pages/CallLogsPage'
import { TestingPage } from './pages/TestingPage'
import { healthCheck } from './services/api'

function App() {
  const [activePage, setActivePage] = useState<PageId>('start-call')
  const [backendOnline, setBackendOnline] = useState(false)
  const [selectedCallId, setSelectedCallId] = useState<string | null>(null)

  useEffect(() => {
    healthCheck()
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false))
  }, [])

  const renderPage = () => {
    switch (activePage) {
      case 'overview': return <OverviewPage onNavigate={setActivePage} />
      case 'start-call':
        return (
          <StartTestCallPage
            onNavigateToSimulator={() => setActivePage('simulator')}
            onNavigateToCalls={(callId) => {
              setSelectedCallId(callId || null);
              setActivePage('calls');
            }}
          />
        )
      case 'config': return <ConfigPage />
      case 'simulator': return <SimulatorPage />
      case 'checklist': return <ChecklistPage />
      case 'calls': return <CallLogsPage initialSelectedCallId={selectedCallId} />
      case 'tests': return <TestingPage />
    }
  }


  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
        backendOnline={backendOnline}
      />
      <main className="main-content">
        {renderPage()}
      </main>
    </div>
  )
}

export default App
