import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  IconButton,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Paper,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import {
  Edit as EditIcon,
  Save as SaveIcon,
  AutoAwesome as AIIcon,
  CheckCircle as CheckIcon,
  TrendingUp as MetricIcon,
  FlagOutlined as GoalIcon,
  Lightbulb as ValueIcon
} from '@mui/icons-material';
import { organizationManagementService, OrganizationGoalResponse } from '../../services/organizationManagementService';

interface OrganizationDetailsProps {
  organization: any;
  orgDetails: any;
  setOrgDetails: (details: any) => void;
  isEditingDetails: boolean;
  setIsEditingDetails: (editing: boolean) => void;
  handleSaveDetails: () => Promise<void>;
  loading: boolean;
  orgLoading: boolean;
}

const OrganizationDetails: React.FC<OrganizationDetailsProps> = ({
  organization,
  orgDetails,
  setOrgDetails,
  isEditingDetails,
  setIsEditingDetails,
  handleSaveDetails,
  loading,
  orgLoading
}) => {
  const [aiDialogOpen, setAiDialogOpen] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [aiResult, setAiResult] = useState<OrganizationGoalResponse | null>(null);
  const [userFeedback, setUserFeedback] = useState('');
  const [previousResult, setPreviousResult] = useState<string | null>(null);
  if (loading || orgLoading) {
    return <CircularProgress />;
  }

  if (!orgDetails) {
    return null;
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">Organization Details</Typography>
        {!isEditingDetails ? (
          <IconButton onClick={() => setIsEditingDetails(true)}>
            <EditIcon />
          </IconButton>
        ) : (
          <Button
            startIcon={<SaveIcon />}
            variant="contained"
            onClick={handleSaveDetails}
            disabled={loading}
          >
            Save
          </Button>
        )}
      </Box>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        <Box sx={{ flex: '1 1 100%' }}>
          <TextField
            fullWidth
            label="Organization ID"
            value={organization.id}
            disabled
            InputProps={{
              readOnly: true,
              sx: { fontFamily: 'monospace' }
            }}
            helperText="This is your organization's unique identifier"
          />
        </Box>
        <Box sx={{ flex: '1 1 100%', '@media (min-width: 900px)': { flex: '1 1 45%' } }}>
          <TextField
            fullWidth
            label="Name"
            value={orgDetails.name || ''}
            onChange={(e) => setOrgDetails({ ...orgDetails, name: e.target.value })}
            disabled={!isEditingDetails}
          />
        </Box>
        <Box sx={{ flex: '1 1 100%', '@media (min-width: 900px)': { flex: '1 1 45%' } }}>
          <TextField
            fullWidth
            label="Website"
            value={orgDetails.website || ''}
            onChange={(e) => setOrgDetails({ ...orgDetails, website: e.target.value })}
            disabled={!isEditingDetails}
          />
        </Box>
        <Box sx={{ flex: '1 1 100%', position: 'relative' }}>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Goals & Description"
            value={orgDetails.description || ''}
            onChange={(e) => setOrgDetails({ ...orgDetails, description: e.target.value })}
            disabled={!isEditingDetails}
          />
          {isEditingDetails && (
            <Button
              startIcon={<AIIcon />}
              variant="outlined"
              size="small"
              onClick={() => setAiDialogOpen(true)}
              sx={{ position: 'absolute', right: 8, top: 8 }}
            >
              Improve with AI
            </Button>
          )}
        </Box>
        <Box sx={{ flex: '1 1 100%', '@media (min-width: 900px)': { flex: '1 1 45%' } }}>
          <TextField
            fullWidth
            label="Abonnement"
            value={orgDetails.subscription_tier || 'free'}
            disabled
          />
        </Box>
        <Box sx={{ flex: '1 1 100%', '@media (min-width: 900px)': { flex: '1 1 45%' } }}>
          <TextField
            fullWidth
            label="Erstellt am"
            value={new Date(orgDetails.created_at).toLocaleDateString('de-DE')}
            disabled
          />
        </Box>
      </Box>

      {/* AI Enhancement Dialog */}
      <Dialog 
        open={aiDialogOpen} 
        onClose={() => setAiDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <AIIcon color="primary" />
            <Typography variant="h6">AI-Powered Goal Enhancement</Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          {aiError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {aiError}
            </Alert>
          )}
          
          {!aiResult ? (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Our AI will analyze your organization description and create comprehensive goals, 
                success metrics, and a clear value proposition.
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Current Description"
                value={orgDetails.description || ''}
                disabled
                sx={{ mb: 2 }}
              />
              {previousResult && (
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  label="Feedback for AI (optional)"
                  placeholder="Tell the AI how to improve the previous result..."
                  value={userFeedback}
                  onChange={(e) => setUserFeedback(e.target.value)}
                />
              )}
            </Box>
          ) : (
            <Box>
              <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  Enhanced Description
                </Typography>
                <Typography variant="body2">
                  {aiResult.improved_description}
                </Typography>
              </Paper>

              <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <ValueIcon color="primary" />
                  <Typography variant="subtitle1" fontWeight="bold">
                    Organization Purpose
                  </Typography>
                </Box>
                <Typography variant="body2">
                  {aiResult.organization_purpose}
                </Typography>
              </Paper>

              <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <GoalIcon color="primary" />
                  <Typography variant="subtitle1" fontWeight="bold">
                    Primary Goals
                  </Typography>
                </Box>
                <List dense>
                  {aiResult.primary_goals.map((goal, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <CheckIcon color="success" fontSize="small" />
                      </ListItemIcon>
                      <ListItemText primary={goal} />
                    </ListItem>
                  ))}
                </List>
              </Paper>

              <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <MetricIcon color="primary" />
                  <Typography variant="subtitle1" fontWeight="bold">
                    Success Metrics
                  </Typography>
                </Box>
                <Box display="flex" flexWrap="wrap" gap={1}>
                  {aiResult.success_metrics.map((metric, index) => (
                    <Chip key={index} label={metric} size="small" />
                  ))}
                </Box>
              </Paper>

              <Paper elevation={2} sx={{ p: 2 }}>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  Value Proposition
                </Typography>
                <Typography variant="body2">
                  {aiResult.value_proposition}
                </Typography>
              </Paper>

              <Divider sx={{ my: 2 }} />
              
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Feedback for refinement (optional)"
                placeholder="What would you like to adjust?"
                value={userFeedback}
                onChange={(e) => setUserFeedback(e.target.value)}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setAiDialogOpen(false);
            setAiResult(null);
            setUserFeedback('');
            setPreviousResult(null);
            setAiError(null);
          }}>
            Cancel
          </Button>
          {!aiResult ? (
            <Button 
              onClick={async () => {
                setAiLoading(true);
                setAiError(null);
                try {
                  const result = await organizationManagementService.improveOrganizationGoals({
                    description: orgDetails.description || '',
                    user_feedback: userFeedback || undefined,
                    previous_result: previousResult || undefined
                  });
                  setAiResult(result);
                } catch (error: any) {
                  setAiError(error.response?.data?.detail || 'Failed to generate goals');
                } finally {
                  setAiLoading(false);
                }
              }}
              variant="contained"
              disabled={aiLoading || !orgDetails.description}
              startIcon={aiLoading ? <CircularProgress size={20} /> : <AIIcon />}
            >
              {aiLoading ? 'Generating...' : 'Generate Goals'}
            </Button>
          ) : (
            <>
              <Button
                onClick={async () => {
                  setPreviousResult(JSON.stringify(aiResult));
                  setAiResult(null);
                }}
                disabled={aiLoading}
              >
                Refine
              </Button>
              <Button
                onClick={() => {
                  // Apply the AI result to the organization details
                  setOrgDetails({
                    ...orgDetails,
                    description: `${aiResult.improved_description}\n\nPurpose: ${aiResult.organization_purpose}\n\nGoals:\n${aiResult.primary_goals.join('\n')}\n\nValue Proposition: ${aiResult.value_proposition}`
                  });
                  setAiDialogOpen(false);
                  setAiResult(null);
                  setUserFeedback('');
                  setPreviousResult(null);
                }}
                variant="contained"
                color="primary"
              >
                Apply Changes
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default OrganizationDetails;