import { BrowserRouter, Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { useAuth } from './context/auth-context'
import { AuthProvider } from './context/AuthProvider'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Register from './pages/Register'
import Products from './pages/Products'
import './App.css'

function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <header className="header">
      <span className="brand">Vouch</span>
      <nav className="header-nav">
        {user ? (
          <>
            <span className="user-email">{user.email}</span>
            <button
              className="btn-link"
              onClick={() => {
                logout()
                navigate('/login')
              }}
            >
              Sign out
            </button>
          </>
        ) : (
          <>
            <a href="/login">Sign in</a>
            <a href="/register">Register</a>
          </>
        )}
      </nav>
    </header>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Header />
        <main className="main">
          <Routes>
            <Route path="/" element={<Navigate to="/products" replace />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/products"
              element={
                <ProtectedRoute>
                  <Products />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/products" replace />} />
          </Routes>
        </main>
      </AuthProvider>
    </BrowserRouter>
  )
}
