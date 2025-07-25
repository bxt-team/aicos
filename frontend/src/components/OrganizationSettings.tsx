import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Tabs,
  Tab,
  Box,
  Alert
} from '@mui/material';
import { useOrganization } from '../contexts/OrganizationContext';
import { apiService } from '../services/api';
import { useNavigate } from 'react-router-dom';
import {
  OrganizationDetails,
  OrganizationMembers,
  OrganizationUsage,
  OrganizationDangerZone,
  InviteMemberDialog,
  DeleteOrganizationDialog
} from './organization';

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
      id={`org-tabpanel-${index}`}
      aria-labelledby={`org-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const OrganizationSettings: React.FC = () => {
  const navigate = useNavigate();
  const {
    currentOrganization,
    members,
    loading: orgLoading,
    updateOrganization,
    loadMembers,
    inviteMember,
    removeMember,
    updateMemberRole,
    deleteOrganization
  } = useOrganization();
  
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Store previous tab value to prevent unnecessary reloads
  const previousTabRef = React.useRef(tabValue);
  
  // Organization details
  const [orgDetails, setOrgDetails] = useState<any>(null);
  const [isEditingDetails, setIsEditingDetails] = useState(false);
  
  // Invite dialog
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  
  // Delete organization dialog
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  
  // Usage stats
  const [usage, setUsage] = useState<any>(null);

  useEffect(() => {
    if (currentOrganization && tabValue !== previousTabRef.current) {
      console.log('[OrganizationSettings] Tab changed from', previousTabRef.current, 'to', tabValue);
      previousTabRef.current = tabValue;
      loadOrganizationData();
    }
  }, [currentOrganization, tabValue]);

  useEffect(() => {
    // Initialize org details when currentOrganization changes
    if (currentOrganization) {
      setOrgDetails({
        name: currentOrganization.name,
        description: currentOrganization.description || '',
        website: currentOrganization.website || '',
        subscription_tier: currentOrganization.subscription_tier,
        created_at: currentOrganization.created_at
      });
    }
  }, [currentOrganization]);

  const loadOrganizationData = async () => {
    if (!currentOrganization) return;
    
    setLoading(true);
    setError('');
    
    try {
      switch (tabValue) {
        case 0: // General - already loaded from context
          break;
        case 1: // Members - always reload to ensure fresh data
          console.log('[OrganizationSettings] Loading members for tab change');
          try {
            await loadMembers();
            console.log('[OrganizationSettings] Members loaded successfully');
          } catch (memberErr: any) {
            console.error('[OrganizationSettings] Error loading members:', memberErr);
            // Don't throw the error, just set it in state
            setError(memberErr.response?.data?.detail || memberErr.message || 'Error loading members');
          }
          break;
        case 2: // Usage
          const usageResponse = await apiService.organizations.getUsage(currentOrganization.id);
          setUsage(usageResponse.data.usage);
          break;
      }
    } catch (err: any) {
      console.error('[OrganizationSettings] Error in loadOrganizationData:', err);
      // Don't set generic errors for specific tab failures - they're handled above
      if (tabValue !== 1) { // Don't overwrite member loading errors
        setError(err.response?.data?.detail || err.message || 'Error loading data');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSaveDetails = async () => {
    if (!currentOrganization || !orgDetails) return;
    
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      await updateOrganization(currentOrganization.id, {
        name: orgDetails.name,
        description: orgDetails.description,
        website: orgDetails.website
      });
      
      setSuccess('Organization successfully updated');
      setIsEditingDetails(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error saving');
    } finally {
      setLoading(false);
    }
  };

  const handleInviteMember = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      await inviteMember(inviteEmail, inviteRole);
      
      setSuccess('Invitation sent successfully');
      setInviteDialogOpen(false);
      setInviteEmail('');
      setInviteRole('member');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error inviting');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    if (!window.confirm('Are you sure you want to remove this member?')) return;
    
    setError('');
    setSuccess('');
    
    try {
      await removeMember(memberId);
      setSuccess('Member successfully removed');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error removing member');
    }
  };

  const handleUpdateMemberRole = async (memberId: string, newRole: string) => {
    setLoading(true);
    setError('');
    
    try {
      await updateMemberRole(memberId, newRole);
      
      setSuccess('Member role updated successfully');
      // Reload members to show updated roles
      await loadMembers();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error updating member role');
      // Reload to revert the UI change
      await loadMembers();
    } finally {
      setLoading(false);
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'owner': return 'error';
      case 'admin': return 'warning';
      case 'member': return 'primary';
      case 'viewer': return 'default';
      default: return 'default';
    }
  };
  
  const handleDeleteOrganization = async () => {
    if (!currentOrganization) return;
    
    if (deleteConfirmation !== currentOrganization.name) {
      setError('Please type the organization name correctly to confirm deletion');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      await deleteOrganization(currentOrganization.id);
      setSuccess('Organization deleted successfully');
      
      // Redirect to home or organizations list after a short delay
      setTimeout(() => {
        navigate('/');
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'Failed to delete organization');
      setLoading(false);
    }
  };

  if (!currentOrganization) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="info">Please select an organization</Alert>
      </Container>
    );
  }

  const currentUserRole = members.find(m => m.is_current_user)?.role;
  const isOwner = currentUserRole === 'owner';

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Paper elevation={3}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs 
            value={tabValue} 
            onChange={(_event, newValue) => {
              // Clear any previous errors when switching tabs
              setError('');
              setSuccess('');
              // Update the tab value
              setTabValue(newValue);
            }}
            aria-label="organization settings tabs"
          >
            <Tab label="Allgemein" id="org-tab-0" aria-controls="org-tabpanel-0" />
            <Tab label="Members" id="org-tab-1" aria-controls="org-tabpanel-1" />
            <Tab label="Nutzung" id="org-tab-2" aria-controls="org-tabpanel-2" />
            <Tab label="Danger Zone" id="org-tab-3" aria-controls="org-tabpanel-3" sx={{ color: 'error.main' }} />
          </Tabs>
        </Box>

        {error && <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ m: 2 }}>{success}</Alert>}

        <TabPanel value={tabValue} index={0}>
          <OrganizationDetails
            organization={currentOrganization}
            orgDetails={orgDetails}
            setOrgDetails={setOrgDetails}
            isEditingDetails={isEditingDetails}
            setIsEditingDetails={setIsEditingDetails}
            handleSaveDetails={handleSaveDetails}
            loading={loading}
            orgLoading={orgLoading}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <OrganizationMembers
            members={members}
            loading={loading}
            currentUserRole={currentUserRole}
            onInviteMember={() => setInviteDialogOpen(true)}
            onUpdateMemberRole={handleUpdateMemberRole}
            onRemoveMember={handleRemoveMember}
            getRoleColor={getRoleColor}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <OrganizationUsage
            usage={usage}
            loading={loading}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <OrganizationDangerZone
            isOwner={isOwner}
            loading={loading}
            onDeleteOrganization={() => setDeleteDialogOpen(true)}
          />
        </TabPanel>
      </Paper>

      {/* Dialogs */}
      <InviteMemberDialog
        open={inviteDialogOpen}
        inviteEmail={inviteEmail}
        inviteRole={inviteRole}
        loading={loading}
        onClose={() => setInviteDialogOpen(false)}
        onEmailChange={setInviteEmail}
        onRoleChange={setInviteRole}
        onInvite={handleInviteMember}
      />

      <DeleteOrganizationDialog
        open={deleteDialogOpen}
        organizationName={currentOrganization?.name || ''}
        deleteConfirmation={deleteConfirmation}
        loading={loading}
        error={error}
        onClose={() => {
          setDeleteDialogOpen(false);
          setDeleteConfirmation('');
          setError('');
        }}
        onConfirmationChange={setDeleteConfirmation}
        onDelete={handleDeleteOrganization}
      />
    </Container>
  );
};

export default OrganizationSettings;