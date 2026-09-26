import { api } from './api';

export interface Program {
  id: number;
  code: string;
  name: string;
  department: string;
  department_code: string;
  degree: string;
  degree_code: string;
  degree_level: string;
  program_type: string;
  program_type_raw: string;
  duration: number;
  total_credits: number;
  description: string;
  status: string;
}

export interface FilterOptions {
  search?: string;
  programType?: string;
  interests?: number[];
}

export const getPrograms = async (
  filters?: FilterOptions
): Promise<Program[]> => {
  const params = new URLSearchParams();
  
  if (filters?.search) {
    params.append('search', filters.search);
  }
  
  if (filters?.programType && filters.programType !== 'all') {
    params.append('program_type', filters.programType);
  }
  
  if (filters?.interests && filters.interests.length > 0) {
    filters.interests.forEach((id) => {
      params.append('interest', id.toString());
    });
  }
  
  const url = params.toString() ? `/programs/?${params.toString()}` : '/programs/';
  const response = await api.get<Program[]>(url);
  return response.data;
};