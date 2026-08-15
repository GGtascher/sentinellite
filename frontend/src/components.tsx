import type { ReactNode } from 'react'
import { AlertTriangle, Database, Menu, Radar, Server, ShieldCheck, Siren, X } from 'lucide-react'
import { NavLink } from 'react-router-dom'

export function Badge({value}: {value: string | null | undefined}) {
  const label = value || 'unknown'
  return <span className={`badge badge-${label.toLowerCase().replace('_', '-')}`}>{label.replace('_', ' ')}</span>
}

export function State({loading, error, empty, children}: {loading?: boolean; error?: string; empty?: boolean; children: ReactNode}) {
  if (loading) return <div className="state"><span className="spinner"/>Loading security data…</div>
  if (error) return <div className="state state-error"><AlertTriangle size={20}/><div><strong>Data unavailable</strong><span>{error}</span></div></div>
  if (empty) return <div className="state"><Database size={22}/><div><strong>No data yet</strong><span>Ingest sample logs or run the demo generator to populate this view.</span></div></div>
  return <>{children}</>
}

export function Panel({title, kicker, action, children, className = ''}: {title: string; kicker?: string; action?: ReactNode; children: ReactNode; className?: string}) {
  return <section className={`panel ${className}`}><header className="panel-head"><div>{kicker && <span className="kicker">{kicker}</span>}<h2>{title}</h2></div>{action}</header>{children}</section>
}

export function PageHeader({eyebrow, title, description, action}: {eyebrow: string; title: string; description: string; action?: ReactNode}) {
  return <header className="page-header"><div><span className="eyebrow"><span/>{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>{action}</header>
}

const nav = [
  ['/', 'Overview', Radar], ['/events', 'Events', Database], ['/alerts', 'Alerts', Siren],
  ['/rules', 'Detection rules', ShieldCheck], ['/hosts', 'Hosts', Server],
] as const

export function Shell({children}: {children: ReactNode}) {
  return <div className="shell">
    <input id="nav-toggle" className="nav-toggle" type="checkbox" aria-label="Toggle navigation"/>
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><ShieldCheck/></div><div><strong>Sentinel<span>Lite</span></strong><small>Security monitoring</small></div></div>
      <nav aria-label="Primary navigation">{nav.map(([path, label, Icon]) => <NavLink key={path} to={path} end={path === '/'}><Icon size={18}/><span>{label}</span></NavLink>)}</nav>
      <div className="system-card"><div><span className="status-dot"/>System operational</div><small>Local processing only</small></div>
      <div className="sidebar-foot"><span>V0.1.0</span><span>DEFENSIVE / LOCAL</span></div>
    </aside>
    <label className="nav-backdrop" htmlFor="nav-toggle"/>
    <main><div className="mobile-bar"><label htmlFor="nav-toggle" aria-label="Open navigation"><Menu/></label><strong>SentinelLite</strong><X className="close-icon"/></div>{children}</main>
  </div>
}

export function formatDate(value: string | null | undefined) {
  if (!value) return 'Timestamp unavailable'
  const parsed = new Date(value)
  return Number.isNaN(parsed.valueOf()) ? value : parsed.toLocaleString([], {dateStyle: 'medium', timeStyle: 'medium'})
}

export function shortId(value: string) { return value.slice(0, 8).toUpperCase() }
