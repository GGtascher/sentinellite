import { Search } from 'lucide-react'
import { FormEvent, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { Badge, formatDate, PageHeader, Panel, shortId, State } from '../components'
import { useApi } from '../hooks'

export default function Events() {
  const [query, setQuery] = useState('')
  const [draft, setDraft] = useState('')
  const {data, loading, error} = useApi(() => api.events(query), [query])
  function search(event: FormEvent) { event.preventDefault(); setQuery(draft ? `?source_ip=${encodeURIComponent(draft)}` : '') }
  return <div className="page"><PageHeader eyebrow="Telemetry explorer" title="Normalized events" description="Search retained telemetry and open any event to compare its normalized and raw representation."/>
    <Panel title="Event stream" kicker={data ? `${data.total.toLocaleString()} events retained` : 'Loading inventory'} action={<form className="search" onSubmit={search}><Search size={16}/><input aria-label="Filter by source IP" value={draft} onChange={e => setDraft(e.target.value)} placeholder="Filter by source IP"/></form>}>
      <State loading={loading} error={error} empty={!data?.items.length}><div className="table-wrap"><table><thead><tr><th>Event</th><th>Timestamp</th><th>Type</th><th>Source</th><th>Host / user</th><th>Parser</th><th>Outcome</th></tr></thead><tbody>{data?.items.map(event => <tr key={event.id}><td><Link className="event-id" to={`/events/${event.id}`}>EVT-{shortId(event.id)}</Link></td><td>{formatDate(event.event_timestamp || event.ingested_at)}</td><td><strong>{event.event_type || 'unclassified'}</strong><small>{event.event_category || 'unknown category'}</small></td><td><code>{event.source_ip || '—'}</code></td><td>{event.hostname || '—'}<small>{event.username || 'No user'}</small></td><td>{event.parser_name}</td><td><Badge value={event.event_outcome}/></td></tr>)}</tbody></table></div></State>
    </Panel></div>
}
