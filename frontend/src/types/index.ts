export interface Category {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  updated_at: string;
  num_sets?: number;
  total_items?: number;
  total_graded?: number;
}

export interface Year {
  id: number;
  category_id: number;
  year: number;
  is_active: boolean;
  updated_at: string;
  category_name: string;
  num_sets?: number;
  total_items?: number;
  total_graded?: number;
}

export interface Set {
  id: number;
  category_id: number;
  year_id: number;
  set_name: string;
  set_description?: string;
  num_sets?: number;
  total_items?: number;
  is_active: boolean;
  updated_at: string;
  category_name: string;
  year: number;
  num_cards?: number;
  total_graded?: number;
}

export interface Card {
  id: number;
  card_uid: string;
  category_id: number;
  year_id: number;
  set_id: number;
  card_number?: string;
  player?: string;
  detail_url?: string;
  image_url?: string;
  subset_name?: string;
  variation?: string;
  cert_number?: string;
  is_active: boolean;
  updated_at: string;
  category_name: string;
  year: number;
  set_name: string;
}

export interface Grade {
  id: number;
  grade_label: string;
  grade_value?: number;
  is_active: boolean;
}

export interface Population {
  card_uid: string;
  grade_label: string;
  count: number;
  total_graded?: number;
  snapshot_date: string;
  player: string;
  set_name: string;
  year: number;
  category_name: string;
}

export interface DashboardStats {
  total_categories: number;
  total_years: number;
  total_sets: number;
  total_cards: number;
  total_grades: number;
  total_populations: number;
  latest_snapshot?: string;
  recent_activity: ActivityItem[];
}

export interface ActivityItem {
  timestamp: string;
  level: string;
  component?: string;
  operation?: string;
  message: string;
  status?: string;
}

export interface SearchResult {
  type: 'card' | 'set' | 'year' | 'category';
  id: number;
  name: string;
  description?: string;
  category?: string;
  year?: number;
  set_name?: string;
}

export interface PopulationTrends {
  trends: Record<string, number>;
  total_cards: number;
  date_range: {
    start: string;
    end: string;
  };
}
