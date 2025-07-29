import api from './api';

export interface OrganizationGoalRequest {
  description: string;
  user_feedback?: string;
  previous_result?: string;
}

export interface OrganizationGoalResponse {
  improved_description: string;
  organization_purpose: string;
  primary_goals: string[];
  success_metrics: string[];
  value_proposition: string;
}

export interface DepartmentSuggestion {
  name: string;
  description: string;
  goals: string[];
  key_responsibilities: string[];
}

export interface DepartmentStructureRequest {
  organization_description: string;
  organization_goals?: string[];
  industry?: string;
  company_size?: string;
  user_feedback?: string;
  previous_result?: DepartmentSuggestion[];
}

export interface DepartmentStructureResponse {
  departments: DepartmentSuggestion[];
  rationale: string;
}

export interface KeyResult {
  metric: string;
  target: string;
  timeframe: string;
  measurement_method: string;
}

export interface Milestone {
  name: string;
  description: string;
  deliverables: string[];
  estimated_completion: string;
  success_criteria: string[];
}

export interface ProjectDescriptionRequest {
  raw_description: string;
  organization_purpose: string;
  organization_goals: string[];
  department?: string;
  user_feedback?: string;
  previous_result?: any;
}

export interface ProjectDescriptionResponse {
  project_name: string;
  executive_summary: string;
  detailed_description: string;
  objectives: string[];
  key_results: KeyResult[];
  milestones: Milestone[];
  success_factors: string[];
  risks_and_mitigations: { [key: string]: string };
}

export interface ProjectTask {
  title: string;
  description: string;
  category: string;
  priority: string;
  estimated_hours: number;
  dependencies: string[];
  deliverables: string[];
  acceptance_criteria: string[];
  skills_required: string[];
}

export interface ProjectTaskRequest {
  project_description: string;
  project_objectives: string[];
  project_milestones: any[];
  organization_context: string;
  department?: string;
  team_size?: number;
  timeline?: string;
  user_feedback?: string;
  previous_tasks?: any[];
}

export interface ProjectTaskResponse {
  tasks: ProjectTask[];
  task_summary: { [category: string]: number };
  critical_path: string[];
  resource_requirements: { [key: string]: string };
}

class OrganizationManagementService {
  async improveOrganizationGoals(request: OrganizationGoalRequest): Promise<OrganizationGoalResponse> {
    try {
      const response = await api.post(
        '/api/organization-management/improve-organization-goals',
        request
      );
      return response.data.data;
    } catch (error: any) {
      console.error('[OrgManagement] Error improving organization goals:', error);
      throw error;
    }
  }

  async suggestDepartments(request: DepartmentStructureRequest): Promise<DepartmentStructureResponse> {
    try {
      const response = await api.post(
        '/api/organization-management/suggest-departments',
        request
      );
      return response.data.data;
    } catch (error: any) {
      console.error('[OrgManagement] Error suggesting departments:', error);
      throw error;
    }
  }

  async enhanceProjectDescription(request: ProjectDescriptionRequest): Promise<ProjectDescriptionResponse> {
    try {
      const response = await api.post(
        '/api/organization-management/enhance-project-description',
        request
      );
      return response.data.data;
    } catch (error: any) {
      console.error('[OrgManagement] Error enhancing project description:', error);
      throw error;
    }
  }

  async generateProjectTasks(request: ProjectTaskRequest): Promise<ProjectTaskResponse> {
    try {
      const response = await api.post(
        '/api/organization-management/generate-project-tasks',
        request
      );
      return response.data.data;
    } catch (error: any) {
      console.error('[OrgManagement] Error generating project tasks:', error);
      throw error;
    }
  }
}

export const organizationManagementService = new OrganizationManagementService();