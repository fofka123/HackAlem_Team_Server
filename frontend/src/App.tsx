import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  Boxes,
  CheckCircle2,
  CircleAlert,
  Code2,
  Database,
  ExternalLink,
  GitBranch,
  LayoutDashboard,
  Network,
  RefreshCw,
  Server,
  ShieldCheck,
  TerminalSquare,
  Users,
} from 'lucide-react'

type ComponentState = 'ok' | 'error' | 'unknown'
type Page = 'overview' | 'services' | 'deployments' | 'logs'

type ReadyResponse = {
  status: string
  components: Record<string, ComponentState>
  time: string
}

type RuntimeEvent = {
  id: number
  time: string
  message: string
  tone: 'ok' | 'error' | 'info'
}

const initialComponents: Record<string, ComponentState> = {
  frontend: 'ok',
  backend: 'unknown',
  postgres: 'unknown',
  redis: 'unknown',
}

const pageMeta: Record<Page, { eyebrow: string; title: string; subtitle: string }> = {
  overview: {
    eyebrow: 'SHARED DEVELOPMENT ENVIRONMENT',
    title: 'Team infrastructure',
    subtitle: 'Frontend, backend and data services run independently.',
  },
  services: {
    eyebrow: 'SERVICE CONTROL',
    title: 'Services',
    subtitle: 'Live health of the components that make up the HackAlem environment.',
  },
  deployments: {
    eyebrow: 'DELIVERY WORKFLOW',
    title: 'Deployments',
    subtitle: 'A simple dev → main workflow keeps the demo version stable.',
  },
  logs: {
    eyebrow: 'RUNTIME VISIBILITY',
    title: 'Logs & diagnostics',
    subtitle: 'Quick runtime events here, full container logs through Portainer.',
  },
}

function StatusDot({ state }: { state: ComponentState }) {
  const label = state === 'ok' ? 'Online' : state === 'error' ? 'Error' : 'Checking'
  return (
    <span className={`status status--${state}`}>
      <span className="status__dot" />
      {label}
    </span>
  )
}

function ServiceCard({
  title,
  subtitle,
  state,
  icon,
  detail,
}: {
  title: string
  subtitle: string
  state: ComponentState
  icon: React.ReactNode
  detail?: string
}) {
  return (
    <article className="service-card">
      <div className="service-card__top">
        <div className="service-card__icon">{icon}</div>
        <StatusDot state={state} />
      </div>
      <h3>{title}</h3>
      <p>{subtitle}</p>
      {detail && <span className="service-card__detail">{detail}</span>}
    </article>
  )
}

function OpenButton({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <button
      className="secondary-button"
      onClick={() => window.open(href, '_blank', 'noopener,noreferrer')}
      type="button"
    >
      {children}
      <ExternalLink size={15} />
    </button>
  )
}

export default function App() {
  const [activePage, setActivePage] = useState<Page>('overview')
  const [components, setComponents] = useState(initialComponents)
  const [updatedAt, setUpdatedAt] = useState('—')
  const [loading, setLoading] = useState(false)
  const [events, setEvents] = useState<RuntimeEvent[]>([
    {
      id: Date.now(),
      time: new Date().toLocaleTimeString(),
      message: 'Team Console started.',
      tone: 'info',
    },
  ])

  const appendEvent = (message: string, tone: RuntimeEvent['tone']) => {
    setEvents((current) =>
      [
        {
          id: Date.now() + Math.floor(Math.random() * 1000),
          time: new Date().toLocaleTimeString(),
          message,
          tone,
        },
        ...current,
      ].slice(0, 40),
    )
  }

  const refresh = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/ready', { cache: 'no-store' })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const data: ReadyResponse = await response.json()
      const next = {
        frontend: 'ok' as ComponentState,
        backend: data.components?.backend ?? 'error',
        postgres: data.components?.postgres ?? 'error',
        redis: data.components?.redis ?? 'error',
      }

      setComponents(next)
      setUpdatedAt(new Date(data.time).toLocaleTimeString())

      const failures = Object.entries(next)
        .filter(([, state]) => state === 'error')
        .map(([name]) => name)

      appendEvent(
        failures.length === 0
          ? 'Health check passed: all services are online.'
          : `Health check reported errors: ${failures.join(', ')}.`,
        failures.length === 0 ? 'ok' : 'error',
      )
    } catch (error) {
      setComponents((prev) => ({
        ...prev,
        backend: 'error',
        postgres: 'unknown',
        redis: 'unknown',
      }))
      setUpdatedAt(new Date().toLocaleTimeString())
      appendEvent(
        `Health request failed: ${error instanceof Error ? error.message : 'unknown error'}.`,
        'error',
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
    const timer = window.setInterval(refresh, 15000)
    return () => window.clearInterval(timer)
  }, [])

  const healthy = useMemo(
    () => Object.values(components).filter((state) => state === 'ok').length,
    [components],
  )

  const meta = pageMeta[activePage]

  const navItem = (page: Page, icon: React.ReactNode, label: string) => (
    <button
      className={`nav__item ${activePage === page ? 'nav__item--active' : ''}`}
      onClick={() => setActivePage(page)}
      type="button"
    >
      {icon}
      {label}
    </button>
  )

  const overview = (
    <>
      <section className="summary-grid">
        <div className="summary-card"><div className="summary-card__icon"><Activity size={19} /></div><div><span>Healthy services</span><strong>{healthy}/4</strong></div></div>
        <div className="summary-card"><div className="summary-card__icon"><Users size={19} /></div><div><span>Team workflow</span><strong>3 developers</strong></div></div>
        <div className="summary-card"><div className="summary-card__icon"><GitBranch size={19} /></div><div><span>Recommended branch</span><strong>dev</strong></div></div>
        <div className="summary-card"><div className="summary-card__icon"><CheckCircle2 size={19} /></div><div><span>Last check</span><strong>{updatedAt}</strong></div></div>
      </section>

      <section className="section">
        <div className="section__heading"><div><h2>Service isolation</h2><p>One broken component does not need to bring down the whole project.</p></div></div>
        <div className="services-grid">
          <ServiceCard title="Frontend" subtitle="React + Vite UI" state={components.frontend} icon={<Code2 size={21} />} />
          <ServiceCard title="Backend" subtitle="FastAPI application API" state={components.backend} icon={<Server size={21} />} />
          <ServiceCard title="PostgreSQL" subtitle="Persistent project data" state={components.postgres} icon={<Database size={21} />} />
          <ServiceCard title="Redis" subtitle="Cache, queues and temporary state" state={components.redis} icon={<Activity size={21} />} />
        </div>
      </section>

      <section className="section split">
        <article className="panel">
          <div className="panel__title"><GitBranch size={19} /><div><h2>Git workflow</h2><p>Parallel work without sending files through messengers.</p></div></div>
          <div className="flow"><span>feature/*</span><i>→</i><span>dev</span><i>→</i><span>main</span><i>→</i><span>demo</span></div>
        </article>
        <article className="panel">
          <div className="panel__title"><CircleAlert size={19} /><div><h2>Failure behaviour</h2><p>Health checks make failures visible instead of hiding them.</p></div></div>
          <ul className="clean-list">
            <li><CheckCircle2 size={16} /> Frontend can fail while API stays alive.</li>
            <li><CheckCircle2 size={16} /> Backend has its own health endpoint.</li>
            <li><CheckCircle2 size={16} /> Database and Redis are isolated internally.</li>
          </ul>
        </article>
      </section>
    </>
  )

  const services = (
    <>
      <section className="services-grid services-grid--large">
        <ServiceCard title="Frontend" subtitle="React + Vite" state={components.frontend} detail="Served through the Caddy gateway" icon={<Code2 size={21} />} />
        <ServiceCard title="Backend" subtitle="FastAPI" state={components.backend} detail="/api/health · /api/ready" icon={<Server size={21} />} />
        <ServiceCard title="PostgreSQL" subtitle="Primary database" state={components.postgres} detail="Internal Docker network only" icon={<Database size={21} />} />
        <ServiceCard title="Redis" subtitle="Cache / temporary state" state={components.redis} detail="Internal Docker network only" icon={<Activity size={21} />} />
      </section>

      <section className="section split">
        <article className="panel">
          <div className="panel__title"><Network size={19} /><div><h2>Health endpoints</h2><p>Direct checks for debugging the shared environment.</p></div></div>
          <div className="action-row">
            <OpenButton href="/api/health">Backend health</OpenButton>
            <OpenButton href="/api/ready">Readiness</OpenButton>
          </div>
        </article>
        <article className="panel">
          <div className="panel__title"><ShieldCheck size={19} /><div><h2>Administration</h2><p>Management interfaces stay bound to localhost.</p></div></div>
          <div className="action-row">
            <OpenButton href="https://127.0.0.1:9443">Portainer</OpenButton>
            <OpenButton href="http://127.0.0.1:3001">Uptime Kuma</OpenButton>
          </div>
        </article>
      </section>
    </>
  )

  const deployments = (
    <>
      <section className="deployment-grid">
        <article className="deployment-card deployment-card--dev">
          <div className="deployment-card__head">
            <div><span className="environment-badge">DEV</span><h2>Integration environment</h2></div>
            <StatusDot state={healthy === 4 ? 'ok' : 'error'} />
          </div>
          <p>Feature branches merge here first. This is where the team integrates and tests changes.</p>
          <div className="deployment-meta">
            <span>Branch</span><strong>dev</strong>
            <span>Mode</span><strong>Docker + hot reload</strong>
            <span>URL</span><strong>127.0.0.1:8080</strong>
          </div>
        </article>

        <article className="deployment-card">
          <div className="deployment-card__head">
            <div><span className="environment-badge environment-badge--prod">MAIN</span><h2>Stable demo version</h2></div>
            <span className="status status--unknown"><span className="status__dot" />Manual promote</span>
          </div>
          <p>Only tested changes should be merged into main before the jury demo.</p>
          <div className="deployment-meta">
            <span>Branch</span><strong>main</strong>
            <span>Rule</span><strong>PR from dev</strong>
            <span>Purpose</span><strong>Demo / release</strong>
          </div>
        </article>
      </section>

      <section className="section panel">
        <div className="panel__title"><GitBranch size={19} /><div><h2>Recommended flow</h2><p>Each teammate works independently without replacing each other's files.</p></div></div>
        <div className="flow flow--large">
          <span>feature/frontend-*</span><i>→</i>
          <span>feature/backend-*</span><i>→</i>
          <span>feature/ai-*</span><i>→</i>
          <span>dev</span><i>→</i>
          <span>main</span>
        </div>
      </section>
    </>
  )

  const logs = (
    <section className="section split">
      <article className="panel">
        <div className="panel__title"><TerminalSquare size={19} /><div><h2>Runtime events</h2><p>Health-check events generated by this Team Console.</p></div></div>
        <div className="event-log">
          {events.map((event) => (
            <div className={`event-row event-row--${event.tone}`} key={event.id}>
              <span className="event-time">{event.time}</span>
              <span className="event-message">{event.message}</span>
            </div>
          ))}
        </div>
      </article>

      <article className="panel">
        <div className="panel__title"><Server size={19} /><div><h2>Full container logs</h2><p>Use Portainer for stdout/stderr from each Docker container.</p></div></div>
        <div className="diagnostic-stack">
          <OpenButton href="https://127.0.0.1:9443">Open Portainer</OpenButton>
          <OpenButton href="http://127.0.0.1:3001">Open Uptime Kuma</OpenButton>
          <button className="secondary-button" onClick={refresh} disabled={loading} type="button">
            <RefreshCw size={15} className={loading ? 'spin' : ''} />
            Run health check
          </button>
        </div>
        <div className="hint-box">
          Terminal shortcut:
          <code>./scripts/logs.sh backend</code>
        </div>
      </article>
    </section>
  )

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand__mark"><Network size={20} /></div>
          <div><strong>HackAlem</strong><span>Team Console</span></div>
        </div>

        <nav className="nav">
          {navItem('overview', <LayoutDashboard size={18} />, 'Overview')}
          {navItem('services', <Boxes size={18} />, 'Services')}
          {navItem('deployments', <GitBranch size={18} />, 'Deployments')}
          {navItem('logs', <TerminalSquare size={18} />, 'Logs')}
        </nav>

        <div className="sidebar__quick">
          <button type="button" onClick={() => window.open('https://127.0.0.1:9443', '_blank')}><Server size={16} />Portainer</button>
          <button type="button" onClick={() => window.open('http://127.0.0.1:3001', '_blank')}><Activity size={16} />Uptime Kuma</button>
        </div>

        <div className="sidebar__security">
          <ShieldCheck size={18} />
          <div><strong>Private by default</strong><span>Admin tools stay on localhost</span></div>
        </div>
      </aside>

      <main className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">{meta.eyebrow}</p>
            <h1>{meta.title}</h1>
            <p className="muted">{meta.subtitle}</p>
          </div>
          <button className="primary-button" onClick={refresh} disabled={loading} type="button">
            <RefreshCw size={17} className={loading ? 'spin' : ''} /> Refresh
          </button>
        </header>

        {activePage === 'overview' && overview}
        {activePage === 'services' && services}
        {activePage === 'deployments' && deployments}
        {activePage === 'logs' && logs}
      </main>
    </div>
  )
}
