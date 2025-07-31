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
  Alert,
  CircularProgress,
  Chip,
  Tooltip,
  Container,
  Breadcrumbs,
  Link,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon,
  Description as DocumentIcon,
  ArrowBack as ArrowBackIcon,
  TextFields as TextFieldsIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { useOrganization } from '../contexts/OrganizationContext';
import { useProject } from '../contexts/ProjectContext';
import { knowledgeBaseService } from '../services/knowledgeBaseService';
import { KnowledgeBase, KnowledgeBaseCreate } from '../types/knowledgeBase';
import { useTranslation } from 'react-i18next';

export default function ProjectKnowledgeBase() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { projectId } = useParams<{ projectId: string }>();
  const { user } = useSupabaseAuth();
  const { currentOrganization } = useOrganization();
  const { projects } = useProject();
  
  const project = projects.find(p => p.id === projectId);
  
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [textDialogOpen, setTextDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedKB, setSelectedKB] = useState<KnowledgeBase | null>(null);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  
  // Upload form state
  const [uploadForm, setUploadForm] = useState({
    name: '',
    description: '',
    file: null as File | null,
  });
  
  // Text form state
  const [textForm, setTextForm] = useState({
    name: '',
    description: '',
    content: '',
  });

  useEffect(() => {
    if (currentOrganization && projectId) {
      fetchKnowledgeBases();
    }
  }, [currentOrganization, projectId]);

  const fetchKnowledgeBases = async () => {
    if (!currentOrganization || !projectId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Fetch only project-specific knowledge bases
      const data = await knowledgeBaseService.listKnowledgeBases(
        currentOrganization.id,
        projectId,
        null, // No department filter
        null  // No agent filter
      );
      setKnowledgeBases(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || t('errors.failedToFetch', { resource: t('knowledgeBase.knowledgeBases').toLowerCase() }));
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!currentOrganization || !projectId || !uploadForm.file) {
      setError(t('errors.requiredField'));
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', uploadForm.file);
      // Only append name if it was explicitly set by the user
      if (uploadForm.name) {
        formData.append('name', uploadForm.name);
      }
      formData.append('description', uploadForm.description || '');
      formData.append('organization_id', currentOrganization.id);
      formData.append('project_id', projectId);
      
      await knowledgeBaseService.createKnowledgeBase(formData);
      
      setSuccess('Knowledge base uploaded successfully');
      setUploadDialogOpen(false);
      setUploadForm({
        name: '',
        description: '',
        file: null,
      });
      fetchKnowledgeBases();
    } catch (err: any) {
      setError(err.message || 'Failed to upload knowledge base');
    } finally {
      setLoading(false);
    }
  };

  const handleTextSubmit = async () => {
    if (!currentOrganization || !projectId || !textForm.name || !textForm.content) {
      setError(t('errors.requiredField'));
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      await knowledgeBaseService.createTextKnowledgeBase({
        name: textForm.name,
        description: textForm.description || '',
        content: textForm.content,
        organization_id: currentOrganization.id,
        project_id: projectId,
      });
      
      setSuccess('Text content added successfully');
      setTextDialogOpen(false);
      setTextForm({
        name: '',
        description: '',
        content: '',
      });
      fetchKnowledgeBases();
    } catch (err: any) {
      setError(err.message || 'Failed to add text content');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async () => {
    if (!selectedKB) return;
    
    setLoading(true);
    setError(null);
    
    try {
      await knowledgeBaseService.updateKnowledgeBase(selectedKB.id, {
        name: selectedKB.name,
        description: selectedKB.description,
      });
      
      setSuccess('Knowledge base updated successfully');
      setEditDialogOpen(false);
      fetchKnowledgeBases();
    } catch (err: any) {
      setError(err.message || 'Failed to update knowledge base');
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
      setError(err.message || 'Failed to delete knowledge base');
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (!project) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">Project not found</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Box mb={3}>
        <Breadcrumbs aria-label="breadcrumb">
          <Link
            component="button"
            variant="body1"
            onClick={() => navigate('/organization-settings/projects')}
            sx={{ textDecoration: 'none', cursor: 'pointer' }}
          >
            {currentOrganization?.name}
          </Link>
          <Link
            component="button"
            variant="body1"
            onClick={() => navigate(`/projects/${projectId}`)}
            sx={{ textDecoration: 'none', cursor: 'pointer' }}
          >
            {project.name}
          </Link>
          <Typography color="text.primary">{t('knowledgeBase.knowledgeBase')}</Typography>
        </Breadcrumbs>
      </Box>

      <Paper elevation={3} sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box display="flex" alignItems="center">
            <IconButton onClick={() => navigate(`/projects/${projectId}`)} sx={{ mr: 2 }}>
              <ArrowBackIcon />
            </IconButton>
            <Typography variant="h5">
              {project.name} - {t('knowledgeBase.knowledgeBase')}
            </Typography>
          </Box>
          <Box>
            <IconButton onClick={fetchKnowledgeBases} disabled={loading}>
              <RefreshIcon />
            </IconButton>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                startIcon={<UploadIcon />}
                onClick={() => setUploadDialogOpen(true)}
                disabled={loading}
              >
                {t('knowledgeBase.uploadDocument')}
              </Button>
              <Button
                variant="outlined"
                startIcon={<TextFieldsIcon />}
                onClick={() => setTextDialogOpen(true)}
                disabled={loading}
              >
                {t('knowledgeBase.addText')}
              </Button>
            </Box>
          </Box>
        </Box>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

        {loading && !knowledgeBases.length ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>{t('common.name')}</TableCell>
                  <TableCell>{t('common.description')}</TableCell>
                  <TableCell>{t('knowledgeBase.fileType')}</TableCell>
                  <TableCell>{t('knowledgeBase.fileSize')}</TableCell>
                  <TableCell>{t('common.uploadedAt')}</TableCell>
                  <TableCell align="right">{t('common.actions')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {knowledgeBases.map((kb) => (
                  <TableRow key={kb.id}>
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        <DocumentIcon sx={{ mr: 1, color: 'text.secondary' }} />
                        {kb.name}
                      </Box>
                    </TableCell>
                    <TableCell>{kb.description || '-'}</TableCell>
                    <TableCell>
                      <Chip label={kb.file_type || 'Unknown'} size="small" />
                    </TableCell>
                    <TableCell>{formatFileSize(kb.file_size || 0)}</TableCell>
                    <TableCell>
                      {new Date(kb.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title={t('common.edit')}>
                        <IconButton
                          onClick={() => {
                            setSelectedKB(kb);
                            setEditDialogOpen(true);
                          }}
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={t('common.delete')}>
                        <IconButton
                          onClick={() => {
                            setSelectedKB(kb);
                            setDeleteConfirmOpen(true);
                          }}
                          color="error"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
                {knowledgeBases.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <Typography color="text.secondary" py={4}>
                        {t('knowledgeBase.noDocuments')}
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Upload Dialog */}
      <Dialog open={uploadDialogOpen} onClose={() => setUploadDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('knowledgeBase.uploadDocument')}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label={t('common.name')}
              value={uploadForm.name}
              onChange={(e) => setUploadForm({ ...uploadForm, name: e.target.value })}
              margin="normal"
              placeholder={uploadForm.file ? uploadForm.file.name.replace(/\.[^/.]+$/, '') : t('knowledgeBase.autoGeneratedFromFileName')}
              helperText={!uploadForm.name && uploadForm.file ? t('knowledgeBase.willUseFileName') : ''}
            />
            <TextField
              fullWidth
              label={t('common.description')}
              value={uploadForm.description}
              onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
              margin="normal"
              multiline
              rows={3}
            />
            <Button
              variant="outlined"
              component="label"
              fullWidth
              sx={{ mt: 2 }}
              startIcon={<UploadIcon />}
            >
              {uploadForm.file ? uploadForm.file.name : t('knowledgeBase.selectFile')}
              <input
                type="file"
                hidden
                accept=".pdf,.txt,.docx,.doc,.md,.markdown"
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
            disabled={loading || !uploadForm.file}
          >
            {t('common.upload')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Text Dialog */}
      <Dialog open={textDialogOpen} onClose={() => setTextDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{t('knowledgeBase.addTextContent')}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label={t('common.name')}
              value={textForm.name}
              onChange={(e) => setTextForm({ ...textForm, name: e.target.value })}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label={t('common.description')}
              value={textForm.description}
              onChange={(e) => setTextForm({ ...textForm, description: e.target.value })}
              margin="normal"
              multiline
              rows={2}
            />
            <TextField
              fullWidth
              label={t('knowledgeBase.content')}
              value={textForm.content}
              onChange={(e) => setTextForm({ ...textForm, content: e.target.value })}
              margin="normal"
              multiline
              rows={10}
              required
              placeholder={t('knowledgeBase.pasteTextHere')}
              helperText={`${textForm.content.length} characters`}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTextDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button
            onClick={handleTextSubmit}
            variant="contained"
            disabled={loading || !textForm.name || !textForm.content}
          >
            {t('common.add')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('knowledgeBase.editDocument')}</DialogTitle>
        <DialogContent>
          {selectedKB && (
            <Box sx={{ mt: 2 }}>
              <TextField
                fullWidth
                label={t('common.name')}
                value={selectedKB.name}
                onChange={(e) => setSelectedKB({ ...selectedKB, name: e.target.value })}
                margin="normal"
                required
              />
              <TextField
                fullWidth
                label={t('common.description')}
                value={selectedKB.description || ''}
                onChange={(e) => setSelectedKB({ ...selectedKB, description: e.target.value })}
                margin="normal"
                multiline
                rows={3}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button
            onClick={handleUpdate}
            variant="contained"
            disabled={loading || !selectedKB?.name}
          >
            {t('common.save')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)}>
        <DialogTitle>{t('knowledgeBase.deleteDocument')}</DialogTitle>
        <DialogContent>
          <Typography>
            {t('knowledgeBase.deleteConfirmation', { name: selectedKB?.name })}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)}>{t('common.cancel')}</Button>
          <Button onClick={handleDelete} color="error" variant="contained" disabled={loading}>
            {t('common.delete')}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}