import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { addressesApi, ordersApi, paymentsApi, type Address } from '../api'
import { useCart } from '../context/cart-context'
import { formatNaira } from '../lib/format'

const emptyForm = { full_name: '', phone: '', address: '', city: '', state: '' }

export default function Checkout() {
  const { cart, refresh } = useCart()
  const [addresses, setAddresses] = useState<Address[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [formError, setFormError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const [placing, setPlacing] = useState(false)
  const [placeError, setPlaceError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    Promise.all([refresh(), addressesApi.list()])
      .then(([, list]) => {
        if (cancelled) return
        setAddresses(list)
        if (list.length > 0) setSelectedId(list[0].id)
        else setShowForm(true)
      })
      .catch(() => {
        if (!cancelled) setError('Could not load checkout.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [refresh])

  const saveAddress = async (e: FormEvent) => {
    e.preventDefault()
    setFormError(null)
    setSaving(true)
    try {
      const created = await addressesApi.create(form)
      setAddresses((prev) => [...prev, created])
      setSelectedId(created.id)
      setForm(emptyForm)
      setShowForm(false)
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Could not save address.')
    } finally {
      setSaving(false)
    }
  }

  const placeOrder = async () => {
    if (!selectedId || !cart) return
    setPlaceError(null)
    setPlacing(true)
    let order
    try {
      order = await ordersApi.checkout(selectedId)
    } catch (err) {
      setPlaceError(err instanceof Error ? err.message : 'Could not place order.')
      setPlacing(false)
      return
    }
    try {
      const { checkout_url } = await paymentsApi.initiate(order.id)
      window.location.assign(checkout_url)
    } catch {
      await refresh()
      setPlaceError(
        `Order #${order.id} was placed, but payment couldn't start. Open Orders to retry.`,
      )
      setPlacing(false)
    }
  }

  if (loading) return <div className="page-loading">Loading checkout…</div>
  if (error) return <div className="page-error">{error}</div>

  if (!cart || cart.items.length === 0) {
    return (
      <div className="page">
        <h1>Checkout</h1>
        <p className="empty">
          Your cart is empty. <Link to="/products">Browse products</Link>
        </p>
      </div>
    )
  }

  return (
    <div className="page checkout-page">
      <h1>Checkout</h1>

      <section className="checkout-section">
        <h2>Shipping address</h2>
        <div className="address-list">
          {addresses.map((a) => (
            <label
              key={a.id}
              className={`address-card${selectedId === a.id ? ' selected' : ''}`}
            >
              <input
                type="radio"
                name="address"
                checked={selectedId === a.id}
                onChange={() => setSelectedId(a.id)}
              />
              <span>
                <strong>{a.full_name}</strong>
                <br />
                {a.address}, {a.city}, {a.state}
              </span>
            </label>
          ))}
        </div>

        {showForm ? (
          <form className="addr-form" onSubmit={saveAddress}>
            <h3>New address</h3>
            {formError && <div className="auth-error">{formError}</div>}
            <div className="addr-grid">
              <input
                required
                placeholder="Full name"
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              />
              <input
                required
                placeholder="Phone"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
              <input
                required
                placeholder="Street address"
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
              />
              <input
                required
                placeholder="City"
                value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
              />
              <input
                required
                placeholder="State"
                value={form.state}
                onChange={(e) => setForm({ ...form, state: e.target.value })}
              />
            </div>
            <button type="submit" disabled={saving}>
              {saving ? 'Saving…' : 'Save address'}
            </button>
          </form>
        ) : (
          <button className="btn-link" onClick={() => setShowForm(true)}>
            + Add new address
          </button>
        )}
      </section>

      <section className="checkout-section">
        <h2>Order summary</h2>
        <ul className="summary-items">
          {cart.items.map((item) => (
            <li key={item.id}>
              <span>
                {item.product_name} × {item.quantity}
              </span>
              <span>{formatNaira(item.sub_total)}</span>
            </li>
          ))}
        </ul>
        <div className="cart-total">
          Total <strong>{formatNaira(cart.total)}</strong>
        </div>
      </section>

      {placeError && <div className="auth-error">{placeError}</div>}

      <button
        className="checkout-btn wide"
        onClick={placeOrder}
        disabled={placing || selectedId === null}
      >
        {placing ? 'Redirecting to payment…' : `Pay ${formatNaira(cart.total)}`}
      </button>
    </div>
  )
}
