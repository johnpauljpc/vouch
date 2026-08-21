import { useState } from 'react'
import type { Product } from '../api'
import { formatNaira } from '../lib/format'
import { useCart } from '../context/cart-context'

type AddState = 'idle' | 'adding' | 'added' | 'error'

export default function ProductCard({ product }: { product: Product }) {
  const [state, setState] = useState<AddState>('idle')
  const { addItem } = useCart()
  const soldOut = product.stock <= 0

  const addToCart = async () => {
    setState('adding')
    try {
      await addItem(product.id, 1)
      setState('added')
    } catch {
      setState('error')
    } finally {
      setTimeout(() => setState('idle'), 1800)
    }
  }

  return (
    <article className="product-card">
      <div className="product-image">
        {product.image ? (
          <img src={product.image} alt={product.name} loading="lazy" />
        ) : (
          <div className="product-placeholder" aria-hidden="true">
            {product.name.charAt(0).toUpperCase()}
          </div>
        )}
      </div>
      <div className="product-body">
        <h3>{product.name}</h3>
        {product.description && <p className="product-desc">{product.description}</p>}
        <div className="product-meta">
          <span className="product-price">{formatNaira(product.price)}</span>
          <span
            className={`stock-badge${soldOut ? ' out' : product.stock <= 5 ? ' low' : ''}`}
          >
            {soldOut
              ? 'Out of stock'
              : product.stock <= 5
                ? `Only ${product.stock} left`
                : 'In stock'}
          </span>
        </div>
        <button
          className="add-btn"
          onClick={addToCart}
          disabled={soldOut || state === 'adding'}
        >
          {soldOut
            ? 'Sold out'
            : state === 'adding'
              ? 'Adding…'
              : state === 'added'
                ? 'Added ✓'
                : state === 'error'
                  ? 'Failed — retry'
                  : 'Add to cart'}
        </button>
      </div>
    </article>
  )
}
