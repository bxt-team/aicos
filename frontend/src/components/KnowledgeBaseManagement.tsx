import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Card,
  CardContent,
  CardActions,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon,
  Description as DocumentIcon,
  Business as OrganizationIcon,
  Folder as ProjectIcon,
  Group as DepartmentIcon,
  SmartToy as AgentIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { useOrganization } from '../contexts/OrganizationContext';
import { useProject } from '../contexts/ProjectContext';
import { knowledgeBaseService } from '../services/knowledgeBaseService';
import { KnowledgeBase, KnowledgeBaseCreate } from '../types/knowledgeBase';
import { useTranslation } from 'react-i18next';

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
      id={`kb-tabpanel-${index}`}
      aria-labelledby={`kb-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function KnowledgeBaseManagement() {
  const { t } = useTranslation();
  const { user } = useSupabaseAuth();
  const { currentOrganization } = useOrganization();
  const { currentProject } = useProject();
  
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedKB, setSelectedKB] = useState<KnowledgeBase | null>(null);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [departments, setDepartments] = useState<any[]>([]);
  
  // Upload form state
  const [uploadForm, setUploadForm] = useState({
    name: '',
    description: '',
    file: null as File | null,
    scope: 'organization',
    departmentId: '',
    agentType: '',
  });

  const agentTypes = [
    'qa_agent',
    'affirmations_agent',
    'content_workflow_agent',
    'instagram_analyzer_agent',
    'threads_analysis_agent',
    'x_analysis_agent',
  ];

  useEffect(() => {
    if (currentOrganization) {
      fetchKnowledgeBases();
      if (currentProject) {
        fetchDepartments();
      }
    }
  }, [currentOrganization, currentProject, tabValue]);

  const fetchKnowledgeBases = async () => {
    if (!currentOrganization) return;
    
    setLoading(true);
    setError(null);
    
    try {
      let projectId = null;
      let departmentId = null;
      let agentType = null;
      
      // Filter based on current tab
      if (tabValue === 1 && currentProject) {
        projectId = currentProject.id;
      } else if (tabValue === 2 && currentProject) {
        projectId = currentProject.id;
        // Could add department filter here
      } else if (tabValue === 3 && currentProject) {
        projectId = currentProject.id;
        // Could add agent filter here
      }
      
      const data = await knowledgeBaseService.listKnowledgeBases(
        currentOrganization.id,
        projectId,
        departmentId,
        agentType
      );
      setKnowledgeBases(data);
    } catch (err: any) {
      setError(err.message || t('errors.failedToFetch', { resource: t('knowledgeBase.knowledgeBases').toLowerCase() }));
    } finally {
      setLoading(false);
    }
  };

  const fetchDepartments = async () => {
    if (!currentProject) return;
    
    try {
      // Fetch departments - you'll need to implement this service
      // const data = await departmentService.listDepartments(currentProject.id);
      // setDepartments(data);
    } catch (err) {
      console.error('Failed to fetch departments:', err);
    }
  };

  const handleUpload = async () => {
    if (!currentOrganization || !uploadForm.file || !uploadForm.name) {
      setError(t('errors.requiredField'));
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', uploadForm.file);
      formData.append('name', uploadForm.name);
      formData.append('description', uploadForm.description || '');
      formData.append('organization_id', currentOrganization.id);
      
      if (uploadForm.scope !== 'organization' && currentProject) {
        formData.append('project_id', currentProject.id);
      }
      
      if (uploadForm.scope === 'department' && uploadForm.departmentId) {
        formData.append('department_id', uploadForm.departmentId);
      }
      
      if (uploadForm.scope === 'agent' && uploadForm.agentType) {
        formData.append('agent_type', uploadForm.agentType);
      }
      
      await knowledgeBaseService.createKnowledgeBase(formData);
      
      setSuccess('Knowledge base uploaded successfully');
      setUploadDialogOpen(false);
      setUploadForm({
        name: '',
        description: '',
        file: null,
        scope: 'organization',
        departmentId: '',
        agentType: '',
      });
      fetchKnowledgeBases();
    } catch (err: any) {
      setError(err.message || t('errors.failedToCreate', { resource: t('knowledgeBase.knowledgeBase').toLowerCase() }));
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedKB) return;
    
    setLoading(true);
    setError(null);
    
    try {
      await knowledgeBaseService.deleteKnowledgeBase(selectedKB.id);
      setSuccess('Knowledge base deleted successfully');
      setDeleteConfirmOpen(false);
      setSelectedKB(null);
      fetchKnowledgeBases();
    } catch (err: any) {
      setError(err.message || t('errors.failedToDelete', { resource: t('knowledgeBase.knowledgeBase').toLowerCase() }));
    } finally {
      setLoading(false);
    }
  };

  const handleReindex = async (kb: KnowledgeBase) => {
    setLoading(true);
    setError(null);
    
    try {
      await knowledgeBaseService.reindexKnowledgeBase(kb.id);
      setSuccess('Knowledge base reindexing started');
    } catch (err: any) {
      setError(err.message || t('errors.failedToUpdate', { resource: t('knowledgeBase.knowledgeBase').toLowerCase() }));
    } finally {
      setLoading(false);
    }
  };

  const getScopeIcon = (kb: KnowledgeBase) => {
    if (kb.agent_type && kb.department_id) return <AgentIcon />;
    if (kb.agent_type && kb.project_id) return <AgentIcon />;
    if (kb.department_id) return <DepartmentIcon />;
    if (kb.project_id) return <ProjectIcon />;
    return <OrganizationIcon />;
  };

  const getScopeLabel = (kb: KnowledgeBase) => {
    if (kb.agent_type && kb.department_id) return `Agent (${kb.agent_type}) - Department`;
    if (kb.agent_type && kb.project_id) return `Agent (${kb.agent_type}) - Project`;
    if (kb.department_id) return 'Department';
    if (kb.project_id) return 'Project';
    return 'Organization';
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">{t('knowledgeBase.knowledgeBase')} {t('common.management', 'Management')}</Typography>
        <Button
          variant="contained"
          startIcon={<UploadIcon />}
          onClick={() => setUploadDialogOpen(true)}
          disabled={!currentOrganization}
        >
          {t('knowledgeBase.uploadKnowledgeBase', 'Upload Knowledge Base')}
        </Button>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {!currentOrganization ? (
        <Alert severity="info">
          {t('knowledgeBase.selectOrganizationMessage', 'Please select an organization to manage knowledge bases.')}
        </Alert>
      ) : (
        <>
          <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
            <Tab label={t('organization.organization')} />
            <Tab label={t('project.project')} disabled={!currentProject} />
            <Tab label={t('department.department')} disabled={!currentProject} />
            <Tab label={t('knowledgeBase.agent', 'Agent')} disabled={!currentProject} />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            <KnowledgeBaseList
              knowledgeBases={knowledgeBases.filter(kb => !kb.project_id)}
              loading={loading}
              onDelete={(kb) => { setSelectedKB(kb); setDeleteConfirmOpen(true); }}
              onReindex={handleReindex}
              formatFileSize={formatFileSize}
              getScopeIcon={getScopeIcon}
              getScopeLabel={getScopeLabel}
            />
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <KnowledgeBaseList
              knowledgeBases={knowledgeBases.filter(kb => kb.project_id && !kb.department_id && !kb.agent_type)}
              loading={loading}
              onDelete={(kb) => { setSelectedKB(kb); setDeleteConfirmOpen(true); }}
              onReindex={handleReindex}
              formatFileSize={formatFileSize}
              getScopeIcon={getScopeIcon}
              getScopeLabel={getScopeLabel}
            />
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <KnowledgeBaseList
              knowledgeBases={knowledgeBases.filter(kb => kb.department_id && !kb.agent_type)}
              loading={loading}
              onDelete={(kb) => { setSelectedKB(kb); setDeleteConfirmOpen(true); }}
              onReindex={handleReindex}
              formatFileSize={formatFileSize}
              getScopeIcon={getScopeIcon}
              getScopeLabel={getScopeLabel}
            />
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <KnowledgeBaseList
              knowledgeBases={knowledgeBases.filter(kb => kb.agent_type)}
              loading={loading}
              onDelete={(kb) => { setSelectedKB(kb); setDeleteConfirmOpen(true); }}
              onReindex={handleReindex}
              formatFileSize={formatFileSize}
              getScopeIcon={getScopeIcon}
              getScopeLabel={getScopeLabel}
            />
          </TabPanel>
        </>
      )}

      {/* Upload Dialog */}
      <Dialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>{t('knowledgeBase.uploadKnowledgeBase', 'Upload Knowledge Base')}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label={t('common.name')}
              value={uploadForm.name}
              onChange={(e) => setUploadForm({ ...uploadForm, name: e.target.value })}
              required
              fullWidth
            />
            <TextField
              label={t('common.description')}
              value={uploadForm.description}
              onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
              multiline
              rows={3}
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>Scope</InputLabel>
              <Select
                value={uploadForm.scope}
                onChange={(e) => setUploadForm({ ...uploadForm, scope: e.target.value })}
              >
                <MenuItem value="organization">Organization</MenuItem>
                <MenuItem value="project" disabled={!currentProject}>
                  Project
                </MenuItem>
                <MenuItem value="department" disabled={!currentProject}>
                  Department
                </MenuItem>
                <MenuItem value="agent" disabled={!currentProject}>
                  Agent
                </MenuItem>
              </Select>
            </FormControl>
            
            {uploadForm.scope === 'department' && (
              <FormControl fullWidth>
                <InputLabel>Department</InputLabel>
                <Select
                  value={uploadForm.departmentId}
                  onChange={(e) => setUploadForm({ ...uploadForm, departmentId: e.target.value })}
                >
                  {departments.map((dept) => (
                    <MenuItem key={dept.id} value={dept.id}>
                      {dept.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
            
            {uploadForm.scope === 'agent' && (
              <FormControl fullWidth>
                <InputLabel>Agent Type</InputLabel>
                <Select
                  value={uploadForm.agentType}
                  onChange={(e) => setUploadForm({ ...uploadForm, agentType: e.target.value })}
                >
                  {agentTypes.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
            
            <Button
              variant="outlined"
              component="label"
              fullWidth
            >
              {uploadForm.file ? uploadForm.file.name : 'Choose File'}
              <input
                type="file"
                hidden
                accept=".pdf,.txt,.json,.csv,.docx"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    setUploadForm({ ...uploadForm, file });
                  }
                }}
              />
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button
            onClick={handleUpload}
            variant="contained"
            disabled={loading || !uploadForm.file || !uploadForm.name}
          >
            Upload
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteConfirmOpen}
        onClose={() => setDeleteConfirmOpen(false)}
      >
        <DialogTitle>{t('knowledgeBase.deleteKnowledgeBase', 'Delete Knowledge Base')}</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{selectedKB?.name}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)}>{t('common.cancel')}</Button>
          <Button
            onClick={handleDelete}
            color="error"
            variant="contained"
            disabled={loading}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

// Knowledge Base List Component
interface KnowledgeBaseListProps {
  knowledgeBases: KnowledgeBase[];
  loading: boolean;
  onDelete: (kb: KnowledgeBase) => void;
  onReindex: (kb: KnowledgeBase) => void;
  formatFileSize: (bytes: number) => string;
  getScopeIcon: (kb: KnowledgeBase) => React.ReactNode;
  getScopeLabel: (kb: KnowledgeBase) => string;
}

function KnowledgeBaseList({
  knowledgeBases,
  loading,
  onDelete,
  onReindex,
  formatFileSize,
  getScopeIcon,
  getScopeLabel,
}: KnowledgeBaseListProps) {
  const { t } = useTranslation();
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (knowledgeBases.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <DocumentIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" color="text.secondary">
          {t('knowledgeBase.noKnowledgeBasesFound', 'No knowledge bases found')}
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 2 }}>
      {knowledgeBases.map((kb) => (
        <Box key={kb.id}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                {getScopeIcon(kb)}
                <Typography variant="h6" sx={{ ml: 1 }}>
                  {kb.name}
                </Typography>
              </Box>
              {kb.description && (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {kb.description}
                </Typography>
              )}
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip
                  label={getScopeLabel(kb)}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
                <Chip
                  label={kb.file_type.toUpperCase()}
                  size="small"
                  variant="outlined"
                />
                <Chip
                  label={formatFileSize(kb.file_size)}
                  size="small"
                  variant="outlined"
                />
              </Box>
            </CardContent>
            <CardActions>
              <Tooltip title="Reindex">
                <IconButton
                  size="small"
                  onClick={() => onReindex(kb)}
                  color="primary"
                >
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Delete">
                <IconButton
                  size="small"
                  onClick={() => onDelete(kb)}
                  color="error"
                >
                  <DeleteIcon />
                </IconButton>
              </Tooltip>
            </CardActions>
          </Card>
        </Box>
      ))}
    </Box>
  );
}