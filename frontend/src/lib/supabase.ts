import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || ''
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY || ''

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
    flowType: 'implicit', // Changed to implicit for magic links
    storage: typeof window !== 'undefined' ? window.localStorage : undefined,
    storageKey: 'supabase.auth.token',
    debug: process.env.NODE_ENV === 'development',
  },
})

// Disable Supabase's visibility change listener after client creation
if (typeof window !== 'undefined' && (supabase as any).auth) {
  const auth = (supabase as any).auth;
  
  // Override the startAutoRefresh method to prevent visibility change detection
  if (auth.startAutoRefresh) {
    const originalStartAutoRefresh = auth.startAutoRefresh.bind(auth);
    auth.startAutoRefresh = function() {
      // Call original without setting up visibility change listener
      const result = originalStartAutoRefresh.apply(this, arguments);
      
      // Remove visibility change listener if it exists
      if (typeof document !== 'undefined') {
        const visibilityHandler = () => {};
        document.removeEventListener('visibilitychange', visibilityHandler);
      }
      
      return result;
    };
  }
}

// Helper to get session
export const getSession = async () => {
  const { data: { session }, error } = await supabase.auth.getSession()
  if (error) throw error
  return session
}

// Helper to get user
export const getUser = async () => {
  const { data: { user }, error } = await supabase.auth.getUser()
  if (error) throw error
  return user
}