import { useEffect, useState } from 'react'

export function useApi<T>(loader: () => Promise<T>, dependencies: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    let active = true
    setLoading(true); setError('')
    loader().then(value => active && setData(value)).catch(reason => active && setError(reason instanceof Error ? reason.message : 'Unable to load data')).finally(() => active && setLoading(false))
    return () => { active = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies)
  return {data, error, loading, setData}
}
