import { Activity, AlertOctagon, ArrowRight, Database, Server, ShieldAlert } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { Badge, formatDate, PageHeader, Panel, State } from '../components'
import { useApi } from '../hooks'

export default function Overview() {
  const stats = useApi(api.statistics)
  const alerts = useApi(() => api.alerts('?page_size=5'))
  const s = stats.data
  const cards = [
    ['Total events', s?.total_events ?? 0, Database, 'All retained telemetry'],
    ['Events today', s?.events_today ?? 0, Activity, 'Since 00:00 UTC'],
    ['Active alerts', s?.active_alerts ?? 0, ShieldAlert, 'New or investigating'],
    ['Critical alerts', s?.critical_alerts ?? 0, AlertOctagon, 'Immediate attention'],
    ['High alerts', s?.high_alerts ?? 0, ShieldAlert, 'Priority queue'],
    ['Monitored hosts', s?.monitored_hosts ?? 0, Server, 'Observed hostnames'],
  ] as const
  const maxCategory = Math.max(...(s?.categories.map(item => item.count) || [1]))
  const maxVolume = Math.max(...(s?.event_volume.map(item => item.count) || [1]))
  return <div className="page">
    <PageHeader eyebrow="Operations overview" title="Security posture, at a glance" description="Live visibility across normalized events, active detections, and monitored hosts." action={<span className="live-pill"><span/>Live telemetry</span>}/>
    <State loading={stats.loading} error={stats.error}><div className="metric-grid">{cards.map(([label, value, Icon, note]) => <article className="metric" key={label}><div className="metric-top"><span>{label}</span><Icon size={19}/></div><strong>{value.toLocaleString()}</strong><small>{note}</small></article>)}</div></State>
    <div className="overview-grid">
      <Panel title="Event volume" kicker="Last 7 days" className="volume-panel">
        <State loading={stats.loading} error={stats.error} empty={!s?.event_volume.length}><div className="volume-chart" aria-label="Event volume chart">{s?.event_volume.map(item => <div key={item.date} className="volume-col"><span className="volume-value">{item.count}</span><i style={{height: `${Math.max(8, item.count / maxVolume * 100)}%`}}/><small>{new Date(item.date).toLocaleDateString([], {weekday: 'short'})}</small></div>)}</div></State>
      </Panel>
      <Panel title="Alerts by severity" kicker="Current distribution">
        <State loading={stats.loading} error={stats.error} empty={!Object.keys(s?.alerts_by_severity || {}).length}><div className="severity-list">{['critical','high','medium','low','informational'].map(name => <div key={name}><div><Badge value={name}/><strong>{s?.alerts_by_severity[name] || 0}</strong></div><span><i className={`fill-${name}`} style={{width: `${(s?.alerts_by_severity[name] || 0) / Math.max(1, s?.active_alerts || 1) * 100}%`}}/></span></div>)}</div></State>
      </Panel>
      <Panel title="Top event categories" kicker="Normalized telemetry">
        <State loading={stats.loading} error={stats.error} empty={!s?.categories.length}><div className="bar-list">{s?.categories.map(item => <div key={item.name}><label><span>{item.name}</span><strong>{item.count}</strong></label><span><i style={{width: `${item.count / maxCategory * 100}%`}}/></span></div>)}</div></State>
      </Panel>
      <Panel title="Top source IPs" kicker="Most observed sources">
        <State loading={stats.loading} error={stats.error} empty={!s?.top_source_ips.length}><div className="rank-list">{s?.top_source_ips.map((item, index) => <div key={item.name}><span>{String(index + 1).padStart(2, '0')}</span><code>{item.name}</code><strong>{item.count}</strong></div>)}</div></State>
      </Panel>
    </div>
    <Panel title="Latest alerts" kicker="Investigation queue" action={<Link className="text-link" to="/alerts">View all <ArrowRight size={15}/></Link>}>
      <State loading={alerts.loading} error={alerts.error} empty={!alerts.data?.items.length}><div className="alert-feed">{alerts.data?.items.map(alert => <Link to={`/alerts/${alert.id}`} key={alert.id}><span className={`alert-marker marker-${alert.severity}`}/><div><strong>{alert.title}</strong><small>{alert.rule_id} · {alert.affected_host || alert.source_ip || 'Multiple entities'}</small></div><Badge value={alert.severity}/><time>{formatDate(alert.last_seen)}</time><ArrowRight size={17}/></Link>)}</div></State>
    </Panel>
  </div>
}
