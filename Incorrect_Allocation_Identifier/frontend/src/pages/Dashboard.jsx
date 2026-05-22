import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';
import { fetchRuns, fetchSummary, fetchExceptions, fetchTopViolators } from '../api';

const SEVERITY_COLORS = {
  Critical: '#ef4444',
  High: '#f97316',
  Medium: '#3b82f6',
};

const RULE_COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899'];

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: '#1a1f35', border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: 8, padding: '10px 14px', fontSize: 12,
    }}>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{label || payload[0]?.name}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || '#94a3b8' }}>
          {p.name}: <strong>{p.value}</strong>
        </div>
      ))}
    </div>
  );
}

function ViolatorExceptionsModal({ violator, runId, onClose }) {
  const [exceptions, setExceptions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (violator) {
      setLoading(true);
      fetchExceptions({ run_id: runId, psid: violator.psid, limit: 100 })
        .then(res => {
          setExceptions(res.data.exceptions || []);
          setLoading(false);
        })
        .catch(err => {
          console.error(err);
          setLoading(false);
        });
    }
  }, [violator, runId]);

  if (!violator) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 1000 }}>
        <div className="modal-header">
          <div>
            <div className="modal-title">Violations for {violator.name}</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>PSID: {violator.psid}</div>
          </div>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body" style={{ padding: 0, maxHeight: '60vh', overflowY: 'auto' }}>
          {loading ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Loading violations...</div>
          ) : exceptions.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rule</th>
                  <th>Severity</th>
                  <th>Project</th>
                  <th>Task</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                {exceptions.map(exc => (
                  <tr key={exc.exception_id}>
                    <td style={{ fontWeight: 600 }}>{exc.rule_id}</td>
                    <td>
                      <span className={`severity-badge ${exc.severity.toLowerCase()}`}>
                        {exc.severity}
                      </span>
                    </td>
                    <td>{exc.project_id}</td>
                    <td>{exc.task_type}</td>
                    <td style={{ maxWidth: '600px', whiteSpace: 'normal', lineHeight: '1.4' }}>{exc.exception_reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>No details found.</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [selectedViolator, setSelectedViolator] = useState(null);

  useEffect(() => { loadDashboard(); }, []);

  async function loadDashboard() {
    setLoading(true);
    setError(null);
    try {
      // Get latest run
      const runsRes = await fetchRuns(1);
      const runs = runsRes.data.runs;
      if (!runs || runs.length === 0) {
        setData(null);
        setLoading(false);
        return;
      }
      const latestRun = runs[0];
      const runId = latestRun.run_id;

      // Get summary for latest run
      const summaryRes = await fetchSummary(runId);
      const summary = summaryRes.data;

      // Get top violators directly from backend
      const violatorRes = await fetchTopViolators({ limit: 10 });
      const topViolators = violatorRes.data.data.map(v => ({
        psid: v.psid,
        name: v.employee_name || 'N/A',
        count: v.violation_count
      }));

      setData({
        run: latestRun,
        summary,
        topViolators
      });
    } catch (e) {
      setError(e.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="state-container">
        <div className="spinner" />
        <div className="state-text">Loading dashboard data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="state-container">
        <div className="state-icon">❌</div>
        <div className="state-text">{error}</div>
        <button className="btn btn-secondary btn-sm" onClick={loadDashboard}>Retry</button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="state-container">
        <div className="state-icon">📭</div>
        <div className="state-text">No pipeline runs found. Trigger a run to see results.</div>
      </div>
    );
  }

  const { run, summary, topViolators } = data;
  const totalRecords = run.total_records_evaluated || 0;
  const totalExceptions = run.total_exceptions || 0;
  const cleanRecords = Math.max(0, totalRecords - new Set(
    (topViolators || []).map(v => v.psid)
  ).size);
  const exceptionRate = totalRecords > 0 ? ((totalExceptions / totalRecords) * 100).toFixed(1) : 0;

  const byRule = (summary?.by_rule || []).map((r, i) => ({
    ...r,
    fill: RULE_COLORS[i % RULE_COLORS.length],
  }));

  const bySeverity = (summary?.by_severity || []).map(s => ({
    ...s,
    fill: SEVERITY_COLORS[s.severity] || '#64748b',
  }));

  return (
    <>
      {/* ── KPI Cards ── */}
      <div className="stats-grid">
        <div className="stat-card accent">
          <span className="stat-label">Records Evaluated</span>
          <span className="stat-value">{totalRecords.toLocaleString()}</span>
          <span className="stat-detail">From latest pipeline run</span>
        </div>
        <div className="stat-card critical">
          <span className="stat-label">Total Exceptions</span>
          <span className="stat-value">{totalExceptions.toLocaleString()}</span>
          <span className="stat-detail">Across {byRule.length} active rules</span>
        </div>
        <div className="stat-card success">
          <span className="stat-label">Exception Rate</span>
          <span className="stat-value">{exceptionRate}%</span>
          <span className="stat-detail">Violations / Records</span>
        </div>
        <div className="stat-card medium">
          <span className="stat-label">Run Status</span>
          <span className="stat-value" style={{ fontSize: 22, textTransform: 'capitalize' }}>
            {run.run_status || 'Unknown'}
          </span>
          <span className="stat-detail">
            {run.run_timestamp ? new Date(run.run_timestamp).toLocaleString() : '—'}
          </span>
        </div>
      </div>

      {/* ── Charts ── */}
      <div className="charts-grid">
        {/* Rule Breakdown Bar Chart */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Exceptions by Rule</span>
          </div>
          {byRule.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={byRule} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis
                  dataKey="rule_id"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                />
                <YAxis
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={48}>
                  {byRule.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="state-container"><div className="state-text">No rule data</div></div>
          )}
        </div>

        {/* Severity Pie Chart */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Severity Distribution</span>
          </div>
          {bySeverity.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={bySeverity}
                  dataKey="count"
                  nameKey="severity"
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={95}
                  paddingAngle={3}
                  stroke="none"
                >
                  {bySeverity.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
                <Legend
                  iconType="circle"
                  iconSize={8}
                  wrapperStyle={{ fontSize: 12, color: '#94a3b8' }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="state-container"><div className="state-text">No severity data</div></div>
          )}
        </div>
      </div>

      {/* ── Top Violators ── */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Top Violators</span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            Employees with most violations
          </span>
        </div>
        {topViolators.length > 0 ? (
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>PSID</th>
                  <th>Employee Name</th>
                  <th>Violations</th>
                </tr>
              </thead>
              <tbody>
                {topViolators.map((v, i) => (
                  <tr key={v.psid} className="clickable" onClick={() => setSelectedViolator(v)}>
                    <td>{i + 1}</td>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{v.psid}</td>
                    <td>{v.name}</td>
                    <td>
                      <span className="severity-badge critical">{v.count}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="state-container"><div className="state-text">No violator data</div></div>
        )}
      </div>

      <ViolatorExceptionsModal 
        violator={selectedViolator} 
        runId={data?.run?.run_id} 
        onClose={() => setSelectedViolator(null)} 
      />
    </>
  );
}
