import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './client';
import type { paths } from './schema';

// Example: GET /api/users/
export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const { data, error } = await api.GET('/api/users/');
      if (error) throw error;
      return data;
    },
  });
}

// Example: GET /api/users/{id}/
export function useUser(id: string) {
  return useQuery({
    queryKey: ['users', id],
    queryFn: async () => {
      const { data, error } = await api.GET('/api/users/{id}/', {
        params: { path: { id } },
      });
      if (error) throw error;
      return data;
    },
    enabled: !!id,
  });
}

// Example: POST /api/users/
export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      body: paths['/api/users/']['post']['requestBody']['content']['application/json']
    ) => {
      const { data, error } = await api.POST('/api/users/', { body });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      // Invalidate users list
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}

// Example: PATCH /api/users/{id}/
export function useUpdateUser(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      body: paths['/api/users/{id}/']['patch']['requestBody']['content']['application/json']
    ) => {
      const { data, error } = await api.PATCH('/api/users/{id}/', {
        params: { path: { id } },
        body,
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users', id] });
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}

// Example: DELETE /api/users/{id}/
export function useDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const { error } = await api.DELETE('/api/users/{id}/', {
        params: { path: { id } },
      });
      if (error) throw error;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}
