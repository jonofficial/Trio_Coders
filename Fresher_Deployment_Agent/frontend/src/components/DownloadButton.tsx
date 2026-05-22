interface Props {
  url: string | null;
  label: string;
}

/**
 * Triggers a browser file download using a programmatic anchor click.
 * Uses the full URL path already stored in state (e.g. "/output/file.xlsx").
 */
export function DownloadButton({ url, label }: Props) {
  function handleDownload() {
    if (!url) return;
    const a = document.createElement("a");
    a.href = url;
    a.download = url.split("/").pop() ?? "report.xlsx";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  if (!url) return null;

  return (
    <button
      onClick={handleDownload}
      className="
        flex items-center gap-1.5 px-3 py-1.5 rounded-lg
        text-xs font-medium text-white/60
        border border-white/[0.08] bg-white/[0.02]
        hover:text-white/90 hover:border-white/20 hover:bg-white/[0.05]
        transition-all duration-150 cursor-pointer
      "
      title={`Download ${label}`}
    >
      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
      </svg>
      {label}
    </button>
  );
}
