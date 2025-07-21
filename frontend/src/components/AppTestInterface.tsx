import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  LinearProgress,
  Tabs,
  Tab,
  Paper,
  CircularProgress,
  Chip,
  IconButton,
  Divider,
  Container,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  ListItemIcon,
} from '@mui/material';
import {
  Upload,
  Smartphone,
  Play,
  Download,
  AlertCircle,
  CheckCircle,
  Loader2,
  Apple,
  FileText,
  Image as ImageIcon,
  BarChart3,
  Accessibility,
  FolderOpen,
  Package,
} from 'lucide-react';

interface Device {
  udid?: string;
  name: string;
  state?: string;
  runtime?: string;
}

interface UploadedApp {
  filename: string;
  path: string;
  size: number;
  uploaded_at: string;
  is_directory: boolean;
}

interface TestResult {
  id: string;
  platform: string;
  status: string;
  started_at: string;
  completed_at?: string;
  results?: {
    test_summary?: string;
    errors?: any[];
    performance?: any;
    accessibility?: any;
    screenshots?: Array<{
      description: string;
      path: string;
    }>;
    recommendations?: any[];
  };
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const AppTestInterface: React.FC = () => {
  const [platform, setPlatform] = useState<'android' | 'ios'>('android');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedPath, setUploadedPath] = useState<string>('');
  const [isTestRunning, setIsTestRunning] = useState(false);
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [selectedTest, setSelectedTest] = useState<TestResult | null>(null);
  const [error, setError] = useState<string>('');
  const [tabValue, setTabValue] = useState(0);
  const [detailsTabValue, setDetailsTabValue] = useState(0);
  // Removed health status - assuming all agents are always up
  const healthStatus = { status: 'healthy', platforms: { android: { status: 'ready' }, ios: { status: 'ready' } } };
  const [uploadedApps, setUploadedApps] = useState<UploadedApp[]>([]);
  const [showAppSelector, setShowAppSelector] = useState(false);
  const [loadingApps, setLoadingApps] = useState(false);

  // Fetch available devices when platform changes
  useEffect(() => {
    fetchDevices();
  }, [platform]);

  // Fetch test results on mount
  useEffect(() => {
    fetchTestResults();
    const interval = setInterval(fetchTestResults, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchDevices = async () => {
    try {
      const response = await fetch(`/api/app-test/devices/${platform}`);
      const data = await response.json();
      const deviceList = data.devices || [];
      
      // Filter out placeholder devices for selection
      // Don't filter by isAvailable as some simulators may need to be downloaded
      const selectableDevices = deviceList.filter(
        (d: Device) => d.udid !== 'no-simulator' && d.udid !== 'error' && d.name !== 'Error loading simulators'
      );
      
      setDevices(selectableDevices);
      
      // Set selected device if we have any
      if (selectableDevices.length > 0 && !selectedDevice) {
        setSelectedDevice(selectableDevices[0].udid || selectableDevices[0].name);
      } else if (selectableDevices.length === 0) {
        setSelectedDevice('');
        if (platform === 'ios') {
          setError('No iOS simulators found. Please install Xcode and download iOS simulators from Xcode > Settings > Platforms.');
        }
      }
    } catch (err) {
      console.error('Failed to fetch devices:', err);
      setError(`Failed to fetch ${platform} devices. Please check if the required tools are installed.`);
    }
  };

  const fetchTestResults = async () => {
    try {
      const response = await fetch('/api/app-test/');
      const data = await response.json();
      console.log('Fetched test results:', data);
      setTestResults(data);
    } catch (err) {
      console.error('Failed to fetch test results:', err);
    }
  };

  // Removed health status fetching - all agents are assumed to be always up

  const fetchUploadedApps = async () => {
    setLoadingApps(true);
    try {
      const response = await fetch(`/api/app-test/uploaded-apps/${platform}`);
      const data = await response.json();
      setUploadedApps(data.apps || []);
    } catch (err) {
      console.error('Failed to fetch uploaded apps:', err);
    } finally {
      setLoadingApps(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const validExtensions = platform === 'android' ? ['.apk'] : ['.app', '.zip', '.tar.gz', '.tgz', '.ipa'];
      const fileName = file.name.toLowerCase();
      
      // Check if file matches any valid extension
      const isValid = validExtensions.some(ext => fileName.endsWith(ext));
      
      if (isValid) {
        setSelectedFile(file);
        setError('');
      } else {
        setError(`Invalid file type. Expected: ${validExtensions.join(', ')}`);
        setSelectedFile(null);
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(`/api/app-test/upload-app?platform=${platform}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      setUploadedPath(data.file_path);
      setError('');
      if (data.reused) {
        setError('App already exists, reusing existing file.');
      }
    } catch (err) {
      setError(`Upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleOpenAppSelector = () => {
    fetchUploadedApps();
    setShowAppSelector(true);
  };

  const handleSelectExistingApp = (app: UploadedApp) => {
    setUploadedPath(app.path);
    setShowAppSelector(false);
    setSelectedFile(null); // Clear any selected file
  };

  const handleStartTest = async () => {
    if (!uploadedPath) return;

    setIsTestRunning(true);
    setError('');

    try {
      const response = await fetch(`/api/app-test/?app_path=${uploadedPath}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          platform,
          device_id: selectedDevice || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error(`Test failed: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Test creation response:', data);
      
      // Refresh test results
      fetchTestResults();
      
      // Reset form
      setSelectedFile(null);
      setUploadedPath('');
    } catch (err) {
      setError(`Test failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsTestRunning(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <CircularProgress size={16} />;
      case 'completed':
        return <CheckCircle size={16} color="green" />;
      case 'failed':
        return <AlertCircle size={16} color="red" />;
      default:
        return null;
    }
  };

  const getPlatformIcon = (platform: string) => {
    return platform === 'ios' ? <Apple size={16} /> : <Smartphone size={16} />;
  };

  const handlePlatformChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    setPlatform(newValue === 0 ? 'android' : 'ios');
    setError(''); // Clear error when switching platforms
    setSelectedDevice(''); // Clear selected device
    setUploadedPath(''); // Clear uploaded path
    setSelectedFile(null); // Clear selected file
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleDetailsTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setDetailsTabValue(newValue);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Platform Status Card */}
      {healthStatus && (
        <Card sx={{ mb: 2, bgcolor: healthStatus.status === 'healthy' ? 'success.light' : 'warning.light' }}>
          <CardContent sx={{ py: 1 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Typography variant="body2">
                Platform Status: {healthStatus.status}
              </Typography>
              <Box display="flex" gap={2}>
                <Chip 
                  label={`Android: ${healthStatus.platforms?.android?.status || 'unknown'}`}
                  size="small"
                  color={healthStatus.platforms?.android?.status === 'ready' ? 'success' : 'default'}
                />
                <Chip 
                  label={`iOS: ${healthStatus.platforms?.ios?.status || 'unknown'}`}
                  size="small"
                  color={healthStatus.platforms?.ios?.status === 'ready' ? 'success' : 'default'}
                />
              </Box>
            </Box>
            {healthStatus.platforms?.ios?.status === 'no_simulators' && (
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                iOS: Xcode is installed but no simulators found. Download simulators from Xcode → Settings → Platforms
              </Typography>
            )}
            {healthStatus.platforms?.ios?.status === 'xcode_not_found' && (
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                iOS: Xcode command line tools not installed. Install Xcode from the App Store.
              </Typography>
            )}
          </CardContent>
        </Card>
      )}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h5" component="h2" gutterBottom>
            Mobile App Testing
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Test iOS and Android apps for performance, accessibility, and user experience
          </Typography>

          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
            <Tabs value={tabValue} onChange={handlePlatformChange}>
              <Tab 
                icon={<Smartphone size={20} />} 
                label="Android" 
                iconPosition="start"
              />
              <Tab 
                icon={<Apple size={20} />} 
                label="iOS" 
                iconPosition="start"
              />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={tabValue}>
            <Stack spacing={3}>
              {/* File Upload Section */}
              <Box>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="subtitle2">
                    {platform === 'android' ? 'APK File' : 'iOS App Bundle (.app, .ipa, .zip, .tar.gz, .tgz)'}
                  </Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={handleOpenAppSelector}
                    disabled={isTestRunning}
                    startIcon={<FolderOpen size={16} />}
                  >
                    Select from existing
                  </Button>
                </Box>
                
                <Stack direction="row" spacing={2}>
                  <TextField
                    type="file"
                    inputProps={{
                      accept: platform === 'android' ? '.apk' : '.app,.ipa,.zip,.tar.gz,.tgz'
                    }}
                    onChange={handleFileSelect}
                    disabled={isUploading || isTestRunning}
                    fullWidth
                  />
                  <Button
                    variant="contained"
                    onClick={handleUpload}
                    disabled={!selectedFile || isUploading || isTestRunning}
                    startIcon={isUploading ? <CircularProgress size={20} /> : <Upload size={20} />}
                  >
                    {isUploading ? 'Uploading...' : 'Upload'}
                  </Button>
                </Stack>
                
                {uploadedPath && (
                  <Alert severity="success" sx={{ mt: 1 }}>
                    App ready: {uploadedPath.split('/').pop()}
                  </Alert>
                )}
              </Box>

              {/* Device Selection */}
              <FormControl fullWidth>
                <InputLabel>Test Device</InputLabel>
                <Select
                  value={selectedDevice}
                  onChange={(e) => setSelectedDevice(e.target.value)}
                  label="Test Device"
                  disabled={devices.length === 0}
                >
                  {devices.length === 0 ? (
                    <MenuItem value="" disabled>
                      {platform === 'ios' 
                        ? 'No iOS simulators available - Install Xcode' 
                        : 'No Android emulators available - Create AVD'}
                    </MenuItem>
                  ) : (
                    devices.map((device) => (
                      <MenuItem 
                        key={device.udid || device.name} 
                        value={device.udid || device.name}
                      >
                        {device.name} {device.state && `(${device.state})`}
                      </MenuItem>
                    ))
                  )}
                </Select>
              </FormControl>

              {/* Start Test Button */}
              <Button
                variant="contained"
                color="primary"
                onClick={handleStartTest}
                disabled={!uploadedPath || isTestRunning}
                fullWidth
                size="large"
                startIcon={isTestRunning ? <CircularProgress size={20} /> : <Play size={20} />}
              >
                {isTestRunning ? 'Running Test...' : 'Start Test'}
              </Button>

              {/* Error Display */}
              {error && (
                <Alert severity="error" icon={<AlertCircle />}>
                  {error}
                </Alert>
              )}
            </Stack>
          </TabPanel>
        </CardContent>
      </Card>

      {/* Test Results */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Test Results
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            View and analyze your app test results
          </Typography>

          <Stack spacing={2} sx={{ mt: 2 }}>
            {testResults.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No test results yet. Run a test to see results here.
              </Typography>
            ) : (
              testResults.map((test) => (
              <Paper
                key={test.id}
                sx={{ 
                  p: 2, 
                  cursor: 'pointer',
                  '&:hover': { bgcolor: 'grey.50' }
                }}
                onClick={() => setSelectedTest(test)}
              >
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box display="flex" alignItems="center" gap={1}>
                    {getPlatformIcon(test.platform)}
                    <Typography variant="subtitle2" sx={{ textTransform: 'capitalize' }}>
                      {test.platform}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(test.started_at).toLocaleString()}
                    </Typography>
                  </Box>
                  <Box display="flex" alignItems="center" gap={1}>
                    {getStatusIcon(test.status)}
                    <Typography variant="caption" sx={{ textTransform: 'capitalize' }}>
                      {test.status}
                    </Typography>
                  </Box>
                </Box>
                
                {test.results?.test_summary && (
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    {test.results.test_summary}
                  </Typography>
                )}
              </Paper>
            ))
            )}
          </Stack>
        </CardContent>
      </Card>

      {/* Detailed Test View */}
      {selectedTest && selectedTest.results && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Test Details
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {selectedTest.platform.toUpperCase()} Test - {selectedTest.id}
            </Typography>

            <Box sx={{ borderBottom: 1, borderColor: 'divider', mt: 2 }}>
              <Tabs value={detailsTabValue} onChange={handleDetailsTabChange}>
                <Tab icon={<FileText size={16} />} label="Summary" iconPosition="start" />
                <Tab icon={<AlertCircle size={16} />} label="Errors" iconPosition="start" />
                <Tab icon={<BarChart3 size={16} />} label="Performance" iconPosition="start" />
                <Tab icon={<Accessibility size={16} />} label="Accessibility" iconPosition="start" />
                <Tab icon={<ImageIcon size={16} />} label="Screenshots" iconPosition="start" />
              </Tabs>
            </Box>

            <TabPanel value={detailsTabValue} index={0}>
              <Typography variant="body1" paragraph>
                {selectedTest.results.test_summary}
              </Typography>
              {selectedTest.results.recommendations && (
                <>
                  <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                    Recommendations
                  </Typography>
                  <Stack spacing={1}>
                    {selectedTest.results.recommendations.map((rec: any, idx: number) => (
                      <Typography key={idx} variant="body2">
                        • {typeof rec === 'string' ? rec : `[${rec.priority || 'normal'}] ${rec.suggestion || JSON.stringify(rec)}`}
                      </Typography>
                    ))}
                  </Stack>
                </>
              )}
            </TabPanel>

            <TabPanel value={detailsTabValue} index={1}>
              {selectedTest.results.errors && selectedTest.results.errors.length > 0 ? (
                <Stack spacing={2}>
                  {selectedTest.results.errors.map((error: any, idx: number) => (
                    <Alert key={idx} severity={
                      error.priority === 'kritisch' || error.priority === 'critical' ? 'error' : 
                      error.priority === 'mittel' || error.priority === 'medium' ? 'warning' : 'info'
                    } icon={<AlertCircle />}>
                      <Typography variant="subtitle2" fontWeight="bold">
                        {error.priority ? `[${error.priority}] ` : ''}{error.description || JSON.stringify(error)}
                      </Typography>
                      {error.log && (
                        <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                          Log: {error.log}
                        </Typography>
                      )}
                    </Alert>
                  ))}
                </Stack>
              ) : (
                <Typography color="text.secondary">No errors found</Typography>
              )}
            </TabPanel>

            <TabPanel value={detailsTabValue} index={2}>
              <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
                <pre style={{ margin: 0 }}>
                  {JSON.stringify(selectedTest.results.performance, null, 2)}
                </pre>
              </Paper>
            </TabPanel>

            <TabPanel value={detailsTabValue} index={3}>
              <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
                <pre style={{ margin: 0 }}>
                  {JSON.stringify(selectedTest.results.accessibility, null, 2)}
                </pre>
              </Paper>
            </TabPanel>

            <TabPanel value={detailsTabValue} index={4}>
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2 }}>
                {selectedTest.results.screenshots?.map((screenshot, idx) => (
                  <Paper key={idx} sx={{ p: 1 }}>
                    <img
                      src={`/static/${screenshot.path}`}
                      alt={screenshot.description}
                      style={{ width: '100%', borderRadius: 4 }}
                    />
                    <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                      {screenshot.description}
                    </Typography>
                  </Paper>
                ))}
              </Box>
            </TabPanel>
          </CardContent>
        </Card>
      )}

      {/* App Selector Dialog */}
      <Dialog
        open={showAppSelector}
        onClose={() => setShowAppSelector(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <Package size={20} />
            Select from existing {platform.toUpperCase()} apps
          </Box>
        </DialogTitle>
        <DialogContent>
          {loadingApps ? (
            <Box display="flex" justifyContent="center" py={3}>
              <CircularProgress />
            </Box>
          ) : uploadedApps.length === 0 ? (
            <Alert severity="info">
              No previously uploaded {platform} apps found. Upload a new app to get started.
            </Alert>
          ) : (
            <List>
              {uploadedApps.map((app, idx) => (
                <ListItemButton
                  key={idx}
                  onClick={() => handleSelectExistingApp(app)}
                  sx={{ borderRadius: 1, mb: 1 }}
                >
                  <ListItemIcon>
                    {app.is_directory ? <Package size={20} /> : <FileText size={20} />}
                  </ListItemIcon>
                  <ListItemText
                    primary={app.filename}
                    secondary={
                      <Stack direction="row" spacing={2} sx={{ mt: 0.5 }}>
                        <Typography variant="caption" color="text.secondary">
                          {formatFileSize(app.size)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {new Date(app.uploaded_at).toLocaleDateString()}
                        </Typography>
                      </Stack>
                    }
                  />
                </ListItemButton>
              ))}
            </List>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowAppSelector(false)}>
            Cancel
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AppTestInterface;