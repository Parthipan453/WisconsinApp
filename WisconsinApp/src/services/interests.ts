import { api } from './api';

export interface Interest {
  id: number;
  name: string;
}

export const getInterests = async (): Promise<Interest[]> => {
  const response = await api.get<Interest[]>('/interests/');
  return response.data;
};