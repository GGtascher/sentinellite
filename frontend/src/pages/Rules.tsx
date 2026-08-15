import { useState } from 'react'
import { api, Rule } from '../api'
import { Badge, PageHeader, Panel, State } from '../components'
import { useApi } from '../hooks'

export default function Rules() {
  const {data, loading, error} = useApi(api.rules); const [selected, setSelected] = useState<Rule | null>(null)
  return <div className="page"><PageHeader eyebrow="Detection content" title="Detection rules" description="Inspect the version-controlled YAML detections currently loaded by SentinelLite."/>
    <Panel title="Loaded rules" kicker={data ? `${data.length} enabled definitions` : 'Loading rules'}><State loading={loading} error={error} empty={!data?.length}><div className="rule-grid">{data?.map(rule => <button key={rule.id} onClick={() => setSelected(rule)} className={selected?.id === rule.id ? 'selected' : ''}><div><code>{rule.id}</code><Badge value={rule.severity}/></div><strong>{rule.title}</strong><p>{rule.description}</p><small>{rule.mitre.technique || 'No ATT&CK technique'} · {rule.threshold ? 'Threshold' : rule.sequence ? 'Sequence' : 'Single event'}</small></button>)}</div></State></Panel>
    {selected && <Panel title={selected.title} kicker={`${selected.id} · rule definition`} action={<Badge value={selected.severity}/>}><pre className="raw-log">{JSON.stringify(selected, null, 2)}</pre></Panel>}
  </div>
}
