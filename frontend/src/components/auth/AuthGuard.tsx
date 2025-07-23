import React, { useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { CircularProgress, Box } from '@mui/material'
import { useSupabaseAuth } from '../../contexts/SupabaseAuthContext'

interface AuthGuardProps {
  children: React.ReactNode
  requireMFA?: boolean
}

export const AuthGuard: React.FC<AuthGuardProps> = ({ children, requireMFA = false }) => {
  const location = useLocation()
  const { user, session, loading, getAAL } = useSupabaseAuth()
  const [checkingMFA, setCheckingMFA] = useState(false)
  const [needsMFA, setNeedsMFA] = useState(false)

  useEffect(() => {
    if (!loading && user && requireMFA) {
      checkMFAStatus()
    }
  }, [user, loading, requireMFA])

  const checkMFAStatus = async () => {
    setCheckingMFA(true)
    try {
      const { currentLevel, nextLevel } = await getAAL()
      if (nextLevel === 'aal2' && currentLevel !== 'aal2') {
        setNeedsMFA(true)
      }
    } catch (err) {
      console.error('Error checking MFA status:', err)
    } finally {
      setCheckingMFA(false)
    }
  }

  if (loading || checkingMFA) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
        }}
      >
        <CircularProgress />
      </Box>
    )
  }

  if (!user || !session) {
    // Redirect to login page but save the attempted location
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (requireMFA && needsMFA) {
    // User needs to complete MFA challenge
    return <Navigate to="/mfa-challenge" replace />
  }

  return <>{children}</>
}

export const withAuth = <P extends object>(
  Component: React.ComponentType<P>,
  requireMFA = false
) => {
  return (props: P) => (
    <AuthGuard requireMFA={requireMFA}>
      <Component {...props} />
    </AuthGuard>
  )
}