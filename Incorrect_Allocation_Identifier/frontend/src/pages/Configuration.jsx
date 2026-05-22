import { useState, useEffect } from 'react';
import { fetchConfig } from '../api';

export default function Configuration() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [config, setConfig] = useState(null);

  useEffect(() => { loadConfig(); }, []);

  async function loadConfig() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchConfig();
      setConfig(res.data);
    } catch (e) {
      setError(e.message || 'Failed to fetch configuration');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="state-container">
        <div className="spinner" />
        <div className="state-text">Loading configuration...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="state-container">
        <div className="state-icon">❌</div>
        <div className="state-text">{error}</div>
        <button className="btn btn-secondary btn-sm" onClick={loadConfig}>Retry</button>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="state-container">
        <div className="state-icon">⚙️</div>
        <div className="state-text">Configuration data is empty.</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">System Configuration</span>
      </div>

      <div className="detail-grid">
        <div className="detail-section" style={{ gridColumn: '1 / -1', marginTop: 0, paddingTop: 0, borderTop: 'none' }}>
          <div className="detail-section-title">General Settings</div>
        </div>
        
        <div className="detail-item">
          <span className="detail-label">PSID Field Name</span>
          <span className="detail-value" style={{ fontFamily: 'monospace' }}>{config.psid_field_name}</span>
        </div>
        
        <div className="detail-item">
          <span className="detail-label">Notification Endpoint</span>
          <span className="detail-value" style={{ color: 'var(--accent)' }}>{config.notification_endpoint}</span>
        </div>
        
        <div className="detail-item">
          <span className="detail-label">Database Host</span>
          <span className="detail-value">{config.db_host}</span>
        </div>
        
        <div className="detail-item">
          <span className="detail-label">Database Name</span>
          <span className="detail-value">{config.db_name}</span>
        </div>

        <div className="detail-section" style={{ gridColumn: '1 / -1' }}>
          <div className="detail-section-title">Business Logic Mappings</div>
        </div>

        <div className="detail-item full-width">
          <span className="detail-label">Contractor Codes</span>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 6 }}>
            {(config.contractor_codes || []).map(code => (
              <span key={code} style={{ 
                background: 'var(--bg-elevated)', 
                padding: '4px 10px', 
                borderRadius: '100px',
                fontSize: 12,
                border: '1px solid var(--border-default)'
              }}>
                {code}
              </span>
            ))}
          </div>
        </div>

        <div className="detail-item full-width" style={{ marginTop: 12 }}>
          <span className="detail-label">Support & Sales Roles</span>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 6 }}>
            {(config.support_sales_roles || []).map(role => (
              <span key={role} style={{ 
                background: 'var(--color-medium-bg)', 
                color: 'var(--color-medium)',
                padding: '4px 10px', 
                borderRadius: '100px',
                fontSize: 12,
                border: '1px solid var(--color-medium-border)'
              }}>
                {role}
              </span>
            ))}
          </div>
        </div>

        <div className="detail-section" style={{ gridColumn: '1 / -1' }}>
          <div className="detail-section-title">Exception Rule Definitions</div>
        </div>

        <div className="detail-item full-width">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ background: 'var(--bg-elevated)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>R1: Unassigned with Active Role</span>
                <span className="severity-badge critical">Critical</span>
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Flags employees whose task is "Unassigned" but their project allocation remains active.</div>
            </div>

            <div style={{ background: 'var(--bg-elevated)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>R2: Incorrect Task Tag</span>
                <span className="severity-badge medium">Medium</span>
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Flags Support/Sales roles incorrectly tagged as NE (Billable). They should be NI (Non-Billable).</div>
            </div>

            <div style={{ background: 'var(--bg-elevated)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>R3: Allocation ≠ 100%</span>
                <span className="severity-badge critical">Critical</span>
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Flags any employee whose combined allocation across all projects does not equal exactly 100%.</div>
            </div>

            <div style={{ background: 'var(--bg-elevated)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>R4: Contractor on Bench</span>
                <span className="severity-badge high">High</span>
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Flags 3rd-party contractors or non-employees who are inappropriately marked as being on the bench.</div>
            </div>

            <div style={{ background: 'var(--bg-elevated)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>R5: Onsite on Bench</span>
                <span className="severity-badge high">High</span>
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Flags employees located onsite who are marked as being on the bench instead of allocated to a local project.</div>
            </div>

            <div style={{ background: 'var(--bg-elevated)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>R6: Stale Long Leave</span>
                <span className="severity-badge medium">Medium</span>
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Flags resources on Long Leave where their projected end date has already passed the current system date.</div>
            </div>

            <div style={{ background: 'var(--bg-elevated)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>R7: Missing RSSL</span>
                <span className="severity-badge medium">Medium</span>
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Flags records missing a Resource Based Service Sub Line (RSSL) or mismatched with Sales Order values.</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
