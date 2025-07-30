import api from './api';
import { KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate } from '../types/knowledgeBase';

class KnowledgeBaseService {

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

    const response = await api.get(
      `/api/knowledge-bases/?${params.toString()}`
    );
    return response.data;
  }

  async getKnowledgeBase(id: string): Promise<KnowledgeBase> {
    const response = await api.get(
      `/api/knowledge-bases/${id}`
    );
    return response.data;
  }

  async createKnowledgeBase(formData: FormData): Promise<KnowledgeBase> {
    const response = await api.post(
      `/api/knowledge-bases/`,
      formData,
      {
        headers: {
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
    const response = await api.put(
      `/api/knowledge-bases/${id}`,
      update
    );
    return response.data;
  }

  async deleteKnowledgeBase(id: string): Promise<void> {
    await api.delete(
      `/api/knowledge-bases/${id}`
    );
  }

  async reindexKnowledgeBase(id: string): Promise<void> {
    await api.post(
      `/api/knowledge-bases/${id}/reindex`,
      {}
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

    const response = await api.get(
      `/api/knowledge-bases/applicable/search/?${params.toString()}`
    );
    return response.data;
  }
}

export const knowledgeBaseService = new KnowledgeBaseService();