/**
 * Centralised HTTP client for API calls.
 *
 * Every request/response goes through `fetchApi` so error handling,
 * header management, and response parsing are consistent everywhere.
 */

export class ApiError extends Error {
  details: string[] | null;
  status: number;

  constructor(message: string, status: number, details: string[] | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

async function parseErrorBody(res: Response): Promise<{ message: string; details: string[] | null }> {
  try {
    const body = await res.json();
    if (body?.detail) {
      if (typeof body.detail === "string") {
        return { message: body.detail, details: null };
      }
      if (body.detail.error) {
        const msg = body.detail.details?.length
          ? `${body.detail.error}: ${body.detail.details.join(", ")}`
          : body.detail.error;
        return { message: msg, details: body.detail.details ?? null };
      }
    }
  } catch {
    // body wasn't JSON
  }
  return { message: `Request failed with status ${res.status}`, details: null };
}

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

interface FetchApiOptions {
  method?: HttpMethod;
  body?: unknown;
  signal?: AbortSignal;
}

export async function fetchApi<T = void>(url: string, options: FetchApiOptions = {}): Promise<T> {
  const { method = "GET", body, signal } = options;

  const headers: Record<string, string> = {};
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal,
  });

  if (!res.ok) {
    const { message, details } = await parseErrorBody(res);
    throw new ApiError(message, res.status, details);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}
