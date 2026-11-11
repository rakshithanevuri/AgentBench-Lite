
import { useEffect, useMemo, useState } from 'react'
import {
  Activity, Bot, Boxes, ChartNoAxesCombined, CircleHelp, Command,
  Cpu, FlaskConical, Gauge, LayoutDashboard, Plus, RefreshCw,
  ShieldCheck, Sparkles, Trash2, X
} from 'lucide-react'
import { api } from './api'

type Agent = {
  id: string
  name: string
  description: string
  entrypoint: string
  version: string
}

type Evaluation = {
  id: string
  suite_name: string
  status: string
  created_at: string
}

const nav = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'agents', label: 'Agents', icon: Bot },
  { id: 'suites', label: 'Task suites', icon: Boxes },
  { id: 'evaluations', label: 'Evaluations', icon: FlaskConical },
  { id: 'results', label: 'Results & traces', icon: ChartNoAxesCombined }
]

export default function App() {
  const [page, setPage] = useState('overview')
  const [agents, setAgents] = useState<Agent[]>([])
  const [suites, setSuites] = useState<any[]>([])
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [health, setHealth] = useState('checking')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [detail, setDetail] = useState<any>(null)
  const [selected, setSelected] = useState<string[]>([])
  const [suite, setSuite] = useState('starter')
  const [result, setResult] = useState<any>(null)
  const [showAgent, setShowAgent] = useState(false)
  const [registry, setRegistry] = useState<string[]>([])
  const [compatibility, setCompatibility] = useState<any>(null)

  const refresh = async () => {
    try {
      const [h, a, s, e, r] = await Promise.all([
        api.health(),
        api.agents(),
        api.suites(),
        api.evaluations(),
        api.registry()
      ])

      setHealth(h.status)
      setAgents(a)
      setSuites(s)
      setEvaluations(e)
      setRegistry(r.entrypoints)

      if (s.length && !s.some((x: any) => x.name === suite)) {
        setSuite(s[0].name)
      }

      setError('')
    } catch (e) {
      setHealth('offline')
      setError(e instanceof Error ? e.message : 'Could not connect to API')
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  useEffect(() => {
    if (page !== 'evaluations' || !suite || selected.length === 0) { setCompatibility(null); return }
    api.compatibility({agent_ids:selected, suite_name:suite}).then(setCompatibility).catch(() => setCompatibility(null))
  }, [page, suite, selected.join(',')])

  const latest = useMemo(() => evaluations[0], [evaluations])

  const launch = async () => {
    setBusy(true)
    setError('')

    try {
      const e = await api.run({
        agent_ids: selected,
        suite_name: suite,
        repeats: 1
      })

      const d = await api.evaluation(e.id)
      setResult(d)
      setDetail(d)
      setPage('results')
      await refresh()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Evaluation failed')
    } finally {
      setBusy(false)
    }
  }

  const openResult = async (id: string) => {
    try {
      const d = await api.evaluation(id)
      setDetail(d)
      setPage('results')
    } catch (e) {
      setError(String(e))
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Command size={20} /></div>
          <div>
            <b>agentbench<span> lite</span></b>
            <small>AGENT EVALUATION WORKSPACE</small>
          </div>
        </div>

        <div className="workspace">
          <span className="workspace-dot" /> LOCAL WORKSPACE
          <span className="chevron">⌄</span>
        </div>

        <div className="nav-label">WORKSPACE</div>

        <nav>
          {nav.map(n => (
            <button
              key={n.id}
              className={`nav-item ${page === n.id ? 'active' : ''}`}
              onClick={() => setPage(n.id)}
            >
              <n.icon size={17} />
              {n.label}
              {n.id === 'evaluations' && (
                <span className="nav-count">{evaluations.length}</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="privacy-card">
            <ShieldCheck size={17} />
            <div>
              <b>Local-first by design</b>
              <p>Your agent tasks and results stay on this machine.</p>
            </div>
          </div>

          <button className="nav-item" onClick={() => setPage('help')}>
            <CircleHelp size={17} /> Help & documentation
          </button>

          <div className="profile">
            <div className="avatar">AB</div>
            <div>
              <b>Local workspace</b>
              <small>Personal instance</small>
            </div>
            <span className={`status-dot ${health === 'ok' ? 'good' : 'bad'}`} />
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="crumb">
            Workspace <span>/</span>
            <b>{nav.find(n => n.id === page)?.label ?? 'Help'}</b>
          </div>

          <div className="top-actions">
            <span className={`api-pill ${health === 'ok' ? 'online' : ''}`}>
              <i /> API {health === 'ok' ? 'Connected' : 'Offline'}
            </span>

            <button className="icon-button" onClick={refresh} title="Refresh">
              <RefreshCw size={16} />
            </button>

            <button className="primary small" onClick={() => setPage('evaluations')}>
              <Plus size={15} /> New evaluation
            </button>
          </div>
        </header>

        {error && (
          <div className="alert">
            <span>{error}</span>
            <button onClick={() => setError('')}><X size={15} /></button>
          </div>
        )}

        {page === 'overview' && (
          <>
            <div className="page-heading">
              <div>
                <div className="eyebrow">YOUR AGENT WORKSPACE</div>
                <h1>Evaluate with confidence.</h1>
                <p>Run structured tests, understand agent behaviour, and compare performance across versions.</p>
              </div>
              <button className="primary" onClick={() => setPage('evaluations')}>
                <Plus size={16} /> Create evaluation
              </button>
            </div>

            <div className="hero-strip">
              <div className="hero-icon"><Sparkles size={22} /></div>
              <div>
                <b>A clearer picture of your agents starts here.</b>
                <p>Connect an agent, choose a task suite, and run your first local benchmark. No model API key needed for the starter examples.</p>
              </div>
              <button className="text-button" onClick={() => setPage('agents')}>
                Set up an agent <span>→</span>
              </button>
            </div>

            <div className="section-head">
              <div>
                <h2>Workspace snapshot</h2>
                <p>A quick look at your evaluation activity.</p>
              </div>
              <span className="muted-label">LIVE DATA</span>
            </div>

            <div className="metric-grid">
              <Metric icon={<Bot />} label="Connected agents" value={agents.length} note="Registered in workspace" />
              <Metric icon={<FlaskConical />} label="Evaluations" value={evaluations.length} note="Total benchmark runs" />
              <Metric icon={<Gauge />} label="Latest status" value={latest?.status ?? '—'} note={latest ? new Date(latest.created_at).toLocaleString() : 'No runs yet'} />
              <Metric icon={<Activity />} label="Task suites" value={suites.length} note="Ready to run" />
            </div>

            <div className="content-grid">
              <section className="panel">
                <div className="panel-head">
                  <div>
                    <h3>Recent evaluations</h3>
                    <p>Your latest benchmark activity.</p>
                  </div>
                  <button className="text-button" onClick={() => setPage('results')}>View all →</button>
                </div>

                {evaluations.length === 0 ? (
                  <Empty
                    icon={<ChartNoAxesCombined />}
                    title="No evaluations yet"
                    text="Your completed benchmark runs will appear here."
                    action="Create your first evaluation"
                    onClick={() => setPage('evaluations')}
                  />
                ) : (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr><th>SUITE</th><th>STATUS</th><th>CREATED</th><th /></tr>
                      </thead>
                      <tbody>
                        {evaluations.slice(0, 5).map(e => (
                          <tr key={e.id}>
                            <td>
                              <b>{e.suite_name}</b>
                              <small className="subcell">{e.id.slice(0, 8)}</small>
                            </td>
                            <td><Status value={e.status} /></td>
                            <td>{new Date(e.created_at).toLocaleString()}</td>
                            <td>
                              <button className="text-button" onClick={() => openResult(e.id)}>Open →</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>

              <section className="panel">
                <div className="panel-head">
                  <div>
                    <h3>Quick start</h3>
                    <p>Three steps to your first benchmark.</p>
                  </div>
                  <Sparkles size={18} className="purple" />
                </div>

                <div className="steps">
                  <Step n="01" title="Register an agent" text="Connect a local or external agent." done={agents.length > 0} onClick={() => setPage('agents')} />
                  <Step n="02" title="Choose a task suite" text="Start with the included two-task smoke test." done={suites.length > 0} onClick={() => setPage('suites')} />
                  <Step n="03" title="Run an evaluation" text="See pass rates, latency, outputs and traces." done={evaluations.length > 0} onClick={() => setPage('evaluations')} />
                </div>
              </section>
            </div>
          </>
        )}

        {page === 'agents' && (
          <>
            <PageTitle
              eyebrow="AGENT MANAGEMENT"
              title="Your agents"
              text="Register and manage agents built with different frameworks and technologies."
              action={
                <button className="primary" onClick={() => setShowAgent(true)}>
                  <Plus size={16} /> Register agent
                </button>
              }
            />

            <div className="info-banner">
              <Cpu size={18} />
              <span>
                <b>Multiple integration options.</b> Register local Python functions or connect external agents through HTTP endpoints. External agents can run in their own environments.
              </span>
            </div>

            <div className="agent-grid">
              {agents.map(a => (
                <div className="panel agent-card" key={a.id}>
                  <div className="agent-top">
                    <div className="agent-icon"><Bot /></div>
                    <Status value="registered" />
                    <button
                      className="icon-button danger"
                      onClick={async () => {
                        await api.deleteAgent(a.id)
                        refresh()
                      }}
                      title="Delete agent"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>

                  <h3>{a.name}</h3>
                  <p>{a.description || 'No description provided.'}</p>

                  <div className="agent-meta">
                    <span>ENTRYPOINT</span>
                    <code>{a.entrypoint}</code>
                  </div>

                  <div className="agent-meta">
                    <span>VERSION</span>
                    <b>{a.version}</b>
                  </div>
                  <div className="agent-meta">
                    <span>CAPABILITIES</span>
                    <b>{(a as any).capabilities?.join(', ') || 'text_input (baseline)'}</b>
                  </div>
                  {!(a as any).capabilities?.includes('document_input') && (
                    <button className="text-button" onClick={async () => { await api.updateAgent(a.id, {capabilities:[...((a as any).capabilities ?? []), 'document_input']}); await refresh(); }}>Declare document_input capability →</button>
                  )}
                </div>
              ))}

              <button className="add-agent" onClick={() => setShowAgent(true)}>
                <Plus />
                <b>Add an agent</b>
                <span>Connect another agent</span>
              </button>
            </div>
          </>
        )}

        {page === 'suites' && (
          <>
            <PageTitle
              eyebrow="BENCHMARK MANAGEMENT"
              title="Task suites"
              text="Reusable benchmarks with task cases, reference answers, capability requirements and shared resources."
              action={<label className="primary" style={{cursor:'pointer'}}>Import benchmark JSON<input type="file" accept=".json,application/json" hidden onChange={async e => { const file=e.target.files?.[0]; if(!file) return; try { const body=JSON.parse(await file.text()); const name=(file.name.replace(/\.json$/i,'').replace(/[^a-zA-Z0-9_-]/g,'_')).slice(0,80); await api.createSuite(name,body); await refresh(); setError(''); } catch(err) { setError(err instanceof Error ? err.message : 'Could not import benchmark JSON'); } e.currentTarget.value=''; }} /></label>}
            />

            <div className="suite-grid">
              {suites.map((s: any) => (
                <div className="panel suite-card" key={s.name}>
                  <div className="suite-icon"><Boxes /></div>
                  <div className="suite-count">{s.task_count} TASKS</div>
                  <h3>{s.title}</h3>
                  <p>{s.description}</p>
                  <div className="agent-meta"><span>REQUIRES</span><b>{s.required_capabilities?.join(', ') || 'text_input'}</b></div>
                  <div className="agent-meta"><span>RESOURCES</span><b>{s.resource_count ?? 0}</b></div>
                  <code>{s.name}</code>
                </div>
              ))}
            </div>

            <div className="info-banner">
              <ShieldCheck size={18} />
              <span>
                Import a JSON benchmark here, or add a YAML file under <code>examples/task_suites/</code>. A benchmark can include reference answers, required capabilities, and shared text/PDF resources (base64-encoded for binary files).
              </span>
            </div>
          </>
        )}

        {page === 'evaluations' && (
          <>
            <PageTitle
              eyebrow="BENCHMARK RUNNER"
              title="New evaluation"
              text="Choose which agents to test and the task suite they should run against."
            />

            <div className="run-layout">
              <section className="panel run-form">
                <div className="form-section">
                  <div className="form-step">01</div>
                  <div className="form-content">
                    <h3>Select agents</h3>
                    <p>Choose one or more registered agents to compare.</p>

                    {agents.length === 0 ? (
                      <Empty
                        icon={<Bot />}
                        title="No agents registered"
                        text="Register an agent before starting an evaluation."
                        action="Go to agents"
                        onClick={() => setPage('agents')}
                      />
                    ) : (
                      agents.map(a => (
                        <label className={`select-agent ${selected.includes(a.id) ? 'chosen' : ''}`} key={a.id}>
                          <input
                            type="checkbox"
                            checked={selected.includes(a.id)}
                            onChange={e => setSelected(old =>
                              e.target.checked
                                ? [...old, a.id]
                                : old.filter(x => x !== a.id)
                            )}
                          />
                          <span className="checkmark" />
                          <span className="agent-mini"><Bot size={17} /></span>
                          <span className="agent-label">
                            <b>{a.name}</b>
                            <small>{a.entrypoint} · v{a.version}</small>
                          </span>
                          <span className="select-version">{a.version}</span>
                        </label>
                      ))
                    )}
                  </div>
                </div>

                <div className="form-section">
                  <div className="form-step">02</div>
                  <div className="form-content">
                    <h3>Choose a task suite</h3>
                    <p>Every selected agent receives the same task cases.</p>

                    <select className="select-input" value={suite} onChange={e => setSuite(e.target.value)}>
                      {suites.map((s: any) => (
                        <option key={s.name} value={s.name}>
                          {s.title} · {s.task_count} tasks
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {compatibility && <div className={`info-banner ${compatibility.compatible ? '' : 'compatibility-warning'}`}>
                  <ShieldCheck size={18} />
                  <span><b>{compatibility.compatible ? 'All selected agents are compatible.' : 'Some agents cannot run this benchmark yet.'}</b>{compatibility.agents.filter((x:any) => !x.compatible).map((x:any) => <span key={x.agent_id}> {x.agent_name}: missing {x.missing_capabilities.join(', ') || x.error}. </span>)}</span>
                </div>}

                <div className="form-section">
                  <div className="form-step">03</div>
                  <div className="form-content">
                    <h3>Review execution</h3>
                    <p>Review the evaluation configuration before starting.</p>

                    <div className="review-row">
                      <span>Selected agents</span>
                      <b>{selected.length}</b>
                    </div>
                    <div className="review-row">
                      <span>Tasks per agent</span>
                      <b>{suites.find((s: any) => s.name === suite)?.task_count ?? 0}</b>
                    </div>
                    <div className="review-row">
                      <span>Evaluation mode</span>
                      <b className="green-text">Local execution</b>
                    </div>
                  </div>
                </div>

                <button
                  className="primary launch"
                  disabled={!selected.length || !suite || busy || health !== 'ok'}
                  onClick={launch}
                >
                  {busy ? (
                    <><RefreshCw className="spin" size={16} /> Running benchmark…</>
                  ) : (
                    <><FlaskConical size={16} /> Run evaluation</>
                  )}
                </button>
              </section>

              <aside className="panel run-aside">
                <div className="aside-symbol"><ShieldCheck /></div>
                <h3>Evaluation transparency</h3>
                <p>AgentBench Lite uses the checks defined in your task suite. External agents may make their own model or tool calls, depending on their implementation.</p>
                <div className="aside-divider" />
                <b>What gets captured</b>
                <ul>
                  <li>Agent response and pass/fail</li>
                  <li>Execution latency</li>
                  <li>Tool calls and reported usage</li>
                  <li>Structured execution trace</li>
                </ul>
                <div className="aside-note">Evaluation execution currently runs synchronously. Keep task suites small.</div>
              </aside>
            </div>
          </>
        )}

        {page === 'results' && (
          <>
            <PageTitle
              eyebrow="EVALUATION HISTORY"
              title="Results & traces"
              text="Inspect benchmark outcomes, compare agent pass rates, and review individual executions."
            />

            <div className="panel">
              {detail ? (
                <>
                  <div className="panel-head">
                    <div>
                      <h3>Evaluation {detail.evaluation.id.slice(0, 8)}</h3>
                      <p>{detail.evaluation.suite_name} · {new Date(detail.evaluation.created_at).toLocaleString()}</p>
                    </div>
                    <Status value={detail.evaluation.status} />
                  </div>

                  <div className="metric-grid compact">
                    {detail.summary.map((s: any) => (
                      <Metric
                        key={s.agent_id}
                        icon={<Bot />}
                        label={s.agent_name}
                        value={`${Math.round(s.pass_rate * 100)}%`}
                        note={`${s.passed}/${s.total} passed · ${Math.round(s.avg_latency_ms)} ms avg`}
                      />
                    ))}
                  </div>

                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>AGENT</th><th>TASK</th><th>STATUS</th><th>SCORE</th><th>LATENCY</th>
                        </tr>
                      </thead>
                      <tbody>
                        {detail.results.map((r: any) => (
                          <tr key={r.id}>
                            <td><b>{agents.find(a => a.id === r.agent_id)?.name ?? r.agent_id.slice(0, 8)}</b></td>
                            <td>{r.task_id}</td>
                            <td><Status value={r.status === 'failed' ? 'failed' : r.passed ? 'passed' : 'not passed'} /></td>
                            <td>{Math.round(r.score * 100)}%</td>
                            <td>{Math.round(r.latency_ms)} ms</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="result-output">
                    {detail.results.map((r: any) => (
                      <details key={r.id}>
                        <summary>{r.task_id} · {r.status}</summary>
                        <div className="trace-grid">
                          <div><small>INPUT</small><pre>{r.input}</pre></div>
                          <div><small>OUTPUT</small><pre>{r.output || r.error}</pre></div>
                          <div><small>EVALUATOR DIAGNOSTICS</small><pre>{JSON.stringify(r.evaluation_details ?? [], null, 2)}</pre></div>
                          <div><small>AGENT METADATA</small><pre>{JSON.stringify(r.metadata_json ?? {}, null, 2)}</pre></div>
                          <div><small>TOOL CALLS</small><pre>{JSON.stringify(r.tool_calls ?? [], null, 2)}</pre></div>
                          <div><small>TRACE</small><pre>{JSON.stringify(r.trace, null, 2)}</pre></div>
                        </div>
                      </details>
                    ))}
                  </div>
                </>
              ) : evaluations.length ? (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr><th>SUITE</th><th>STATUS</th><th>CREATED</th><th /></tr>
                    </thead>
                    <tbody>
                      {evaluations.map(e => (
                        <tr key={e.id}>
                          <td>{e.suite_name}</td>
                          <td><Status value={e.status} /></td>
                          <td>{new Date(e.created_at).toLocaleString()}</td>
                          <td>
                            <button className="text-button" onClick={() => openResult(e.id)}>Inspect →</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <Empty
                  icon={<ChartNoAxesCombined />}
                  title="No benchmark results yet"
                  text="Run your first evaluation to see agent performance and execution traces."
                  action="Start evaluation"
                  onClick={() => setPage('evaluations')}
                />
              )}
            </div>
          </>
        )}

        {page === 'help' && (
          <>
            <PageTitle
              eyebrow="DOCUMENTATION"
              title="Getting started"
              text="A few notes to help you get the most out of AgentBench Lite."
            />

            <div className="panel help-copy">
              <h3>How evaluations work</h3>
              <p>Register an agent, create or edit a YAML task suite, and select both in the evaluation runner. Each agent receives the same task inputs. The evaluator applies the checks defined on each task and records the response, score, timing and trace.</p>

              <h3>Adding a local Python agent</h3>
              <p>Use <code>@register_agent("your_entrypoint")</code> on a function accepting <code>(task_input: str, settings: dict)</code>. Import your module from the API startup before creating an agent configuration. Only load trusted local code.</p>

              <h3>Adding an external HTTP agent</h3>
              <p>Select <code>http_agent</code> during registration and provide its endpoint URL and timeout. The external agent can run in a separate process or environment. It receives a JSON request containing the task input and returns an answer.</p>

              <h3>Scoring</h3>
              <p>The initial release uses deterministic checks: <code>exact_match</code>, <code>contains</code>, and <code>not_empty</code>. It does not silently use an LLM judge.</p>
            </div>
          </>
        )}
      </main>

      {showAgent && (
        <AgentModal
          registry={registry}
          onClose={() => setShowAgent(false)}
          onSave={async (body: any) => {
            await api.createAgent(body)
            setShowAgent(false)
            await refresh()
          }}
          onDiscover={api.discoverAgent}
          onTestConnection={api.testConnection}
        />
      )}
    </div>
  )
}

function Metric({ icon, label, value, note }: any) {
  return (
    <div className="metric-card">
      <div className="metric-top">
        <span>{label}</span>
        <i>{icon}</i>
      </div>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  )
}

function PageTitle({ eyebrow, title, text, action }: any) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{text}</p>
      </div>
      {action}
    </div>
  )
}

function Status({ value }: any) {
  const good = ['completed', 'passed', 'registered', 'ok'].includes(value)
  const warn = ['completed_with_errors', 'not passed'].includes(value)

  return (
    <span className={`status ${good ? 'success' : warn ? 'warning' : 'neutral'}`}>
      <i />{value.replaceAll('_', ' ')}
    </span>
  )
}

function Empty({ icon, title, text, action, onClick }: any) {
  return (
    <div className="empty">
      <div>{icon}</div>
      <b>{title}</b>
      <p>{text}</p>
      {action && <button className="text-button" onClick={onClick}>{action} →</button>}
    </div>
  )
}

function Step({ n, title, text, done, onClick }: any) {
  return (
    <button className="step" onClick={onClick}>
      <span className={`step-number ${done ? 'done' : ''}`}>{done ? '✓' : n}</span>
      <span>
        <b>{title}</b>
        <small>{text}</small>
      </span>
      <span className="step-arrow">→</span>
    </button>
  )
}

function AgentModal({ registry, onClose, onSave, onDiscover, onTestConnection }: any) {
  const [name, setName] = useState('')
  const [entrypoint, setEntrypoint] = useState(registry[0] ?? '')
  const [description, setDescription] = useState('')
  const [version, setVersion] = useState('1.0.0')
  const [endpoint, setEndpoint] = useState('')
  const [timeout, setTimeoutValue] = useState(30)
  const [capabilities, setCapabilities] = useState('text_input')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [discovery, setDiscovery] = useState<any>(null)
  const [checking, setChecking] = useState(false)
  const [connection, setConnection] = useState<any>(null)

  const isHttpAgent = entrypoint === 'http_agent'

  return (
    <div
      className="modal-backdrop"
      onMouseDown={e => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="modal">
        <div className="modal-head">
          <div>
            <div className="eyebrow">AGENT REGISTRY</div>
            <h2>Connect an agent</h2>
          </div>
          <button className="icon-button" onClick={onClose}>
            <X />
          </button>
        </div>

        <p className="modal-intro">
          Connect an existing HTTP agent. Discover its manifest automatically, or configure capabilities manually when it has no manifest.
        </p>

        <form
          onSubmit={async e => {
            e.preventDefault()
            setSaving(true)
            setError('')

            try {
              const settings = isHttpAgent
                ? { endpoint: endpoint.trim(), timeout }
                : {}

              await onSave({
                name,
                entrypoint,
                description,
                version,
                settings,
                capabilities: capabilities.split(',').map((x:string) => x.trim()).filter(Boolean)
              })
            } catch (err) {
              setError(String(err))
              setSaving(false)
            }
          }}
        >
          <label>
            Agent name
            <input
              required
              minLength={2}
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. KnowledgePilot"
            />
          </label>

          <label>
            Agent integration
            <select
              value={entrypoint}
              onChange={e => setEntrypoint(e.target.value)}
              required
            >
              {registry.map((r: string) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </label>

          {isHttpAgent && (
            <>
              <label>
                Endpoint URL
                <input
                  type="url"
                  required
                  value={endpoint}
                  onChange={e => setEndpoint(e.target.value)}
                  placeholder="http://127.0.0.1:9001/agent"
                />
              </label>

              <label>
                Timeout (seconds)
                <input
                  type="number"
                  required
                  min={1}
                  max={120}
                  value={timeout}
                  onChange={e => setTimeoutValue(Number(e.target.value))}
                />
              </label>
              <div className="modal-actions" style={{justifyContent:'flex-start', flexWrap:'wrap'}}>
                <button type="button" className="secondary" disabled={!endpoint.trim() || checking} onClick={async () => {
                  setChecking(true); setError(''); setConnection(null)
                  try { const found = await onDiscover(endpoint.trim(), Math.min(timeout, 10)); setDiscovery(found); if (found.manifest_found) setCapabilities(found.capabilities.join(', ')); setConnection({ok:true, message:found.manifest_found ? 'Connected. Capabilities discovered from /manifest.' : 'Agent is reachable. No /manifest found; configure capabilities manually.'}) }
                  catch (err) { setError(String(err)); setDiscovery(null) } finally { setChecking(false) }
                }}>{checking ? 'Checking…' : 'Discover capabilities'}</button>
                <button type="button" className="secondary" disabled={!endpoint.trim() || checking} onClick={async () => {
                  setChecking(true); setError(''); setConnection(null)
                  try { const checked = await onTestConnection(endpoint.trim(), Math.min(timeout, 10)); setConnection({ok:true, message:checked.manifest_found ? 'Connection verified; manifest available.' : 'Health check passed; manifest not available.'}); setDiscovery(checked) }
                  catch (err) { setConnection({ok:false, message:String(err)}) } finally { setChecking(false) }
                }}>Test connection</button>
              </div>
              {connection && <div className={connection.ok ? 'info-banner' : 'form-error'}>{connection.message}</div>}
              {discovery?.manifest_found && <div className="info-banner"><ShieldCheck size={16}/><span>Manifest detected · protocol {discovery.protocol_version || '1.0'} · {discovery.capabilities.length} capabilities</span></div>}
              {!discovery?.manifest_found && <small>Optional agent routes: GET /health and GET /manifest. Discovery never runs a task or calls an LLM.</small>}
            </>
          )}

          <label>
            Capabilities (comma-separated)
            <input value={capabilities} onChange={e => setCapabilities(e.target.value)} placeholder="text_input, document_input, tools" />
            <small>Declare only what this agent actually supports. Common values: text_input, document_input, tools, stateful, streaming, usage_reporting.</small>
          </label>

          <label>
            Description
            <input
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="What does this agent do?"
            />
          </label>

          <label>
            Version
            <input
              value={version}
              onChange={e => setVersion(e.target.value)}
            />
          </label>

          {error && <div className="form-error">{error}</div>}

          <div className="modal-actions">
            <button type="button" className="secondary" onClick={onClose}>
              Cancel
            </button>
            <button
              className="primary"
              disabled={saving || !entrypoint || (isHttpAgent && !endpoint.trim())}
            >
              {saving ? 'Saving…' : 'Connect agent'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
