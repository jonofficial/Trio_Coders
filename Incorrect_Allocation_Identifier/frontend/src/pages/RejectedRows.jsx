import { useState, useEffect } from 'react';
import { fetchRejected, fetchRuns } from '../api';

export default function RejectedRows() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [rejectedRows, setRejectedRows] = useState([]);
  const [runId, setRunId] = useState(null);
  
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 50;

  useEffect(() => { loadRejected(); }, []);

  async function loadRejected() {
    setLoading(true);
    setError(null);
    try {
      // Fetch latest run first to get its ID, then fetch rejected rows for that run.
      // If we don't pass a run_id, the backend might fetch all rejected rows or default to none,
      // but the API mapping asks for a run_id if we want specific results.
      const runsRes = await fetchRuns(1);
      const latestRunId = runsRes.data?.runs?.[0]?.run_id || null;
      setRunId(latestRunId);

      const res = await fetchRejected(latestRunId ? { run_id: latestRunId } : {});
      setRejectedRows(res.data.data || []);
    } catch (e) {
      setError(e.message || 'Failed to fetch rejected rows');
    } finally {
      setLoading(false);
    }
  }

  const totalPages = Math.ceil(rejectedRows.length / itemsPerPage);
  const currentData = rejectedRows.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  if (loading) {
    return (
      <div className="state-container">
        <div className="spinner" />
        <div className="state-text">Loading rejected rows...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="state-container">
        <div className="state-icon">❌</div>
        <div className="state-text">{error}</div>
        <button className="btn btn-secondary btn-sm" onClick={loadRejected}>Retry</button>
      </div>
    );
  }

  if (rejectedRows.length === 0) {
    return (
      <div className="state-container">
        <div className="state-icon">✅</div>
        <div className="state-text">No rows were rejected during the data ingestion pipeline.</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Rejected Rows ({rejectedRows.length})</span>
      </div>

      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: 80 }}>Row #</th>
              <th style={{ width: 120 }}>Source</th>
              <th style={{ width: 200 }}>Reason</th>
              <th>Raw Data Preview</th>
            </tr>
          </thead>
          <tbody>
            {currentData.map((row, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 600 }}>{row.row_index}</td>
                <td><span className="severity-badge medium">{row.source}</span></td>
                <td style={{ color: 'var(--color-high)' }}>{row.reason}</td>
                <td style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--text-muted)' }}>
                  {JSON.stringify(row.raw_data).substring(0, 100)}...
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <span>Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, rejectedRows.length)} of {rejectedRows.length} entries</span>
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
    </div>
  );
}
