export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = {
  headers?: Record<string, string>;
  body?: unknown;
};

export async function apiRequest<T>(path: string, method: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(path, {
    method,
    headers: {
      Accept: "application/json",
      ...(options.body === undefined ? {} : { "Content-Type": "application/json" }),
      ...options.headers,
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    let detail = `API request failed: ${path}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      // Keep the generic error when the response is not JSON.
    }
    throw new ApiError(detail, response.status);
  }

  return response.json() as Promise<T>;
}

export function apiGet<T>(path: string, headers?: Record<string, string>): Promise<T> {
  return apiRequest<T>(path, "GET", { headers });
}

export function apiPost<T>(path: string, body: unknown, headers?: Record<string, string>): Promise<T> {
  return apiRequest<T>(path, "POST", { body, headers });
}

export function apiDelete<T>(path: string, headers?: Record<string, string>): Promise<T> {
  return apiRequest<T>(path, "DELETE", { headers });
}
