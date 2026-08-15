export type EventSummary = {
  id: string; event_timestamp: string | null; ingested_at: string; hostname: string | null;
  source_ip: string | null; username: string | null; event_category: string | null;
  event_type: string | null; event_outcome: string | null; severity: string | null;
  parser_name: string; message: string | null;
}

export type EventDetail = EventSummary & Record<string, unknown> & {
  raw_event: string; parser_confidence: number; parse_status: string; event_metadata: Record<string, unknown>;
}

export type Alert = {
  id: string; title: string; description: string; severity: string; status: string; rule_id: string;
  timestamp: string; first_seen: string; last_seen: string; event_count: number; affected_host: string | null;
  source_ip: string | null; username: string | null; mitre: Record<string, string>;
  evidence: Record<string, unknown>; analyst_notes: string; events?: EventSummary[];
}

export type Rule = {
  id: string; title: string; description: string; severity: string; enabled: boolean;
  match: Record<string, unknown>; group_by: string[]; threshold: Record<string, number> | null;
  sequence: Record<string, unknown> | null; mitre: Record<string, string>;
}

export type Statistics = {
  total_events: number; events_today: number; active_alerts: number; critical_alerts: number;
  high_alerts: number; monitored_hosts: number; alerts_by_severity: Record<string, number>;
  categories: {name: string; count: number}[]; top_source_ips: {name: string; count: number}[];
  event_volume: {date: string; count: number}[];
}

export type Page<T> = {items: T[]; total: number; page: number; page_size: number}
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {headers: {'Content-Type': 'application/json', ...init?.headers}, ...init})
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export const api = {
  statistics: () => request<Statistics>('/statistics'),
  events: (query = '') => request<Page<EventSummary>>(`/events${query}`),
  event: (id: string) => request<EventDetail>(`/events/${id}`),
  eventAlerts: (id: string) => request<Alert[]>(`/events/${id}/alerts`),
  alerts: (query = '') => request<Page<Alert>>(`/alerts${query}`),
  alert: (id: string) => request<Alert>(`/alerts/${id}`),
  updateAlert: (id: string, body: {status?: string; analyst_notes?: string}) => request<Alert>(`/alerts/${id}`, {method: 'PATCH', body: JSON.stringify(body)}),
  rules: () => request<Rule[]>('/rules'),
  hosts: () => request<{hostname: string; event_count: number; last_seen: string}[]>('/hosts'),
}
