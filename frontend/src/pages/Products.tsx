import { useAuth } from '../context/auth-context'

export default function Products() {
  const { user } = useAuth()
  return (
    <div className="page">
      <h1>Products</h1>
      <p>Product listing coming next — signed in as {user?.email}</p>
    </div>
  )
}
