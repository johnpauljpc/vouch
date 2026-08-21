import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError, ordersApi, paymentsApi, type Order } from '../api'
import { formatNaira } from '../lib/format'

export default function Orders() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ordersApi
      .list()
      .then((data) => {
        if (!cancelled) setOrders(data)
      })
      .catch(() => {
        if (!cancelled) setError('Could not load your orders.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const reload = async () => {
    setOrders(await ordersApi.list())
  }

  const payNow = async (o: Order) => {
    setBusyId(o.id)
    setActionError(null)
    try {
      const { checkout_url } = await paymentsApi.initiate(o.id)
      window.location.assign(checkout_url)
    } catch (err) {
      setActionError(err instanceof ApiError ? friendly(err) : 'Payment failed to start.')
      setBusyId(null)
    }
  }

  const cancel = async (o: Order) => {
    setBusyId(o.id)
    setActionError(null)
    try {
      await ordersApi.cancel(o.id)
      await reload()
    } catch (err) {
      setActionError(err instanceof ApiError ? friendly(err) : 'Could not cancel.')
    } finally {
      setBusyId(null)
    }
  }

  if (loading) return <div className="page-loading">Loading orders…</div>
  if (error) return <div className="page-error">{error}</div>

  return (
    <div className="page">
      <h1>Your orders</h1>

      {actionError && <div className="auth-error">{actionError}</div>}

      {orders.length === 0 ? (
        <p className="empty">
          No orders yet. <Link to="/products">Start shopping</Link>
        </p>
      ) : (
        <ul className="orders-list">
          {orders.map((o) => (
            <li key={o.id} className="order-card">
              <div className="order-head">
                <span className="order-id">Order #{o.id}</span>
                <span className="order-date">
                  {new Date(o.created_at).toLocaleString()}
                </span>
                <span className={`stock-badge ${badgeClass(o.status, o.is_paid)}`}>
                  {badgeLabel(o.status, o.is_paid)}
                </span>
              </div>
              <ul className="order-items">
                {(o.items ?? []).map((it) => (
                  <li key={it.id}>
                    {it.product_name} × {it.quantity}
                  </li>
                ))}
              </ul>
              <div className="order-foot">
                <strong>{formatNaira(o.total_amount)}</strong>
                <div className="order-actions">
                  {!o.is_paid && o.status === 'pending' && (
                    <>
                      <button
                        className="checkout-btn"
                        disabled={busyId === o.id}
                        onClick={() => payNow(o)}
                      >
                        {busyId === o.id ? 'Redirecting…' : 'Pay now'}
                      </button>
                      <button
                        className="btn-link"
                        disabled={busyId === o.id}
                        onClick={() => cancel(o)}
                      >
                        Cancel
                      </button>
                    </>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function badgeLabel(status: string, isPaid: boolean): string {
  if (isPaid || status === 'paid') return 'Paid'
  switch (status) {
    case 'pending':
      return 'Awaiting payment'
    case 'delivered':
      return 'Delivered'
    case 'cancelled':
      return 'Cancelled'
    case 'failed':
      return 'Failed'
    default:
      return status
  }
}

function badgeClass(status: string, isPaid: boolean): string {
  if (isPaid || status === 'paid') return ''
  if (status === 'delivered') return ''
  if (status === 'pending') return 'low'
  return 'out'
}

function friendly(err: ApiError): string {
  try {
    const parsed = JSON.parse(err.message)
    if (parsed?.detail) return parsed.detail
    if (typeof parsed === 'string') return parsed
  } catch {
    /* plain */
  }
  return err.message
}
