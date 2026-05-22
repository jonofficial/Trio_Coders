import { useState, useCallback, useEffect } from "react";
import type { PipelineState } from "../types";
import { triggerPipeline, fetchExcelFile } from "../services/api";
import {
  parsePyramidExcel,
  parseSuggestionsExcel,
  computeSummary,
} from "../services/excelParser";

const STORAGE_KEY = "lastRun";

const INITIAL_STATE: PipelineState = {
  status: "idle",
  error: null,
  pyramidData: [],
  suggestionsData: [],
  summary: null,
};

/** Fetch + parse both Excel files from their full URL paths. */
async function loadFromPaths(
  pyramidPath: string,
  suggestionsPath: string
): Promise<Pick<PipelineState, "pyramidData" | "suggestionsData" | "summary">> {
  const [pyramidBuffer, suggestionsBuffer] = await Promise.all([
    fetchExcelFile(pyramidPath),
    fetchExcelFile(suggestionsPath),
  ]);

  const pyramidData = parsePyramidExcel(pyramidBuffer);
  const suggestionsData = parseSuggestionsExcel(suggestionsBuffer);

  if (pyramidData.length === 0) {
    throw new Error("Excel files were empty — no project data found");
  }

  return { pyramidData, suggestionsData, summary: computeSummary(pyramidData, suggestionsData) };
}

export function usePipeline() {
  const [state, setState] = useState<PipelineState>(INITIAL_STATE);
  const [pyramidPath, setPyramidPath] = useState<string | null>(null);
  const [suggestionsPath, setSuggestionsPath] = useState<string | null>(null);

  // ── On mount: restore from localStorage if a previous run exists ──────
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return;

    let paths: { pyramid_path: string; suggestions_path: string };
    try {
      paths = JSON.parse(stored);
    } catch {
      localStorage.removeItem(STORAGE_KEY);
      return;
    }

    if (!paths.pyramid_path || !paths.suggestions_path) {
      localStorage.removeItem(STORAGE_KEY);
      return;
    }

    setState((prev) => ({ ...prev, status: "loading" }));

    loadFromPaths(paths.pyramid_path, paths.suggestions_path)
      .then(({ pyramidData, suggestionsData, summary }) => {
        setPyramidPath(paths.pyramid_path);
        setSuggestionsPath(paths.suggestions_path);
        setState({ status: "success", error: null, pyramidData, suggestionsData, summary });
      })
      .catch(() => {
        localStorage.removeItem(STORAGE_KEY);
        setState(INITIAL_STATE);
      });
  }, []);

  // ── Run the pipeline ──────────────────────────────────────────────────
  const run = useCallback(async () => {
    setState({ ...INITIAL_STATE, status: "loading", error: null });

    try {
      const response = await triggerPipeline();

      if (!response.pyramid_path || !response.suggestions_path) {
        setState((prev) => ({
          ...prev,
          status: "error",
          error: "Pipeline completed but no output files were generated",
        }));
        return;
      }

      // Persist paths for next app load
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          pyramid_path: response.pyramid_path,
          suggestions_path: response.suggestions_path,
        })
      );

      setPyramidPath(response.pyramid_path);
      setSuggestionsPath(response.suggestions_path);

      const { pyramidData, suggestionsData, summary } = await loadFromPaths(
        response.pyramid_path,
        response.suggestions_path
      );

      setState({ status: "success", error: null, pyramidData, suggestionsData, summary });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "An unexpected error occurred";
      setState((prev) => ({ ...prev, status: "error", error: message }));
    }
  }, []);

  // ── Reset: clear state AND localStorage ──────────────────────────────
  const reset = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setPyramidPath(null);
    setSuggestionsPath(null);
    setState(INITIAL_STATE);
  }, []);

  return { ...state, pyramidPath, suggestionsPath, run, reset };
}
