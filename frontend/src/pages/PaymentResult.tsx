import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { paymentsApi } from '../api'

type ResultState = 'checking' | 'paid' | 'unpaid' | 'error'

export default function PaymentResult() {
  const [params] = useSearchParams()
  const reference = params.get('reference')
  const callbackStatus = params.get('status')
  const [state, setState] = useState<ResultState>(reference ? 'checking' : 'error')

  useEffect(() => {
    if (!reference) return
    let cancelled = false
    paymentsApi
      .verify(reference)
      .then((res) => {
        if (!cancelled) setState(res.order_status === 'paid' ? 'paid' : 'unpaid')
      })
      .catch(() => {
        if (!cancelled) {
          setState(callbackStatus === 'success' ? 'paid' : 'error')
        }
      })
    return () => {
      cancelled = true
    }
  }, [reference, callbackStatus])

  return (
    <div className="page payment-result">
      {state === 'checking' && <p className="result-msg">Confirming your payment…</p>}

      {state === 'paid' && (
        <>
          <div className="result-icon success">✓</div>
          <h1>Payment successful</h1>
          <p className="result-msg">
            Thank you! Your order is confirmed and your receipt is on its way to your
            email.
          </p>
          <Link className="checkout-btn" to="/products">
            Continue shopping
          </Link>
        </>
      )}

      {state === 'unpaid' && (
        <>
          <div className="result-icon pending">…</div>
          <h1>Payment not completed</h1>
          <p className="result-msg">
            We couldn't confirm your payment. If you were charged, it will reflect
            shortly — you can retry from your cart.
          </p>
          <Link className="checkout-btn" to="/cart">
            Back to cart
          </Link>
        </>
      )}

      {state === 'error' && (
        <>
          <div className="result-icon failed">✕</div>
          <h1>Something went wrong</h1>
          <p className="result-msg">We couldn't verify this payment reference.</p>
          <Link className="checkout-btn" to="/products">
            Back to products
          </Link>
        </>
      )}
    </div>
  )
}
