import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals() })

describe('SentinelLite dashboard', () => {
  it('renders overview metrics returned by the API', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      const body = url.includes('statistics') ? {
        total_events: 42, events_today: 12, active_alerts: 2, critical_alerts: 1, high_alerts: 1,
        monitored_hosts: 3, alerts_by_severity: {critical: 1}, categories: [], top_source_ips: [], event_volume: []
      } : {items: [], total: 0, page: 1, page_size: 5}
      return Promise.resolve(new Response(JSON.stringify(body), {status: 200}))
    }))
    render(<MemoryRouter><App/></MemoryRouter>)
    expect(await screen.findByText('42')).toBeInTheDocument()
    expect(screen.getByText('Security posture, at a glance')).toBeInTheDocument()
  })

  it('shows an actionable empty state for the events view', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response(JSON.stringify({items: [], total: 0, page: 1, page_size: 50}), {status: 200}))))
    render(<MemoryRouter initialEntries={['/events']}><App/></MemoryRouter>)
    expect(await screen.findByText('No data yet')).toBeInTheDocument()
    expect(screen.getByLabelText('Filter by source IP')).toBeInTheDocument()
  })

  it('renders safe API errors without injecting markup', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response(JSON.stringify({detail: '<script>alert(1)</script>'}), {status: 500}))))
    render(<MemoryRouter initialEntries={['/hosts']}><App/></MemoryRouter>)
    expect(await screen.findByText('<script>alert(1)</script>')).toBeInTheDocument()
    expect(document.querySelector('script')).toBeNull()
  })

  it('renders an alert investigation row from the API', async () => {
    const alert = {
      id: 'aabbccdd-0000-0000-0000-000000000000', title: 'SSH brute force', description: 'Test',
      severity: 'high', status: 'new', rule_id: 'AUTH-001', timestamp: '2026-08-15T12:00:00Z',
      first_seen: '2026-08-15T12:00:00Z', last_seen: '2026-08-15T12:01:00Z', event_count: 5,
      affected_host: 'lab01', source_ip: '10.0.0.5', username: 'root', mitre: {}, evidence: {}, analyst_notes: ''
    }
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response(JSON.stringify({items: [alert], total: 1, page: 1, page_size: 50}), {status: 200}))))
    render(<MemoryRouter initialEntries={['/alerts']}><App/></MemoryRouter>)
    expect(await screen.findByText('SSH brute force')).toBeInTheDocument()
    expect(screen.getByText('AUTH-001')).toBeInTheDocument()
    expect(screen.getByText('5 events')).toBeInTheDocument()
  })

  it('submits pasted logs and refreshes the persistent workbench journal', async () => {
    const fetchMock = vi.fn((_: string, init?: RequestInit) => {
      if (init?.method === 'POST') return Promise.resolve(new Response(JSON.stringify({
        total_submitted: 1, successfully_parsed: 1, partially_parsed: 0,
        raw_fallback: 0, rejected: 0, event_ids: ['12345678-0000-0000-0000-000000000000'], messages: []
      }), {status: 200}))
      return Promise.resolve(new Response(JSON.stringify({items: [], total: 0, page: 1, page_size: 25}), {status: 200}))
    })
    vi.stubGlobal('fetch', fetchMock)
    render(<MemoryRouter initialEntries={['/ingest']}><App/></MemoryRouter>)
    expect(await screen.findByText('Add and verify logs')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Log content'), {target: {value: 'src_ip=10.0.0.1 action=blocked'}})
    fireEvent.click(screen.getByRole('button', {name: 'Submit and analyze'}))
    expect(await screen.findByText('Submission complete')).toBeInTheDocument()
    expect(screen.getByText('Submitted')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/ingest/text'), expect.objectContaining({method: 'POST'}))
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('source_type=workbench'), expect.anything())
  })
})
