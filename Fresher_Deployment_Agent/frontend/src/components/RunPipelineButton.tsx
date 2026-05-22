import type { PipelineStatus } from "../types";

interface Props {
  status: PipelineStatus;
  onRun: () => void;
  onReset: () => void;
}

export function RunPipelineButton({ status, onRun, onReset }: Props) {
  const isLoading = status === "loading";
  const isComplete = status === "success" || status === "error";

  return (
    <div className="flex items-center gap-4">
      <button
        id="run-pipeline-btn"
        onClick={onRun}
        disabled={isLoading}
        className={`
          relative group px-8 py-3.5 rounded-xl font-semibold text-sm tracking-wide
          transition-all duration-300 cursor-pointer
          ${
            isLoading
              ? "bg-white/5 text-white/30 border border-white/10 cursor-not-allowed"
              : "bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/40 hover:scale-[1.02] active:scale-[0.98]"
          }
        `}
      >
        {isLoading ? (
          <span className="flex items-center gap-3">
            <svg
              className="w-4 h-4 animate-spin"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="3"
                strokeLinecap="round"
                className="opacity-20"
              />
              <path
                d="M12 2a10 10 0 0 1 10 10"
                stroke="currentColor"
                strokeWidth="3"
                strokeLinecap="round"
              />
            </svg>
            Running Pipeline…
          </span>
        ) : (
          <span className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 3l14 9-14 9V3z" />
            </svg>
            Run Pipeline
          </span>
        )}
      </button>

      {isComplete && (
        <button
          id="reset-btn"
          onClick={onReset}
          className="px-5 py-3 rounded-xl text-sm font-medium text-white/50 border border-white/10 hover:text-white/80 hover:border-white/20 transition-all duration-200 cursor-pointer"
        >
          Reset
        </button>
      )}
    </div>
  );
}
