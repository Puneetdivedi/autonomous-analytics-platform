import apiClient from './apiClient';
import { Project } from '@/types';

export interface ProjectInput {
  name: string;
  description: string;
}

export const projectService = {
  async list(): Promise<Project[]> {
    const { data } = await apiClient.get<Project[]>('/projects');
    return data;
  },

  async get(id: string): Promise<Project> {
    const { data } = await apiClient.get<Project>(`/projects/${id}`);
    return data;
  },

  async create(input: ProjectInput): Promise<Project> {
    const { data } = await apiClient.post<Project>('/projects', input);
    return data;
  },

  async update(id: string, input: Partial<ProjectInput>): Promise<Project> {
    const { data } = await apiClient.patch<Project>(`/projects/${id}`, input);
    return data;
  },

  async remove(id: string): Promise<void> {
    await apiClient.delete(`/projects/${id}`);
  },
};
