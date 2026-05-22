import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { triggerPipeline, fetchRunStatus } from '../api';

const PIPELINE_STEPS = [
  { id: 'fetch', label: 'Fetch Data', apiLabel: 'Fetch Data', desc: 'Ingesting RIS and SO datasets' },
  { id: 'clean', label: 'Clean Data', apiLabel: 'Clean Data', desc: 'Standardizing fields and handling duplicates' },
  { id: 'aggregate', label: 'Aggregate Allocation', apiLabel: 'Aggregate Allocation', desc: 'Merging records by PSID' },
  { id: 'validate', label: 'Validate Rules (R1–R7)', apiLabel: 'Validate Rules (R1–R7)', desc: 'Applying business compliance logic' },
  { id: 'report', label: 'Generate Report', apiLabel: 'Generate Report', desc: 'Creating formatted exception files' },
  { id: 'store', label: 'Store Results', apiLabel: 'Store Results', desc: 'Persisting audit logs and records' },
];

function ExecutionTimeline({ currentStepLabel, status }) {
  const currentStepIndex = useMemo(() => {
    if (status === 'success') return PIPELINE_STEPS.length;
    return PIPELINE_STEPS.findIndex(s => s.apiLabel === currentStepLabel);
  }, [currentStepLabel, status]);

  return (
    <div className="timeline-container">
      {PIPELINE_STEPS.map((step, index) => {
        const isCompleted = index < currentStepIndex || status === 'success';
        const isRunning = index === currentStepIndex && status !== 'success';
        const stateClass = isCompleted ? 'completed' : isRunning ? 'running' : 'pending';

        return (
          <div key={step.id} className={`timeline-step ${stateClass}`}>
            <div className="timeline-indicator">
              {isCompleted ? '✓' : <div className="timeline-indicator-inner" />}
            </div>
            <div className="timeline-content">
              <div className="timeline-title">{step.label}</div>
              <div className="timeline-desc">{step.desc}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function TriggerRun() {
  const navigate = useNavigate();
  
  const [risPath, setRisPath] = useState('');
  const [soPath, setSoPath] = useState('');
  const [useDefaultData, setUseDefaultData] = useState(true);
  
  const [status, setStatus] = useState('idle'); // idle | starting | polling | success | error
  const [errorMsg, setErrorMsg] = useState(null);
  const [tempRunId, setTempRunId] = useState(null);
  const [progressData, setProgressData] = useState(null);
  const [startTime, setStartTime] = useState(null);
  const [endTime, setEndTime] = useState(null);

  // Poll status when a run is in progress
  useEffect(() => {
    let interval;
    if (status === 'polling' && tempRunId) {
      interval = setInterval(async () => {
        try {
          const res = await fetchRunStatus(tempRunId);
          const data = res.data;
          setProgressData(data);
          
          if (data.status === 'success' || data.status === 'completed') {
            setEndTime(Date.now());
            setStatus('success');
            setTimeout(() => {
              navigate('/'); // redirect to dashboard on success
            }, 3000);
          } else if (data.status === 'error' || data.status === 'failed') {
            setStatus('error');
            setErrorMsg(data.error_message || 'Pipeline failed during execution.');
          }
        } catch (e) {
          console.error("Polling error:", e);
        }
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [status, tempRunId, navigate]);

  const handleTrigger = async () => {
    setStatus('starting');
    setErrorMsg(null);
    setProgressData(null);
    setStartTime(Date.now());
    setEndTime(null);
    
    try {
      const payload = useDefaultData 
        ? {} 
        : { ris_path: risPath, so_path: soPath };
        
      const res = await triggerPipeline(payload);
      
      if (res.data && res.data.run_id) {
        setTempRunId(res.data.run_id);
        setStatus('polling');
      } else {
        throw new Error("Invalid response format: Missing run_id");
      }
    } catch (e) {
      setStatus('error');
      setErrorMsg(e.response?.data?.detail || e.message || 'Failed to trigger pipeline');
    }
  };

  const duration = endTime && startTime ? ((endTime - startTime) / 1000).toFixed(1) : null;

  return (
    <div className="card" style={{ maxWidth: 600, margin: '0 auto' }}>
      <div className="card-header">
        <span className="card-title">Trigger IAI Pipeline</span>
        {status === 'polling' && progressData?.progress_pct && (
          <span className="severity-badge medium">{progressData.progress_pct}%</span>
        )}
      </div>
      
      {(status === 'idle' || status === 'error') && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          
          <div style={{ background: 'var(--bg-elevated)', padding: 16, borderRadius: 'var(--radius-sm)' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
              <input 
                type="checkbox" 
                checked={useDefaultData} 
                onChange={e => setUseDefaultData(e.target.checked)} 
              />
              <span style={{ fontSize: 13, fontWeight: 500 }}>Use default configuration data paths</span>
            </label>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, paddingLeft: 24 }}>
              The backend will use paths configured in its environment or internal configuration.
            </div>
          </div>

          {!useDefaultData && (
            <>
              <div className="form-group">
                <span className="form-label">RIS Data Path (Absolute)</span>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="e.g. C:\Data\RIS.xlsx"
                  value={risPath}
                  onChange={e => setRisPath(e.target.value)}
                />
              </div>
              <div className="form-group">
                <span className="form-label">SO Data Path (Absolute)</span>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="e.g. C:\Data\SO.xlsx"
                  value={soPath}
                  onChange={e => setSoPath(e.target.value)}
                />
              </div>
            </>
          )}

          {status === 'error' && (
            <div style={{ padding: 12, background: 'var(--color-critical-bg)', color: 'var(--color-critical)', borderRadius: 'var(--radius-sm)', fontSize: 13, border: '1px solid var(--color-critical-border)' }}>
              <strong>Error:</strong> {errorMsg}
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 10 }}>
            <button 
              className="btn btn-primary" 
              onClick={handleTrigger}
              disabled={!useDefaultData && (!risPath || !soPath)}
            >
              Start Analysis Run
            </button>
          </div>
        </div>
      )}

      {(status === 'starting' || status === 'polling' || status === 'success') && (
        <div style={{ padding: '10px 0' }}>
          <div style={{ marginBottom: 24 }}>
            <h3 style={{ marginBottom: 6, fontSize: 18 }}>Pipeline Execution</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
              {status === 'success' 
                ? `Workflow completed successfully in ${duration}s.` 
                : 'The backend is processing the data through our multi-stage compliance engine.'}
            </p>
          </div>
          
          <ExecutionTimeline 
            currentStepLabel={progressData?.current_step} 
            status={status} 
          />

          {status === 'polling' && progressData?.progress_pct && (
             <div style={{ marginTop: 20 }}>
                <div className="progress-bar-track">
                  <div 
                    className="progress-bar-fill" 
                    style={{ width: `${progressData.progress_pct}%` }}
                  ></div>
                </div>
             </div>
          )}
        </div>
      )}
    </div>
  );
}
