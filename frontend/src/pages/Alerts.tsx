import { Link } from 'react-router-dom'
import { api } from '../api'
import { Badge, formatDate, PageHeader, Panel, shortId, State } from '../components'
import { useApi } from '../hooks'

export default function Alerts() {
  const {data, loading, error} = useApi(() => api.alerts())
  return <div className="page"><PageHeader eyebrow="Detection queue" title="Security alerts" description="Prioritize defensive detections, review supporting evidence, and track analyst disposition."/>
    <Panel title="Investigation queue" kicker={data ? `${data.total} detections` : 'Loading detections'}><State loading={loading} error={error} empty={!data?.items.length}><div className="table-wrap"><table><thead><tr><th>Alert</th><th>Detection</th><th>Entity</th><th>Evidence</th><th>Last seen</th><th>Status</th></tr></thead><tbody>{data?.items.map(alert => <tr key={alert.id}><td><Link className="event-id" to={`/alerts/${alert.id}`}>ALT-{shortId(alert.id)}</Link><Badge value={alert.severity}/></td><td><strong>{alert.title}</strong><small>{alert.rule_id}</small></td><td>{alert.affected_host || alert.source_ip || 'Multiple'}<small>{alert.username || 'No user'}</small></td><td>{alert.event_count} event{alert.event_count === 1 ? '' : 's'}</td><td>{formatDate(alert.last_seen)}</td><td><Badge value={alert.status}/></td></tr>)}</tbody></table></div></State></Panel>
  </div>
}
