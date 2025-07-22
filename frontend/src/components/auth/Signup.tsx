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
  Stepper,
  Step,
  StepLabel
} from '@mui/material';
import { useAuth } from '../../contexts/AuthContext';

const steps = ['Persönliche Daten', 'Organisation'];

const Signup: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [organizationName, setOrganizationName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { signup } = useAuth();
  const navigate = useNavigate();

  const handleNext = () => {
    if (activeStep === 0) {
      // Validate step 1
      if (!email || !password || !name) {
        setError('Bitte füllen Sie alle Felder aus');
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwörter stimmen nicht überein');
        return;
      }
      if (password.length < 8) {
        setError('Passwort muss mindestens 8 Zeichen lang sein');
        return;
      }
    }
    setError('');
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!organizationName) {
      setError('Bitte geben Sie einen Organisationsnamen ein');
      return;
    }

    setError('');
    setIsLoading(true);

    try {
      await signup(email, password, name, organizationName);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Registrierung fehlgeschlagen. Bitte versuchen Sie es erneut.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <>
            <TextField
              margin="normal"
              required
              fullWidth
              id="name"
              label="Vollständiger Name"
              name="name"
              autoComplete="name"
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isLoading}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              id="email"
              label="E-Mail Adresse"
              name="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Passwort"
              type="password"
              id="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              helperText="Mindestens 8 Zeichen"
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="confirmPassword"
              label="Passwort bestätigen"
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={isLoading}
            />
            <Button
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              onClick={handleNext}
              disabled={isLoading}
            >
              Weiter
            </Button>
          </>
        );
      case 1:
        return (
          <Box component="form" onSubmit={handleSubmit}>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              Erstellen Sie Ihre Organisation. Sie können später weitere Teammitglieder einladen.
            </Typography>
            <TextField
              margin="normal"
              required
              fullWidth
              id="organizationName"
              label="Organisationsname"
              name="organizationName"
              autoFocus
              value={organizationName}
              onChange={(e) => setOrganizationName(e.target.value)}
              disabled={isLoading}
              helperText="Z.B. Ihr Firmenname oder Projektname"
            />
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
              <Button
                onClick={handleBack}
                disabled={isLoading}
              >
                Zurück
              </Button>
              <Button
                type="submit"
                variant="contained"
                disabled={isLoading || !organizationName}
              >
                {isLoading ? <CircularProgress size={24} /> : 'Konto erstellen'}
              </Button>
            </Box>
          </Box>
        );
      default:
        return null;
    }
  };

  return (
    <Container component="main" maxWidth="sm">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper elevation={3} sx={{ padding: 4, width: '100%' }}>
          <Typography component="h1" variant="h4" align="center" gutterBottom>
            AI Company
          </Typography>
          <Typography component="h2" variant="h6" align="center" color="text.secondary" gutterBottom>
            Konto erstellen
          </Typography>
          
          <Stepper activeStep={activeStep} sx={{ mt: 3, mb: 3 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {error && (
            <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
              {error}
            </Alert>
          )}

          {renderStepContent()}
          
          <Divider sx={{ my: 2 }}>oder</Divider>
          
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="body2">
              Bereits registriert?{' '}
              <Link to="/login" style={{ textDecoration: 'none', color: '#1976d2' }}>
                Jetzt anmelden
              </Link>
            </Typography>
          </Box>
        </Paper>
        
        {/* Footer with copyright and legal links */}
        <Box
          sx={{
            mt: 4,
            textAlign: 'center',
            pb: 3,
            '& a': {
              color: 'text.secondary',
              textDecoration: 'none',
              mx: 1.5,
              fontSize: '0.875rem',
              '&:hover': {
                color: 'primary.main',
                textDecoration: 'underline'
              }
            }
          }}
        >
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
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
            <span style={{ color: 'text.disabled' }}>•</span>
            <a 
              href="https://buildnext.io/privacy" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              Privacy
            </a>
            <span style={{ color: 'text.disabled' }}>•</span>
            <a 
              href="https://buildnext.io/imprint" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              Imprint
            </a>
          </Box>
        </Box>
      </Box>
    </Container>
  );
};

export default Signup;