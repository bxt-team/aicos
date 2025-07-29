import axios from 'axios';
import { KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate } from '../types/knowledgeBase';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class KnowledgeBaseService {
  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': token ? `Bearer ${token}` : '',
    };
  }

  async listKnowledgeBases(
    organizationId: string,
    projectId?: string | null,
    departmentId?: string | null,
    agentType?: string | null
  ): Promise<KnowledgeBase[]> {
    const params = new URLSearchParams();
    params.append('organization_id', organizationId);
    if (projectId) params.append('project_id', projectId);
    if (departmentId) params.append('department_id', departmentId);
    if (agentType) params.append('agent_type', agentType);

    const response = await axios.get(
      `${API_BASE_URL}/api/knowledge-bases?${params.toString()}`,
      { headers: this.getHeaders() }
    );
    return response.data;
  }

  async getKnowledgeBase(id: string): Promise<KnowledgeBase> {
    const response = await axios.get(
      `${API_BASE_URL}/api/knowledge-bases/${id}`,
      { headers: this.getHeaders() }
    );
    return response.data;
  }

  async createKnowledgeBase(formData: FormData): Promise<KnowledgeBase> {
    const response = await axios.post(
      `${API_BASE_URL}/api/knowledge-bases/`,
      formData,
      {
        headers: {
          ...this.getHeaders(),
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  async updateKnowledgeBase(
    id: string,
    update: KnowledgeBaseUpdate
  ): Promise<KnowledgeBase> {
    const response = await axios.put(
      `${API_BASE_URL}/api/knowledge-bases/${id}`,
      update,
      { headers: this.getHeaders() }
    );
    return response.data;
  }

  async deleteKnowledgeBase(id: string): Promise<void> {
    await axios.delete(
      `${API_BASE_URL}/api/knowledge-bases/${id}`,
      { headers: this.getHeaders() }
    );
  }

  async reindexKnowledgeBase(id: string): Promise<void> {
    await axios.post(
      `${API_BASE_URL}/api/knowledge-bases/${id}/reindex`,
      {},
      { headers: this.getHeaders() }
    );
  }

  async getApplicableKnowledgeBases(
    organizationId: string,
    projectId?: string | null,
    departmentId?: string | null,
    agentType?: string | null
  ): Promise<any[]> {
    const params = new URLSearchParams();
    params.append('organization_id', organizationId);
    if (projectId) params.append('project_id', projectId);
    if (departmentId) params.append('department_id', departmentId);
    if (agentType) params.append('agent_type', agentType);

    const response = await axios.get(
      `${API_BASE_URL}/api/knowledge-bases/applicable/search?${params.toString()}`,
      { headers: this.getHeaders() }
    );
    return response.data;
  }
}

export const knowledgeBaseService = new KnowledgeBaseService();