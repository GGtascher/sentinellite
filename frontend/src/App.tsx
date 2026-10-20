import { Route, Routes } from 'react-router-dom'
import { Shell } from './components'
import AlertDetail from './pages/AlertDetail'
import Alerts from './pages/Alerts'
import EventDetail from './pages/EventDetail'
import Events from './pages/Events'
import Hosts from './pages/Hosts'
import Ingest from './pages/Ingest'
import Overview from './pages/Overview'
import Rules from './pages/Rules'

export default function App() { return <Shell><Routes><Route path="/" element={<Overview/>}/><Route path="/ingest" element={<Ingest/>}/><Route path="/events" element={<Events/>}/><Route path="/events/:id" element={<EventDetail/>}/><Route path="/alerts" element={<Alerts/>}/><Route path="/alerts/:id" element={<AlertDetail/>}/><Route path="/rules" element={<Rules/>}/><Route path="/hosts" element={<Hosts/>}/><Route path="*" element={<Overview/>}/></Routes></Shell> }
