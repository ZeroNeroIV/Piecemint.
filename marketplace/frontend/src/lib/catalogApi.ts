import axios from 'axios'

import { marketplaceApiPath } from './urls'

/** Dev / local-preview default for when same-origin `/api` is unavailable (vite preview, broken proxy). */
export const MARKETPLACE_DEV_LOOPBACK_ORIGIN = 'http://127.0.0.1:8001' as const

export function marketplaceDirectApiUrl(apiPath: string): string {
  const p = apiPath.startsWith('/') ? apiPath : `/${apiPath}`
  return `${MARKETPLACE_DEV_LOOPBACK_ORIGIN}${p}`
}

/** Browser pointed at localhost in dev OR `vite preview` (PROD bundle, no `/api` proxy). */
export function marketplaceUseLoopbackCandidates(): boolean {
  if (import.meta.env.DEV) return true
  if (typeof window === 'undefined') return false
  const h = window.location.hostname
  return h === 'localhost' || h === '127.0.0.1'
}

/** Same-origin `/api/...` first, then IPv4 loopback (bypasses bad proxies / vite preview without proxy). */
export function marketplaceAxiosCandidates(path: string): string[] {
  const primary = marketplaceApiPath(path)
  if (
    !marketplaceUseLoopbackCandidates() ||
    !primary.startsWith('/api') ||
    primary.startsWith(MARKETPLACE_DEV_LOOPBACK_ORIGIN)
  ) {
    return [primary]
  }
  const direct = marketplaceDirectApiUrl(path)
  return primary === direct ? [primary] : [primary, direct]
}

const RETRY_MS = [0, 280, 700, 1500]

export async function axiosGetMarketplaceJson<T>(apiPath: string): Promise<T> {
  const urls = marketplaceAxiosCandidates(apiPath)
  let lastErr: unknown
  for (const url of urls) {
    for (let i = 0; i < RETRY_MS.length; i++) {
      if (RETRY_MS[i] > 0) {
        await new Promise<void>((r) => {
          window.setTimeout(r, RETRY_MS[i])
        })
      }
      try {
        const res = await axios.get<T>(url, { timeout: 20_000 })
        return res.data
      } catch (e) {
        lastErr = e
      }
    }
  }
  throw lastErr
}

/** fetch() fallback chain for blobs (downloads). */
export async function fetchMarketplaceBlob(apiPath: string): Promise<Response> {
  const urls = marketplaceAxiosCandidates(apiPath)
  let last: Response | undefined
  for (const url of urls) {
    for (let i = 0; i < RETRY_MS.length; i++) {
      if (RETRY_MS[i] > 0) {
        await new Promise<void>((r) => {
          window.setTimeout(r, RETRY_MS[i])
        })
      }
      try {
        const res = await fetch(url)
        if (res.ok) return res
        last = res
      } catch {
        /* try next */
      }
    }
  }
  if (last) return last
  throw new Error('Marketplace fetch failed for all candidates')
}
