export enum UserRole {
  CITIZEN = 'CITIZEN',
  ADMIN = 'ADMIN',
  OFFICER = 'OFFICER',
}

export enum IssueType {
  POTHOLE = 'Pothole',
  GARBAGE = 'Garbage Accumulation',
  WATERLOGGING = 'Waterlogging',
  STREETLIGHT = 'Broken Streetlight',
  MANHOLE = 'Open Manhole',
  ROAD_DAMAGE = 'Road Damage',
}

export enum IssueStatus {
  REPORTED = 'REPORTED',
  AI_ANALYZED = 'AI_ANALYZED',
  UNDER_REVIEW = 'UNDER_REVIEW',
  ASSIGNED = 'ASSIGNED',
  IN_PROGRESS = 'IN_PROGRESS',
  RESOLVED = 'RESOLVED',
  CLOSED = 'CLOSED',
}

export enum SeverityLevel {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL',
}

export interface User {
  id: number;
  full_name: string;
  email: string;
  role: UserRole;
  department_id?: number | null;
  created_at: string;
}

export interface Department {
  id: number;
  name: string;
  code: string;
  description?: string;
  contact_email?: string;
  created_at: string;
}

export interface BoundingBox {
  class: string;
  confidence: number;
  x: number;
  y: number;
  width: number;
  height: number;
  box_normalized?: number[];
}

export interface AIAnalysisResult {
  status: string;
  issue_type: string | null;
  confidence: number | null;
  severity: SeverityLevel | null;
  priority_score: number | null;
  recommended_department: string | null;
  recommended_department_code: string | null;
  bounding_boxes: BoundingBox[];
  defect_area_ratio: number;
  annotated_image_url?: string;
  original_image_url: string;
}

export interface IssueImage {
  id: number;
  original_image_path: string;
  image_url?: string;
  annotated_image_path?: string;
  bounding_box_json?: string;
  created_at: string;
}

export interface StatusHistory {
  id: number;
  previous_status?: IssueStatus;
  new_status: IssueStatus;
  changed_by: User;
  notes?: string;
  progress_percentage?: number;
  created_at: string;
}

export interface DuplicateRelation {
  id: number;
  duplicate_issue_id: number;
  distance_meters: number;
  similarity_score: number;
  created_at: string;
}

export interface Issue {
  id: number;
  title: string;
  description?: string;
  issue_type: IssueType;
  latitude: number;
  longitude: number;
  address?: string;
  ai_confidence: number;
  severity: SeverityLevel;
  priority_score: number;
  status: IssueStatus;
  reporter_id: number;
  reporter?: User;
  department_id?: number;
  department?: Department;
  images: IssueImage[];
  status_history: StatusHistory[];
  assigned_officer_id?: number | null;
  assigned_officer?: User | null;
  assigned_at?: string | null;
  progress_percentage: number;
  latest_update?: string | null;
  estimated_completion_date?: string | null;
  resolved_at?: string | null;
  closed_at?: string | null;
  duplicate_count: number;
  created_at: string;
  updated_at: string;
}

export interface MapPoint {
  id: number;
  title: string;
  issue_type: string;
  latitude: number;
  longitude: number;
  address?: string;
  status: string;
  severity: string;
  priority_score: number;
  image_url?: string;
  department?: string | null;
  created_at: string;
}

export interface DepartmentStat {
  department_id: number;
  department_name: string;
  total_assigned: number;
  pending: number;
  in_progress: number;
  resolved: number;
  resolution_rate: number;
}

export interface AnalyticsDashboardData {
  total_issues: number;
  open_issues: number;
  in_progress_issues: number;
  resolved_issues: number;
  critical_issues_count: number;
  issues_by_category: Record<string, number>;
  issues_by_severity: Record<string, number>;
  issues_by_status: Record<string, number>;
  department_performance: DepartmentStat[];
}
