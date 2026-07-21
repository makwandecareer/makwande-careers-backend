export type User = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
};

export type ProfileForm = {
  phone: string;
  location: string;
  professional_title: string;
  professional_summary: string;
  linkedin_url: string;
  portfolio_url: string;
  website_url: string;
  visibility: "private" | "employers";
};

export type CareerRecord = Record<string, unknown>;

export type ProfileBundle = {
  user: User;
  profile: ProfileForm | null;
  education: CareerRecord[];
  experience: CareerRecord[];
  skills: CareerRecord[];
  projects: CareerRecord[];
  certifications: CareerRecord[];
  languages: CareerRecord[];
  references: CareerRecord[];
  cvs: CareerRecord[];
  ats_history: CareerRecord[];
  completion: {
    percentage: number;
    sections: Record<string, boolean>;
  };
};

export type GeneratedCV = {
  id?: string;
  title?: string;
  target_role?: string;
  template_key?: string;
  content?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
};

export type ATSResult = {
  score: number;
  matched_keywords: string[];
  missing_keywords: string[];
  recommendations: string[];
};
