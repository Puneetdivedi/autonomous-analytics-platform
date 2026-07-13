import apiClient from './apiClient';
import { DataSource } from '@/types';

export interface ConnectionInput {
  project_id: string;
  name: string;
  type: string;
  connection_string: string;
}

export const datasourceService = {
  async list(projectId: string): Promise<DataSource[]> {
    const { data } = await apiClient.get<DataSource[]>('/datasources', {
      params: { project_id: projectId },
    });
    return data;
  },

  async createConnection(input: ConnectionInput): Promise<DataSource> {
    const { data } = await apiClient.post<DataSource>(
      '/datasources/connections',
      input
    );
    return data;
  },

  async upload(projectId: string, file: File): Promise<DataSource> {
    const form = new FormData();
    form.append('file', file);
    form.append('project_id', projectId);
    const { data } = await apiClient.post<DataSource>(
      '/datasources/upload',
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return data;
  },

  async introspect(id: string): Promise<DataSource> {
    const { data } = await apiClient.post<DataSource>(
      `/datasources/${id}/introspect`
    );
    return data;
  },
};
