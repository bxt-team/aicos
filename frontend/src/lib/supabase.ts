import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || ''
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY || ''

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true, // Keep auto refresh enabled
    persistSession: true,
    detectSessionInUrl: true,
    flowType: 'implicit', // Changed to implicit for magic links
    storage: typeof window !== 'undefined' ? window.localStorage : undefined,
    storageKey: 'supabase.auth.token',
    debug: process.env.NODE_ENV === 'development',
  },
  global: {
    headers: {
      'X-Client-Info': 'supabase-js/2.0.0',
    },
  },
})

// Override the visibility change behavior after client creation
if (typeof window !== 'undefined') {
  // Access the internal auth client
  const authClient = (supabase as any).auth;
  
  if (authClient && authClient._visibilityChangedCallback) {
    // Remove the default visibility change callback
    authClient._visibilityChangedCallback = null;
  }
  
  // Override the _onVisibilityChanged method to do nothing
  if (authClient && authClient._onVisibilityChanged) {
    authClient._onVisibilityChanged = (callback: any) => {
      // Do nothing - this prevents visibility change detection
      return () => {};
    };
  }
  
  // Also try to remove any existing visibility change listeners
  const noop = () => {};
  document.removeEventListener('visibilitychange', noop);
  
  // Set up our own refresh interval that doesn't depend on visibility
  let refreshInterval: NodeJS.Timer | null = null;
  
  const setupRefreshInterval = () => {
    // Clear any existing interval
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
    
    // Refresh token every 50 minutes (tokens typically expire after 60 minutes)
    refreshInterval = setInterval(async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (session) {
          await supabase.auth.refreshSession();
        }
      } catch (error) {
        console.error('Failed to refresh session:', error);
      }
    }, 50 * 60 * 1000); // 50 minutes
  };
  
  // Set up the refresh interval
  setupRefreshInterval();
  
  // Clean up on page unload
  window.addEventListener('beforeunload', () => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });
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