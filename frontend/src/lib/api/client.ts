import axios, {
  AxiosError,
  AxiosHeaders,
  type InternalAxiosRequestConfig,
} from "axios"

import { siteConfig } from "@/config/site"
import { tokenStorage } from "@/features/auth/token-storage"

export interface ApiErrorPayload {
  detail?: string
  message?: string
}

export interface NormalizedApiError {
  message: string
  status: number | null
  code: string | null
  isNetworkError: boolean
  kind: ApiErrorKind
}

export type ApiErrorKind =
  | "validation"
  | "authentication"
  | "authorization"
  | "not_found"
  | "conflict"
  | "rate_limit"
  | "timeout"
  | "network"
  | "backend"
  | "malformed_response"
  | "unknown"

export const apiClient = axios.create({
  baseURL: siteConfig.apiUrl,
  timeout: 20_000,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
})

function attachBearerToken(
  config: InternalAxiosRequestConfig,
): InternalAxiosRequestConfig {
  const token = tokenStorage.get()

  if (!token) {
    return config
  }

  const headers = AxiosHeaders.from(config.headers)
  headers.set("Authorization", `Bearer ${token}`)
  config.headers = headers

  return config
}

apiClient.interceptors.request.use(attachBearerToken)
apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (
      axios.isAxiosError(error) &&
      error.response?.status === 401 &&
      !error.config?.url?.includes("/auth/login") &&
      tokenStorage.get()
    ) {
      tokenStorage.clear()
      window.dispatchEvent(new Event("auth:unauthorized"))
    }
    return Promise.reject(error)
  },
)

export function normalizeApiError(
  error: unknown,
  fallbackMessage = "Something went wrong. Please try again.",
): NormalizedApiError {
  if (!axios.isAxiosError<ApiErrorPayload>(error)) {
    return {
      message:
        error instanceof Error && error.message
          ? error.message
          : fallbackMessage,
      status: null,
      code: null,
      isNetworkError: false,
      kind: "unknown",
    }
  }

  const axiosError = error as AxiosError<ApiErrorPayload>
  const responseMessage =
    axiosError.response?.data?.detail ??
    axiosError.response?.data?.message

  const status = axiosError.response?.status ?? null
  const kind: ApiErrorKind =
    axiosError.code === "ECONNABORTED" || axiosError.code === "ETIMEDOUT"
      ? "timeout"
      : axiosError.response === undefined
        ? "network"
        : status === 400 || status === 422
          ? "validation"
          : status === 401
            ? "authentication"
            : status === 403
              ? "authorization"
              : status === 404
                ? "not_found"
                : status === 409
                  ? "conflict"
                  : status === 429
                    ? "rate_limit"
                    : status !== null && status >= 500
                      ? "backend"
                      : "unknown"

  return {
    message: responseMessage ?? fallbackMessage,
    status,
    code: axiosError.code ?? null,
    isNetworkError: axiosError.response === undefined,
    kind,
  }
}

export function shouldRetryApiError(
  failureCount: number,
  error: unknown,
) {
  if (failureCount >= 2) return false
  const normalized = error as Partial<NormalizedApiError>
  return ["network", "timeout", "backend"].includes(normalized.kind ?? "")
}
