export enum UserRole {
  CITIZEN = 'CITIZEN',
  ADMIN = 'ADMIN',
  OFFICER = 'OFFICER',
}

export enum ModelReadinessStatus {
  OBJECT_DETECTION_SUPPORTED = 'OBJECT_DETECTION_SUPPORTED',
  IMAGE_CLASSIFICATION_ONLY = 'IMAGE_CLASSIFICATION_ONLY',
  PENDING_MANUAL_TRAINING = 'PENDING_MANUAL_TRAINING',
  INSUFFICIENT_SUITABLE_DATA = 'INSUFFICIENT_SUITABLE_DATA',
  ANALYSIS_FAILED = 'ANALYSIS_FAILED',
  FUTURE_SCOPE = 'FUTURE_SCOPE',
}

export interface DefectCategoryMeta {
  name: string;
  domain: 'Road' | 'Sanitation' | 'Drainage';
  capability: ModelReadinessStatus;
  capabilityLabel: string;
  modelType: 'object_detection' | 'image_classification' | 'pending';
  description: string;
}

export const ACTIVE_12_CATEGORIES: DefectCategoryMeta[] = [
  // Road-related defects (5)
  {
    name: 'Pothole',
    domain: 'Road',
    capability: ModelReadinessStatus.OBJECT_DETECTION_SUPPORTED,
    capabilityLabel: 'Object detection supported by a compatible model',
    modelType: 'object_detection',
    description: 'Cavity or depression in asphalt (YOLOv8 RDD2020 India).'
  },
  {
    name: 'Longitudinal Crack',
    domain: 'Road',
    capability: ModelReadinessStatus.OBJECT_DETECTION_SUPPORTED,
    capabilityLabel: 'Object detection supported by a compatible model',
    modelType: 'object_detection',
    description: 'Fracture parallel to road direction (YOLOv8 RDD2020 India).'
  },
  {
    name: 'Transverse Crack',
    domain: 'Road',
    capability: ModelReadinessStatus.OBJECT_DETECTION_SUPPORTED,
    capabilityLabel: 'Object detection supported by a compatible model',
    modelType: 'object_detection',
    description: 'Fracture perpendicular to centerline (YOLOv8 RDD2020 India; 9 test samples).'
  },
  {
    name: 'Alligator Crack',
    domain: 'Road',
    capability: ModelReadinessStatus.OBJECT_DETECTION_SUPPORTED,
    capabilityLabel: 'Object detection supported by a compatible model',
    modelType: 'object_detection',
    description: 'Interconnected fatigue fractures (YOLOv8 RDD2020 India).'
  },
  {
    name: 'Damaged Road Surface',
    domain: 'Road',
    capability: ModelReadinessStatus.IMAGE_CLASSIFICATION_ONLY,
    capabilityLabel: 'Image classification only',
    modelType: 'image_classification',
    description: 'Raveling / weathered shoulder (IRDID broken_edges; whole-image scene classification, no bounding boxes).'
  },
  // Sanitation defects (3)
  {
    name: 'Garbage Accumulation',
    domain: 'Sanitation',
    capability: ModelReadinessStatus.PENDING_MANUAL_TRAINING,
    capabilityLabel: 'Pending manual training',
    modelType: 'pending',
    description: 'Accumulated solid waste (Indian Domestic Trash dataset pending training).'
  },
  {
    name: 'Illegal Dumping',
    domain: 'Sanitation',
    capability: ModelReadinessStatus.PENDING_MANUAL_TRAINING,
    capabilityLabel: 'Pending manual training',
    modelType: 'pending',
    description: 'Unauthorized large-scale disposal of rubble or commercial waste.'
  },
  {
    name: 'Overflowing Garbage Bins',
    domain: 'Sanitation',
    capability: ModelReadinessStatus.PENDING_MANUAL_TRAINING,
    capabilityLabel: 'Pending manual training',
    modelType: 'pending',
    description: 'Municipal dustbin exceeding capacity with waste spillover.'
  },
  // Drainage defects (4)
  {
    name: 'Blocked Drains',
    domain: 'Drainage',
    capability: ModelReadinessStatus.INSUFFICIENT_SUITABLE_DATA,
    capabilityLabel: 'Insufficient suitable data',
    modelType: 'pending',
    description: 'Stormwater canal clogged by silt/debris. Field collection required.'
  },
  {
    name: 'Overflowing Drains',
    domain: 'Drainage',
    capability: ModelReadinessStatus.INSUFFICIENT_SUITABLE_DATA,
    capabilityLabel: 'Insufficient suitable data',
    modelType: 'pending',
    description: 'Drain water spilling over canal banks onto roadways. Field collection required.'
  },
  {
    name: 'Waterlogging',
    domain: 'Drainage',
    capability: ModelReadinessStatus.IMAGE_CLASSIFICATION_ONLY,
    capabilityLabel: 'Image classification only',
    modelType: 'image_classification',
    description: 'Whole-image submerged road scene (IRDID waterlogged_roads; distinct from localized water-region detection, no bounding boxes).'
  },
  {
    name: 'Damaged Drainage Covers',
    domain: 'Drainage',
    capability: ModelReadinessStatus.INSUFFICIENT_SUITABLE_DATA,
    capabilityLabel: 'Insufficient suitable data',
    modelType: 'pending',
    description: 'Broken, collapsed, or displaced stormwater drain slabs/culvert grates. Distinct from sewer manholes.'
  },
];

export enum IssueType {
  // Road-related defects (5)
  POTHOLE = 'Pothole',
  LONGITUDINAL_CRACK = 'Longitudinal Crack',
  TRANSVERSE_CRACK = 'Transverse Crack',
  ALLIGATOR_CRACK = 'Alligator Crack',
  DAMAGED_ROAD_SURFACE = 'Damaged Road Surface',
  ROAD_DAMAGE = 'Road Damage', // Legacy umbrella (quarantined)

  // Sanitation defects (3)
  GARBAGE = 'Garbage Accumulation',
  ILLEGAL_DUMPING = 'Illegal Dumping',
  OVERFLOWING_BINS = 'Overflowing Garbage Bins',

  // Drainage defects (4)
  BLOCKED_DRAIN = 'Blocked Drains',
  OVERFLOWING_DRAIN = 'Overflowing Drains',
  WATERLOGGING = 'Waterlogging',
  DAMAGED_DRAINAGE_COVER = 'Damaged Drainage Covers',

  // Utility Civic Defects (Quarantined outside active 12-category workflow)
  STREETLIGHT = 'Broken Streetlight',
  MANHOLE = 'Open Manhole',
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
  detected_defects?: Array<{
    category: string;
    confidence: number;
    model_id?: string;
    bounding_box?: number[];
  }>;
  model_provenance?: Record<string, any>;
  defect_area_ratio: number;
  annotated_image_url?: string;
  original_image_url: string;
  message?: string;
  error?: string;
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
  detected_defects_json?: string | null;
  model_provenance_json?: string | null;
  verified_category?: string | null;
  ai_analysis_status?: string | null;
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
