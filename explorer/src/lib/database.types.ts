export interface Profile {
  id: string;
  email: string;
  display_name: string;
  role: 'admin' | 'user';
  forge_level: 'Observer' | 'Consumer' | 'Contributor' | 'Forgemaster';
  xp: number;
  created_at: string;
  updated_at: string;
}

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: Profile;
        Insert: {
          id: string;
          email: string;
          display_name?: string;
          role?: 'admin' | 'user';
          forge_level?: 'Observer' | 'Consumer' | 'Contributor' | 'Forgemaster';
          xp?: number;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          email?: string;
          display_name?: string;
          role?: 'admin' | 'user';
          forge_level?: 'Observer' | 'Consumer' | 'Contributor' | 'Forgemaster';
          xp?: number;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [];
      };
    };
    Views: Record<string, never>;
    Functions: Record<string, never>;
    Enums: Record<string, never>;
    CompositeTypes: Record<string, never>;
  };
}
