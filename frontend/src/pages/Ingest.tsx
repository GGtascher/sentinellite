import { BookOpen, CheckCircle2, FileUp, RefreshCw, Send, TerminalSquare } from 'lucide-react'
import { FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type EventSummary, type IngestionResult } from '../api'
import { Badge, formatDate, PageHeader, Panel, shortId, State } from '../components'

const samples = [
  {
    name: 'Linux SSH',
    format: 'Syslog / auth.log',
    value: 'Aug 15 14:31:11 server01 sshd[1234]: Failed password for root from 10.0.0.5 port 55422 ssh2',
  },
  {
    name: 'Windows event',
    format: 'JSON / Sysmon',
    value: JSON.stringify({EventID: 4625, Computer: 'win-lab-01', user: 'alice', src_ip: '10.20.30.40', message: 'Failed interactive logon'}, null, 2),
  },
  {
    name: 'Firewall',
    format: 'key=value',
    value: 'src_ip=192.168.1.12 dst_ip=192.168.1.20 dst_port=443 protocol=tcp action=blocked severity=high',
  },
  {
    name: 'Web access',
    format: 'Apache / Nginx',
    value: '203.0.113.55 - - [15/Aug/2026:14:00:01 +0000] "POST /login HTTP/1.1" 401 382',
  },
  {
    name: 'Generic JSON',
    format: 'Canonical fields',
    value: JSON.stringify({timestamp: new Date().toISOString(), host: 'app-lab', event_type: 'application_health', severity: 'informational', message: 'Application health check completed'}, null, 2),
  },
  {
    name: 'Unknown / raw',
    format: 'Any UTF-8 text',
    value: 'sensor::zephyr / node=alpha / signal nominal / observer 10.10.9.7',
  },
]

const fieldHelp = [
  ['Time', 'timestamp, time, @timestamp'],
  ['Host', 'host, hostname, computer'],
  ['Network', 'src_ip, dst_ip, src_port, dst_port'],
  ['Identity', 'user, username, account'],
  ['Event', 'event_type, action, result, severity'],
  ['Process', 'process, image, parentimage, commandline'],
]

export default function Ingest() {
  const [text, setText] = useState(samples[0].value)
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<IngestionResult | null>(null)
  const [history, setHistory] = useState<EventSummary[]>([])
  const [historyLoading, setHistoryLoading] = useState(true)
  const [historyError, setHistoryError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')

  async function loadHistory() {
    setHistoryLoading(true); setHistoryError('')
    try {
      const page = await api.events('?source_type=workbench&page=1&page_size=25')
      setHistory(page.items)
    } catch (reason) {
      setHistoryError(reason instanceof Error ? reason.message : 'Unable to load submission journal')
    } finally { setHistoryLoading(false) }
  }

  useEffect(() => { void loadHistory() }, [])

  async function submitText(event: FormEvent) {
    event.preventDefault()
    if (!text.trim()) { setSubmitError('Paste at least one log record.'); return }
    setSubmitting(true); setSubmitError(''); setResult(null)
    try {
      setResult(await api.ingestText(text))
      await loadHistory()
    } catch (reason) {
      setSubmitError(reason instanceof Error ? reason.message : 'Log submission failed')
    } finally { setSubmitting(false) }
  }

  async function submitFile() {
    if (!file) { setSubmitError('Choose a supported UTF-8 text file first.'); return }
    setSubmitting(true); setSubmitError(''); setResult(null)
    try {
      setResult(await api.ingestFile(file))
      await loadHistory()
    } catch (reason) {
      setSubmitError(reason instanceof Error ? reason.message : 'File upload failed')
    } finally { setSubmitting(false) }
  }

  return <div className="page ingest-page">
    <PageHeader eyebrow="Local ingestion workbench" title="Add and verify logs" description="Paste security logs or upload a UTF-8 text file. Recognized formats are normalized automatically; unknown formats are safely retained as raw evidence." action={<span className="live-pill"><span/>No log execution</span>}/>

    <div className="ingest-layout">
      <div>
        <Panel title="Paste logs" kicker="One log, many lines, or a JSON array">
          <form onSubmit={submitText} className="ingest-form">
            <label htmlFor="log-input">Log content</label>
            <textarea id="log-input" value={text} onChange={event => setText(event.target.value)} rows={13} spellCheck={false} placeholder="Paste one log per line, a JSON object, or a JSON array…"/>
            <div className="ingest-actions"><button className="button" type="submit" disabled={submitting}><Send size={15}/>{submitting ? 'Submitting…' : 'Submit and analyze'}</button><small>Maximum 5,000 events per batch · 256 KiB per event</small></div>
          </form>
        </Panel>

        <Panel title="Upload a log file" kicker="UTF-8 text only">
          <div className="upload-row"><label className="file-picker"><FileUp size={18}/><span>{file ? file.name : 'Choose .txt, .log, .json, .jsonl, .ndjson, .csv, or .tsv'}</span><input type="file" accept=".txt,.log,.json,.jsonl,.ndjson,.csv,.tsv" onChange={event => setFile(event.target.files?.[0] || null)}/></label><button type="button" className="button button-secondary" disabled={submitting || !file} onClick={() => void submitFile()}>Upload and analyze</button></div>
        </Panel>

        {(result || submitError) && <Panel title={submitError ? 'Submission failed' : 'Submission complete'} kicker="Parser result" className={submitError ? 'result-error' : 'result-success'}>
          {submitError ? <div className="inline-error">{submitError}</div> : result && <><div className="result-grid"><div><strong>{result.total_submitted}</strong><span>Submitted</span></div><div><strong>{result.successfully_parsed}</strong><span>Parsed</span></div><div><strong>{result.partially_parsed}</strong><span>Partial</span></div><div><strong>{result.raw_fallback}</strong><span>Raw fallback</span></div><div><strong>{result.rejected}</strong><span>Rejected</span></div></div>{result.messages.map(message => <p className="result-message" key={message}>{message}</p>)}</>}
        </Panel>}
      </div>

      <aside>
        <Panel title="Supported input" kicker="Quick format guide">
          <div className="format-list">{samples.map(sample => <button type="button" key={sample.name} onClick={() => setText(sample.value)}><TerminalSquare size={16}/><span><strong>{sample.name}</strong><small>{sample.format}</small></span><b>Use example</b></button>)}</div>
          <p className="format-note"><BookOpen size={15}/>Use one text log per line. Pretty JSON objects and JSON arrays are accepted. Unrecognized text is stored with <code>raw_fallback</code>, not discarded.</p>
        </Panel>
        <Panel title="Recognized JSON fields" kicker="Aliases are normalized">
          <dl className="alias-list">{fieldHelp.map(([label, fields]) => <div key={label}><dt>{label}</dt><dd>{fields}</dd></div>)}</dl>
        </Panel>
      </aside>
    </div>

    <Panel title="Submission journal" kicker="Latest 25 workbench events" action={<button className="icon-button" type="button" onClick={() => void loadHistory()} aria-label="Refresh submission journal"><RefreshCw size={15}/></button>}>
      <State loading={historyLoading} error={historyError} empty={!history.length}><div className="table-wrap"><table><thead><tr><th>Event</th><th>Received</th><th>Normalized type</th><th>Parser</th><th>Parse status</th><th>Host / source</th></tr></thead><tbody>{history.map(event => <tr key={event.id}><td><Link className="event-id" to={`/events/${event.id}`}>EVT-{shortId(event.id)}</Link></td><td>{formatDate(event.ingested_at)}</td><td><strong>{event.event_type || 'unclassified'}</strong><small>{event.message || 'Raw evidence retained'}</small></td><td>{event.parser_name}</td><td><Badge value={event.parse_status}/></td><td>{event.hostname || event.source_ip || '—'}</td></tr>)}</tbody></table></div></State>
      {!!history.length && <div className="journal-foot"><CheckCircle2 size={14}/>Journal entries are stored in PostgreSQL. Open an event to compare normalized fields with the original raw log.</div>}
    </Panel>
  </div>
}
