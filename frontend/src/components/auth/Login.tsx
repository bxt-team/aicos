import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Divider,
  IconButton,
  InputAdornment,
  useTheme,
  alpha,
  FormControlLabel,
  Checkbox
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Email,
  Lock
} from '@mui/icons-material';
import { useSupabaseAuth } from '../../contexts/SupabaseAuthContext';
import './auth.css';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { signIn } = useSupabaseAuth();
  const navigate = useNavigate();
  const theme = useTheme();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await signIn(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
        position: 'relative',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'radial-gradient(circle at 20% 50%, rgba(255,255,255,0.1) 0%, transparent 50%), radial-gradient(circle at 80% 80%, rgba(255,255,255,0.1) 0%, transparent 50%)',
        }
      }}
    >
      <Container component="main" maxWidth="xs">
        <Paper 
          elevation={24} 
          sx={{ 
            padding: 5,
            borderRadius: 3,
            backdropFilter: 'blur(10px)',
            background: alpha(theme.palette.background.paper, 0.95),
            position: 'relative',
            overflow: 'hidden',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: -2,
              left: -2,
              right: -2,
              bottom: -2,
              background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
              borderRadius: 3,
              opacity: 0.1,
              zIndex: -1
            }
          }}
        >
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Box sx={{ mb: 2 }}>
              <img 
                src="/logo.svg" 
                alt="AICOS Logo" 
                className="auth-logo-image"
                style={{ 
                  width: 80, 
                  height: 80,
                  filter: theme.palette.mode === 'dark' ? 'brightness(1.2)' : 'none'
                }} 
              />
            </Box>
            <Typography 
              component="h1" 
              variant="h4" 
              sx={{ 
                fontWeight: 700,
                fontFamily: 'Inter, sans-serif',
                color: theme.palette.primary.main,
                mb: 1
              }}
            >
              AICOS
            </Typography>
            <Typography 
              variant="body1" 
              color="text.secondary"
              sx={{ fontWeight: 300 }}
            >
              Welcome back! Please login to continue.
            </Typography>
          </Box>
          
          {error && (
            <Alert 
              severity="error" 
              sx={{ 
                mb: 3,
                borderRadius: 2,
                '& .MuiAlert-icon': {
                  fontSize: 20
                }
              }}
            >
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="email"
              label="Email Address"
              name="email"
              autoComplete="email"
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Email sx={{ color: 'action.active', fontSize: 20 }} />
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  '&:hover fieldset': {
                    borderColor: theme.palette.primary.main,
                  },
                },
              }}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Password"
              type={showPassword ? 'text' : 'password'}
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Lock sx={{ color: 'action.active', fontSize: 20 }} />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle password visibility"
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                      size="small"
                    >
                      {showPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{
                mb: 1,
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  '&:hover fieldset': {
                    borderColor: theme.palette.primary.main,
                  },
                },
              }}
            />
            
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    name="rememberMe"
                    color="primary"
                    size="small"
                  />
                }
                label={
                  <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                    Remember me
                  </Typography>
                }
              />
              <Link 
                to="/forgot-password" 
                style={{ 
                  textDecoration: 'none', 
                  color: theme.palette.primary.main,
                  fontSize: '0.875rem',
                  fontWeight: 500
                }}
              >
                Forgot password?
              </Link>
            </Box>
            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              sx={{ 
                mb: 3,
                py: 1.5,
                borderRadius: 2,
                textTransform: 'none',
                fontSize: '1rem',
                fontWeight: 600,
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                boxShadow: `0 4px 20px ${alpha(theme.palette.primary.main, 0.3)}`,
                '&:hover': {
                  boxShadow: `0 6px 30px ${alpha(theme.palette.primary.main, 0.4)}`,
                },
                '&:disabled': {
                  background: theme.palette.action.disabledBackground,
                }
              }}
              disabled={isLoading || !email || !password}
            >
              {isLoading ? (
                <CircularProgress size={24} sx={{ color: 'white' }} />
              ) : (
                'Sign In'
              )}
            </Button>
            
            <Divider sx={{ mb: 3 }}>
              <Typography variant="body2" color="text.secondary" sx={{ px: 2 }}>
                OR
              </Typography>
            </Divider>
            
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Don't have an account?{' '}
                <Link 
                  to="/signup" 
                  style={{ 
                    textDecoration: 'none', 
                    color: theme.palette.primary.main,
                    fontWeight: 600
                  }}
                >
                  Sign up now
                </Link>
              </Typography>
            </Box>
          </Box>
        </Paper>
        
        {/* Footer with copyright and legal links */}
        <Box
          sx={{
            mt: 4,
            textAlign: 'center',
            color: 'white',
            '& a': {
              color: 'white',
              textDecoration: 'none',
              mx: 1.5,
              fontSize: '0.875rem',
              opacity: 0.9,
              '&:hover': {
                opacity: 1,
                textDecoration: 'underline'
              }
            }
          }}
        >
          <Typography variant="body2" sx={{ mb: 1 }}>
            © {new Date().getFullYear()} buildnext GmbH. All rights reserved.
          </Typography>
          <Box>
            <a 
              href="https://buildnext.io/terms" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              Terms and Conditions
            </a>
            <span style={{ opacity: 0.5 }}>•</span>
            <a 
              href="https://buildnext.io/privacy" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              Privacy
            </a>
            <span style={{ opacity: 0.5 }}>•</span>
            <a 
              href="https://buildnext.io/imprint" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              Imprint
            </a>
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default Login;