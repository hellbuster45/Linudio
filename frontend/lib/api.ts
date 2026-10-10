// Base URL of the Linudio backend. Set NEXT_PUBLIC_API_URL in frontend/.env.local to point
// somewhere else (e.g. when the backend runs on another port or machine).
export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

export const apiUrl = (path: string): string => `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;

// The backend reports most failures as `{ error: string }` (HTTP 200) and request-validation
// or HTTPException failures as `{ detail: ... }`. This pulls a readable message out of either.
export const apiErrorMessage = (data: unknown, fallback = "Something went wrong"): string | null => {
    if (!data || typeof data !== "object") return null;
    const record = data as Record<string, unknown>;
    if (typeof record.error === "string") return record.error;
    if (typeof record.detail === "string") return record.detail;
    if (Array.isArray(record.detail)) return fallback;
    return null;
};
