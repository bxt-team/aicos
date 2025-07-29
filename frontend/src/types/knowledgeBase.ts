export interface KnowledgeBase {
  id: string;
  name: string;
  description?: string;
  organization_id: string;
  project_id?: string;
  department_id?: string;
  agent_type?: string;
  file_type: string;
  file_name: string;
  file_size: number;
  file_path: string;
  vector_store_id?: string;
  metadata?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface KnowledgeBaseCreate {
  name: string;
  description?: string;
  organization_id: string;
  project_id?: string;
  department_id?: string;
  agent_type?: string;
  file_type: string;
  file_name: string;
  file_size: number;
  metadata?: Record<string, any>;
  is_active?: boolean;
}

export interface KnowledgeBaseUpdate {
  name?: string;
  description?: string;
  metadata?: Record<string, any>;
  is_active?: boolean;
}