const ACCESS_KEY = 'vouch_access'
const REFRESH_KEY = 'vouch_refresh'

export function getToken(): string | null {
  return localStorage.getItem(ACCESS_KEY)
}

export function setTokens(access: string, refresh?: string) {
  localStorage.setItem(ACCESS_KEY, access)
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

async function refreshAccessToken(): Promise<string | null> {
  const refresh = localStorage.getItem(REFRESH_KEY)
  if (!refresh) return null
  try {
    const res = await fetch('/api/auth/token/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    })
    if (!res.ok) {
      clearTokens()
      return null
    }
    const data = await res.json()
    setTokens(data.access)
    return data.access as string
  } catch {
    return null
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  }
  if (token) headers.Authorization = `Bearer ${token}`

  let res = await fetch(`/api${path}`, { ...options, headers })

  if (res.status === 401 && token) {
    token = await refreshAccessToken()
    if (token) {
      headers.Authorization = `Bearer ${token}`
      res = await fetch(`/api${path}`, { ...options, headers })
    }
  }

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = JSON.stringify(body.detail ?? body)
    } catch {
      /* keep statusText */
    }
    throw new ApiError(res.status, detail)
  }

  if (res.status === 204) return undefined as T
  return res.json()
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// --- Auth ---
export const authApi = {
  register: (email: string, password: string) =>
    request('/auth/register/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string) =>
    request<{ access: string; refresh: string }>('/auth/token/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  profile: () => request<{ id: number; username: string; email: string }>('/auth/profile/'),
}

// --- Products ---
export interface Product {
  id: number
  name: string
  description: string | null
  price: string
  stock: number
  image: string | null
  is_available: boolean
}

export const productsApi = {
  list: () => request<Product[]>('/products/list-create/'),
  detail: (id: number) => request<Product>(`/products/${id}/`),
}

// --- Cart ---
export interface CartItem {
  id: number
  product_name: string
  price: string
  quantity: number
  sub_total: string
}

export interface Cart {
  id: number
  items: CartItem[]
  user: string
  total: string
}

export const cartApi = {
  get: () => request<Cart>('/cart/'),
  add: (product: number, quantity = 1) =>
    request('/cart/items/', { method: 'POST', body: JSON.stringify({ product, quantity }) }),
  update: (itemId: number, quantity: number) =>
    request(`/cart/item/${itemId}/`, { method: 'PUT', body: JSON.stringify({ quantity }) }),
  remove: (itemId: number) => request(`/cart/item/${itemId}/`, { method: 'DELETE' }),
  clear: () => request('/cart/clear/', { method: 'DELETE' }),
}

// --- Addresses ---
export interface Address {
  id: number
  full_name: string
  phone: string
  address: string
  city: string
  state: string
  country: string
}

export const addressesApi = {
  list: () => request<Address[]>('/addresses/'),
  create: (data: Omit<Address, 'id'>) =>
    request<Address>('/addresses/', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Partial<Address>) =>
    request<Address>(`/addresses/${id}/`, { method: 'PATCH', body: JSON.stringify(data) }),
  remove: (id: number) => request(`/addresses/${id}/`, { method: 'DELETE' }),
}

// --- Orders ---
export interface OrderItem {
  id: number
  product_name: string
  product: number
  price: string
  quantity: number
  sub_total: string
}

export interface Order {
  id: number
  total_amount: string
  status: string
  is_paid: boolean
  created_at: string
  updated_at: string
  items: OrderItem[]
  shipping_address: Address | null
}

export const ordersApi = {
  list: () => request<Order[]>('/orders/'),
  detail: (id: number) => request<Order>(`/orders/${id}/`),
  checkout: (shipping_address_id: number) =>
    request<Order>('/checkout/', { method: 'POST', body: JSON.stringify({ shipping_address_id }) }),
  cancel: (id: number) => request(`/orders/cancel/${id}/`, { method: 'PATCH', body: '{}' }),
}

// --- Payments ---
export const paymentsApi = {
  initiate: (order_id: number) =>
    request<{ order_id: number; reference: string; amount: string; checkout_url: string }>(
      '/payments/initiate/',
      { method: 'POST', body: JSON.stringify({ order_id }) },
    ),
  verify: (reference: string) =>
    request<{ detail: string; payment_status: string; order_status: string }>(
      `/payments/verify/?reference=${encodeURIComponent(reference)}`,
    ),
}
