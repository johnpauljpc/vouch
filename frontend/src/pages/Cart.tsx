import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../api'
import { useCart } from '../context/cart-context'
import { formatNaira } from '../lib/format'

export default function Cart() {
  const { cart, refresh, updateItem, removeItem, clear } = useCart()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<number | 'clear' | null>(null)
  const [itemError, setItemError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    refresh()
      .catch(() => {
        if (!cancelled) setError('Could not load your cart.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [refresh])

  if (loading) return <div className="page-loading">Loading cart…</div>
  if (error) return <div className="page-error">{error}</div>

  if (!cart || cart.items.length === 0) {
    return (
      <div className="page">
        <h1>Your cart</h1>
        <p className="empty">
          Your cart is empty. <Link to="/products">Browse products</Link>
        </p>
      </div>
    )
  }

  const run = async (key: number | 'clear', action: () => Promise<void>) => {
    setBusyId(key)
    setItemError(null)
    try {
      await action()
    } catch (err) {
      setItemError(
        err instanceof ApiError ? friendly(err) : 'Something went wrong. Try again.',
      )
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="page">
      <div className="cart-head">
        <h1>Your cart</h1>
        <button
          className="btn-link"
          disabled={busyId !== null}
          onClick={() => run('clear', clear)}
        >
          {busyId === 'clear' ? 'Clearing…' : 'Clear cart'}
        </button>
      </div>

      {itemError && <div className="auth-error">{itemError}</div>}

      <ul className="cart-list">
        {cart.items.map((item) => (
          <li key={item.id} className="cart-row">
            <div className="cart-item-info">
              <span className="cart-item-name">{item.product_name}</span>
              <span className="cart-item-unit">{formatNaira(item.price)} each</span>
            </div>
            <div className="qty-stepper">
              <button
                aria-label="Decrease quantity"
                disabled={busyId === item.id || item.quantity <= 1}
                onClick={() =>
                  run(item.id, () => updateItem(item.id, item.quantity - 1))
                }
              >
                −
              </button>
              <span>{item.quantity}</span>
              <button
                aria-label="Increase quantity"
                disabled={busyId === item.id}
                onClick={() =>
                  run(item.id, () => updateItem(item.id, item.quantity + 1))
                }
              >
                +
              </button>
            </div>
            <span className="cart-item-subtotal">
              {formatNaira(item.sub_total ?? Number(item.price) * item.quantity)}
            </span>
            <button
              className="btn-link remove-item"
              disabled={busyId === item.id}
              onClick={() => run(item.id, () => removeItem(item.id))}
            >
              Remove
            </button>
          </li>
        ))}
      </ul>

      <div className="cart-summary">
        <div className="cart-total">
          Total <strong>{formatNaira(cart.total)}</strong>
        </div>
        <Link to="/checkout" className="checkout-btn">
          Proceed to checkout
        </Link>
      </div>
    </div>
  )
}

function friendly(err: ApiError): string {
  try {
    const parsed = JSON.parse(err.message)
    const q = parsed?.quantity
    if (typeof q === 'string') return q
    if (parsed?.detail) return parsed.detail
  } catch {
    /* plain message */
  }
  return err.message
}
