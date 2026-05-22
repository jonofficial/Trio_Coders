import { useState, useEffect, useMemo } from 'react';
import { fetchExceptions, getExportUrl, fetchRuns } from '../api';

function ExceptionDetailModal({ exc, onClose }) {
  if (!exc) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div className="modal-title">Exception Detail — {exc.rule_id}</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
              PSID: {exc.psid} | {exc.employee_name}
            </div>
          </div>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        
        <div className="modal-body">
          {/* Main Issue */}
          <div style={{
            background: 'var(--bg-elevated)', borderLeft: '4px solid var(--accent)',
            padding: 16, borderRadius: 'var(--radius-sm)', marginBottom: 24
          }}>
            <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 8, color: 'var(--text-primary)' }}>
              {exc.rule_name}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 12 }}>
              {exc.exception_reason}
            </div>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-high)' }}>
              Recommended Action: <span style={{ fontWeight: 400, color: 'var(--text-secondary)' }}>{exc.recommended_action}</span>
            </div>
          </div>

          <div className="detail-grid">
            <div className="detail-section full-width">
              <div className="detail-section-title">Employee Context</div>
            </div>
            <div className="detail-item">
              <span className="detail-label">Employee</span>
              <span className="detail-value">{exc.employee_name} ({exc.psid})</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Status & Grade</span>
              <span className="detail-value">{exc.employee_status} / {exc.grade}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Mode of Hire</span>
              <span className="detail-value">{exc.mode_of_hire}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Resource Manager (RM)</span>
              <span className="detail-value">{exc.rm}</span>
            </div>

            <div className="detail-section full-width">
              <div className="detail-section-title">Assignment Context</div>
            </div>
            <div className="detail-item">
              <span className="detail-label">Project</span>
              <span className="detail-value">{exc.project_name} ({exc.project_id})</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Task Type</span>
              <span className="detail-value">{exc.task_type}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Role</span>
              <span className="detail-value">{exc.project_role}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Allocation</span>
              <span className="detail-value">Row: {exc.row_allocation_pct}% | Total: {exc.total_allocation_pct}%</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Location / Onsite</span>
              <span className="detail-value">{exc.location_category} / {exc.onsite_status}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Bench Status</span>
              <span className="detail-value">{exc.bench_flag ? 'Yes' : 'No'}</span>
            </div>

            <div className="detail-section full-width">
              <div className="detail-section-title">Compliance Fields</div>
            </div>
            <div className="detail-item">
              <span className="detail-label">RIS SSL</span>
              <span className="detail-value">{exc.resource_based_ssl}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">SO SSL</span>
              <span className="detail-value">{exc.so_resource_base_ssl}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Resource End Date</span>
              <span className="detail-value">
                {exc.resource_end_date ? new Date(exc.resource_end_date).toLocaleDateString() : 'N/A'}
                {exc.days_past_end_date !== null && exc.days_past_end_date !== 'N/A' && ` (${exc.days_past_end_date} days past)`}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Exceptions() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exceptions, setExceptions] = useState([]);
  const [runId, setRunId] = useState(null);
  
  const [filterRule, setFilterRule] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 50;

  const [selectedExc, setSelectedExc] = useState(null);

  useEffect(() => { loadExceptions(); }, []);

  async function loadExceptions() {
    setLoading(true);
    setError(null);
    try {
      // Per instructions, we fetch the latest run to grab its export URL runId, 
      // but fetch the latest exceptions without filtering by runId in the api call to fulfill "no run filters" rule for UI.
      const runsRes = await fetchRuns(1);
      const latestRunId = runsRes.data?.runs?.[0]?.run_id || null;
      setRunId(latestRunId);

      // limit high enough to get all typical exceptions for the run (max 5000 allowed by backend)
      const res = await fetchExceptions({ limit: 5000 });
      setExceptions(res.data.exceptions || []);
    } catch (e) {
      setError(e.message || 'Failed to fetch exceptions');
    } finally {
      setLoading(false);
    }
  }

  // Derived state
  const filteredData = useMemo(() => {
    return exceptions.filter(e => {
      const matchRule = filterRule ? e.rule_id === filterRule : true;
      const matchSev = filterSeverity ? e.severity === filterSeverity : true;
      
      const search = searchQuery.toLowerCase();
      const matchSearch = search ? (
        (e.psid || '').toLowerCase().includes(search) ||
        (e.employee_name || '').toLowerCase().includes(search) ||
        (e.project_id || '').toLowerCase().includes(search) ||
        (e.project_name || '').toLowerCase().includes(search)
      ) : true;

      return matchRule && matchSev && matchSearch;
    });
  }, [exceptions, filterRule, filterSeverity, searchQuery]);

  const totalPages = Math.ceil(filteredData.length / itemsPerPage);
  const currentData = filteredData.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  const ruleOptions = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7'];
  const severityOptions = ['Critical', 'High', 'Medium'];

  if (loading) {
    return (
      <div className="state-container">
        <div className="spinner" />
        <div className="state-text">Loading exceptions...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="state-container">
        <div className="state-icon">❌</div>
        <div className="state-text">{error}</div>
        <button className="btn btn-secondary btn-sm" onClick={loadExceptions}>Retry</button>
      </div>
    );
  }

  if (exceptions.length === 0) {
    return (
      <div className="state-container">
        <div className="state-icon">✅</div>
        <div className="state-text">No exceptions found. The allocation data is perfectly clean.</div>
      </div>
    );
  }

  return (
    <>
      <div className="card">
        <div className="card-header">
          <span className="card-title">Exception Records ({filteredData.length})</span>
          {runId && (
            <a href={getExportUrl(runId)} className="btn btn-primary btn-sm" download>
              ⬇ Export CSV
            </a>
          )}
        </div>

        {/* Filters */}
        <div className="filters-bar">
          <div className="form-group">
            <span className="form-label">Search</span>
            <input 
              type="text" 
              className="form-input" 
              placeholder="PSID, Name, Project..." 
              value={searchQuery}
              onChange={e => { setSearchQuery(e.target.value); setCurrentPage(1); }}
              style={{ width: 220 }}
            />
          </div>
          <div className="form-group">
            <span className="form-label">Rule</span>
            <select 
              className="form-select"
              value={filterRule}
              onChange={e => { setFilterRule(e.target.value); setCurrentPage(1); }}
            >
              <option value="">All Rules</option>
              {ruleOptions.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div className="form-group">
            <span className="form-label">Severity</span>
            <select 
              className="form-select"
              value={filterSeverity}
              onChange={e => { setFilterSeverity(e.target.value); setCurrentPage(1); }}
            >
              <option value="">All Severities</option>
              {severityOptions.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>

        {/* Table */}
        {filteredData.length > 0 ? (
          <>
            <div className="data-table-wrapper" style={{ maxHeight: '60vh', overflowY: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Rule ID</th>
                    <th>Severity</th>
                    <th>PSID</th>
                    <th>Employee Name</th>
                    <th>Task</th>
                    <th>Alloc %</th>
                    <th>Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {currentData.map(exc => (
                    <tr key={exc.exception_id} className="clickable" onClick={() => setSelectedExc(exc)}>
                      <td style={{ fontWeight: 600 }}>{exc.rule_id}</td>
                      <td>
                        <span className={`severity-badge ${exc.severity.toLowerCase()}`}>
                          {exc.severity}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-primary)' }}>{exc.psid}</td>
                      <td>{exc.employee_name}</td>
                      <td>{exc.task_type}</td>
                      <td>{exc.total_allocation_pct}%</td>
                      <td title={exc.exception_reason}>{exc.exception_reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="pagination">
                <span>Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, filteredData.length)} of {filteredData.length} entries</span>
                <div className="pagination-controls">
                  <button 
                    className="page-btn" 
                    disabled={currentPage === 1}
                    onClick={() => setCurrentPage(p => p - 1)}
                  >
                    Prev
                  </button>
                  <button 
                    className="page-btn" 
                    disabled={currentPage === totalPages}
                    onClick={() => setCurrentPage(p => p + 1)}
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="state-container" style={{ padding: '40px 0' }}>
            <div className="state-text">No exceptions match your filters.</div>
          </div>
        )}
      </div>

      <ExceptionDetailModal exc={selectedExc} onClose={() => setSelectedExc(null)} />
    </>
  );
}
