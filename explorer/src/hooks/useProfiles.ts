import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '../lib/supabase';
import type { Profile } from '../lib/database.types';

/** Fetch all profiles (admin only — RLS enforced server-side). */
export function useAllProfiles(enabled: boolean) {
  return useQuery<Profile[]>({
    queryKey: ['profiles'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('profiles')
        .select('*')
        .order('created_at', { ascending: true });
      if (error) throw error;
      return (data ?? []) as Profile[];
    },
    enabled,
  });
}

/** Update the current user's display name. */
export function useUpdateDisplayName() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, { userId: string; displayName: string }>({
    mutationFn: async ({ userId, displayName }) => {
      const { error } = await supabase
        .from('profiles')
        .update({ display_name: displayName })
        .eq('id', userId);
      if (error) throw error;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });
}
