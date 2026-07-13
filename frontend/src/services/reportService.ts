import apiClient from './apiClient';
import { Report } from '@/types';

export const reportService = {
  async list(projectId: string): Promise<Report[]> {
    const { data } = await apiClient.get<Report[]>('/reports', {
      params: { project_id: projectId },
    });
    return data;
  },

  async download(id: string): Promise<Blob> {
    const { data } = await apiClient.get<Blob>(`/reports/${id}/download`, {
      responseType: 'blob',
    });
    return data;
  },

  downloadUrl(id: string): string {
    return `${apiClient.defaults.baseURL}/reports/${id}/download`;
  },
};
