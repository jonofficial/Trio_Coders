import axios from "axios";
import type { PipelineResponse } from "../types";

// Vite proxy forwards /run-pipeline and /output to the backend
const api = axios.create({ baseURL: "/" });

/**
 * Trigger the FDA pipeline (synchronous — blocks until complete).
 * Returns { pyramid_path, suggestions_path } as full URL paths.
 */
export async function triggerPipeline(): Promise<PipelineResponse> {
  const { data } = await api.post<PipelineResponse>("/run-pipeline");
  return data;
}

/**
 * Fetch an Excel file by its full URL path (e.g. "/output/file.xlsx").
 */
export async function fetchExcelFile(path: string): Promise<ArrayBuffer> {
  const { data } = await api.get(path, { responseType: "arraybuffer" });
  return data;
}
