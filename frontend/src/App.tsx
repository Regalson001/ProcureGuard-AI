
import { useEffect, useState } from 'react'

import type { ReactNode } from 'react'

import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Bell,
  CheckCircle2,
  ClipboardCheck,
  FileText,
  LayoutDashboard,
  Play,
  RefreshCw,
  Search,
  ShieldCheck,
  Truck,
  UploadCloud
} from 'lucide-react'

import {
  request,
  type Finding,
  type Metrics
} from './api'


export default function App() {

  const [metrics, setMetrics] =
    useState<Metrics | null>(null)

  const [findings, setFindings] =
    useState<Finding[]>([])

  const [busy, setBusy] =
    useState(false)

  const [message, setMessage] =
    useState('')

  const [tab, setTab] =
    useState('Overview')

  const [query, setQuery] =
    useState('')


  async function refresh() {

    try {

      const [m, f] = await Promise.all([

        request<Metrics>('/api/dashboard'),

        request<Finding[]>('/api/audits')

      ])

      setMetrics(m)

      setFindings(f)

    } catch (e) {

      setMessage(
        e instanceof Error
          ? e.message
          : 'Could not connect to API'
      )

    }

  }


  useEffect(() => {

    void refresh()

  }, [])


  async function runAudit() {

    setBusy(true)

    setMessage('')

    try {

      const result = await request<{
        created_findings: number
      }>('/api/audits/run', {

        method: 'POST'

      })

      setMessage(
        `Audit completed. ${result.created_findings} new finding(s) created.`
      )

      await refresh()

    } catch (e) {

      setMessage(
        e instanceof Error
          ? e.message
          : 'Audit failed'
      )

    } finally {

      setBusy(false)

    }

  }


  async function upload(file?: File) {

    if (!file) return

    const body = new FormData()

    body.append('file', file)

    body.append('document_type', 'procurement')

    try {

      await request('/api/documents', {

        method: 'POST',

        body

      })

      setMessage(`${file.name} uploaded.`)

      await refresh()

    } catch (e) {

      setMessage(
        e instanceof Error
          ? e.message
          : 'Upload failed'
      )

    }

  }


  async function decide(
    id: number,
    decision: string
  ) {

    try {

      await request(
        `/api/reviews/${id}/decision`,
        {

          method: 'POST',

          headers: {
            'Content-Type': 'application/json'
          },

          body: JSON.stringify({

            decision,

            reviewer: 'Workspace reviewer',

            comment: 'Reviewed in dashboard'

          })

        }
      )

      setMessage(
        `Finding #${id}: ${decision}.`
      )

      await refresh()

    } catch (e) {

      setMessage(
        e instanceof Error
          ? e.message
          : 'Could not save decision'
      )

    }

  }


  const filtered = findings.filter(f =>

    `${f.title} ${f.category} ${f.explanation}`
      .toLowerCase()
      .includes(query.toLowerCase())

  )


  const nav = [

    {
      name: 'Overview',
      icon: LayoutDashboard
    },

    {
      name: 'Audit findings',
      icon: ClipboardCheck
    },

    {
      name: 'Documents',
      icon: FileText
    }

  ]


  return (

    <div className="shell">

      <aside className="sidebar">

        <div className="brand">

          <div className="brand-mark">

            <ShieldCheck size={22} />

          </div>

          <div>

            <b>ProcureGuard</b>

            <small>AI AUDIT PLATFORM</small>

          </div>

        </div>


        <div className="workspace-label">

          WORKSPACE

        </div>


        {nav.map(n => (

          <button

            key={n.name}

            className={
              `nav-item ${
                tab === n.name ? 'active' : ''
              }`
            }

            onClick={() => setTab(n.name)}

          >

            <n.icon size={17} />

            {n.name}

          </button>

        ))}


        <div className="sidebar-bottom">

          <div className="secure">

            <ShieldCheck size={17} />

            <span>

              <b>Audit environment</b>

              <small>Local development mode</small>

            </span>

          </div>


          <div className="profile">

            <div className="avatar">

              SO

            </div>

            <span>

              <b>Workspace Admin</b>

              <small>Procurement team</small>

            </span>

          </div>

        </div>

      </aside>


      <main className="main">

        <header className="topbar">

          <div>

            <span className="crumb">

              Workspace

            </span>

            <span className="slash">/</span>

            <b>{tab}</b>

          </div>


          <div className="top-actions">

            <span className="status">

              <i />

              API workspace

            </span>

            <button
              className="icon-btn"
              aria-label="Notifications"
            >

              <Bell size={18} />

            </button>

            <div className="avatar">SO</div>

          </div>

        </header>


        <div className="content">

          <div className="welcome">

            <div>

              <div className="eyebrow">

                PROCUREMENT INTELLIGENCE

              </div>

              <h1>

                {
                  tab === 'Overview'
                    ? 'Audit overview'
                    : tab
                }

              </h1>

              <p>

                Monitor procurement activity,
                verify transactions and investigate exceptions.

              </p>

            </div>


            <div className="welcome-actions">

              <button
                className="btn secondary"
                onClick={() => void refresh()}
              >

                <RefreshCw size={16} />

                Refresh

              </button>


              <button
                className="btn primary"
                onClick={() => void runAudit()}
                disabled={busy}
              >

                <Play size={16} />

                {
                  busy
                    ? 'Running audit…'
                    : 'Run audit'
                }

              </button>

            </div>

          </div>


          {message && (

            <div className="notice">

              {message}

              <button
                onClick={() => setMessage('')}
              >

                ×

              </button>

            </div>

          )}


          <section className="metric-grid">

            <Metric

              icon={<Truck />}

              label="Registered vendors"

              value={metrics?.vendors ?? '—'}

              note="Vendor records"

            />


            <Metric

              icon={<FileText />}

              label="Documents uploaded"

              value={metrics?.documents ?? '—'}

              note="Stored source files"

            />


            <Metric

              icon={<AlertTriangle />}

              label="Open findings"

              value={metrics?.open_findings ?? '—'}

              note="Awaiting review"

              warning

            />


            <Metric

              icon={<ShieldCheck />}

              label="High-risk findings"

              value={metrics?.high_risk ?? '—'}

              note="Requires attention"

              warning

            />

          </section>


          <section className="panel-grid">

            <div className="panel main-panel">

              <div className="panel-head">

                <div>

                  <h2>

                    {
                      tab === 'Documents'
                        ? 'Document intake'
                        : tab === 'Audit findings'
                          ? 'Audit findings'
                          : 'Latest audit findings'
                    }

                  </h2>

                  <p>

                    Exceptions generated by procurement validation rules

                  </p>

                </div>


                <span className="live-tag">

                  <i />

                  LIVE DATA

                </span>

              </div>


              <div className="toolbar">

                <div className="search">

                  <Search size={16} />

                  <input

                    value={query}

                    onChange={e =>
                      setQuery(e.target.value)
                    }

                    placeholder="Search findings…"

                  />

                </div>


                <label className="btn secondary upload">

                  <UploadCloud size={16} />

                  Upload document

                  <input

                    type="file"

                    accept=".pdf,.png,.jpg,.jpeg,.txt"

                    onChange={e =>
                      void upload(e.target.files?.[0])
                    }

                  />

                </label>

              </div>


              <div className="table-wrap">

                <table>

                  <thead>

                    <tr>

                      <th>FINDING</th>

                      <th>SEVERITY</th>

                      <th>STATUS</th>

                      <th>REFERENCE</th>

                    </tr>

                  </thead>


                  <tbody>

                    {filtered.map(f => (

                      <tr key={f.id}>

                        <td>

                          <b>{f.title}</b>

                          <small>

                            {f.category.replaceAll('_', ' ')}

                          </small>

                          <p className="explanation">

                            {f.explanation}

                          </p>

                        </td>


                        <td>

                          <span
                            className={`severity ${f.severity}`}
                          >

                            {f.severity}

                          </span>

                        </td>


                        <td>

                          <span className="finding-status">

                            {f.status.replaceAll('_', ' ')}

                          </span>

                        </td>


                        <td>

                          #{f.id}

                        </td>

                      </tr>

                    ))}


                    {filtered.length === 0 && (

                      <tr>

                        <td
                          colSpan={4}
                          className="empty"
                        >

                          No findings yet. Add procurement records
                          through the API, then run an audit.

                        </td>

                      </tr>

                    )}

                  </tbody>

                </table>

              </div>

            </div>


            <div className="right-column">

              <div className="panel action-panel">

                <div className="panel-head">

                  <div>

                    <h2>Review queue</h2>

                    <p>Human decision required</p>

                  </div>

                  <ClipboardCheck size={19} />

                </div>


                {findings

                  .filter(f =>
                    f.status === 'pending_review'
                  )

                  .slice(0, 5)

                  .map(f => (

                    <div
                      className="review-item"
                      key={f.id}
                    >

                      <div className="review-icon">

                        <AlertTriangle size={16} />

                      </div>


                      <div className="review-copy">

                        <b>{f.title}</b>

                        <small>

                          {f.severity} risk · Finding #{f.id}

                        </small>


                        <div className="review-buttons">

                          <button
                            onClick={() =>
                              void decide(f.id, 'approved')
                            }
                          >

                            Approve

                          </button>


                          <button
                            onClick={() =>
                              void decide(f.id, 'rejected')
                            }
                          >

                            Reject

                          </button>

                        </div>

                      </div>

                    </div>

                  ))}


                {findings.every(
                  f => f.status !== 'pending_review'
                ) && (

                  <div className="empty compact">

                    <CheckCircle2 size={20} />

                    No items awaiting review

                  </div>

                )}

              </div>


              <div className="panel pipeline">

                <h2>Audit pipeline</h2>

                <p>Core validation stages</p>


                {[
                  'Document intake',
                  'Reference matching',
                  'Policy validation',
                  'Human review'
                ].map((s, i) => (

                  <div
                    className="pipeline-step"
                    key={s}
                  >

                    <span className="step-number">

                      {i + 1}

                    </span>

                    <span>{s}</span>

                    <span className="step-state">

                      {i === 3 ? 'Review' : 'Ready'}

                    </span>

                  </div>

                ))}

              </div>

            </div>

          </section>


          <footer>

            ProcureGuard AI

            <span>·</span>

            Procurement audit workspace

            <span>·</span>

            Local MVP

          </footer>

        </div>

      </main>

    </div>

  )

}


function Metric({

  icon,

  label,

  value,

  note,

  warning = false

}: {

  icon: ReactNode

  label: string

  value: string | number

  note: string

  warning?: boolean

}) {

  return (

    <div className="metric-card">

      <div
        className={`metric-icon ${
          warning ? 'warn' : ''
        }`}
      >

        {icon}

      </div>


      <div className="metric-label">

        {label}

      </div>


      <div className="metric-value">

        {value}

      </div>


      <div className="metric-note">

        {note}

        <ArrowUpRight size={13} />

      </div>

    </div>

  )

}
