import { ArrowLeft } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { Badge, formatDate, PageHeader, Panel, shortId, State } from '../components'
import { useApi } from '../hooks'

const hidden = new Set(['raw_event', 'event_metadata', 'id', 'message'])
export default function EventDetail() {
  const {id = ''} = useParams()
  const event = useApi(() => api.event(id), [id])
  const alerts = useApi(() => api.eventAlerts(id), [id])
  const item = event.data
  return <div className="page"><Link to="/events" className="back"><ArrowLeft size={16}/>Back to events</Link><PageHeader eyebrow={item ? `EVT-${shortId(item.id)}` : 'Event investigation'} title={item?.event_type || 'Event details'} description={item?.message || 'Inspect normalized fields, parsing details, raw evidence, and related alerts.'} action={item && <Badge value={item.event_outcome}/>} />
    <State loading={event.loading} error={event.error}>{item && <div className="detail-grid"><div className="detail-main"><Panel title="Normalized fields" kicker="Canonical event model"><dl className="field-grid">{Object.entries(item).filter(([key, value]) => !hidden.has(key) && value !== null && typeof value !== 'object').map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{key.includes('timestamp') || key === 'ingested_at' ? formatDate(String(value)) : String(value)}</dd></div>)}</dl></Panel><Panel title="Raw event" kicker="Original evidence · rendered as text"><pre className="raw-log">{item.raw_event}</pre></Panel></div><aside className="detail-aside"><Panel title="Parser analysis" kicker="Extraction provenance"><div className="confidence"><strong>{Math.round(item.parser_confidence * 100)}%</strong><span><i style={{width: `${item.parser_confidence * 100}%`}}/></span><small>{item.parser_name} · {item.parse_status}</small></div></Panel><Panel title="Related alerts" kicker="Detection context"><State loading={alerts.loading} error={alerts.error} empty={!alerts.data?.length}><div className="related-list">{alerts.data?.map(alert => <Link to={`/alerts/${alert.id}`} key={alert.id}><Badge value={alert.severity}/><strong>{alert.title}</strong><small>{alert.rule_id}</small></Link>)}</div></State></Panel><Panel title="Parser metadata" kicker="Format-specific fields"><pre className="metadata">{JSON.stringify(item.event_metadata, null, 2)}</pre></Panel></aside></div>}</State>
  </div>
}

