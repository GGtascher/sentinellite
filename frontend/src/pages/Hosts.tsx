import { Server } from 'lucide-react'
import { api } from '../api'
import { formatDate, PageHeader, Panel, State } from '../components'
import { useApi } from '../hooks'

export default function Hosts() {
  const {data, loading, error} = useApi(api.hosts)
  return <div className="page"><PageHeader eyebrow="Asset observations" title="Discovered hosts" description="Hostnames observed in normalized telemetry. SentinelLite does not perform active network discovery."/><Panel title="Observed inventory" kicker={data ? `${data.length} unique hosts` : 'Loading hosts'}><State loading={loading} error={error} empty={!data?.length}><div className="host-grid">{data?.map(host => <article key={host.hostname}><span><Server size={20}/></span><div><strong>{host.hostname}</strong><small>Last observed {formatDate(host.last_seen)}</small></div><b>{host.event_count.toLocaleString()}<small>events</small></b></article>)}</div></State></Panel></div>
}

