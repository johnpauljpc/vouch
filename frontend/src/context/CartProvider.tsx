import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { cartApi, type Cart } from '../api'
import { useAuth } from './auth-context'
import { CartContext } from './cart-context'

export function CartProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [stored, setStored] = useState<{ ownerId: number; cart: Cart } | null>(null)

  const userId = user?.id ?? null

  useEffect(() => {
    if (!userId) return
    let cancelled = false
    cartApi
      .get()
      .then((cart) => {
        if (!cancelled) setStored({ ownerId: userId, cart })
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [userId])

  const refresh = useCallback(async () => {
    if (!userId) return
    const cart = await cartApi.get()
    setStored({ ownerId: userId, cart })
  }, [userId])

  const addItem = useCallback(
    async (productId: number, quantity = 1) => {
      await cartApi.add(productId, quantity)
      await refresh()
    },
    [refresh],
  )

  const updateItem = useCallback(
    async (itemId: number, quantity: number) => {
      await cartApi.update(itemId, quantity)
      await refresh()
    },
    [refresh],
  )

  const removeItem = useCallback(
    async (itemId: number) => {
      await cartApi.remove(itemId)
      await refresh()
    },
    [refresh],
  )

  const clear = useCallback(async () => {
    await cartApi.clear()
    await refresh()
  }, [refresh])

  const cart = stored && userId !== null && stored.ownerId === userId ? stored.cart : null
  const itemCount = cart ? cart.items.reduce((n, i) => n + i.quantity, 0) : 0

  return (
    <CartContext.Provider value={{ cart, itemCount, refresh, addItem, updateItem, removeItem, clear }}>
      {children}
    </CartContext.Provider>
  )
}
