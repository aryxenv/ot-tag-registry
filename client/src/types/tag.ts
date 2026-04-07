/**
 * Tag-related type definitions.
 * Mirrors server/src/models/tag.py
 */

export type DataType = "float" | "int" | "bool" | "string";

export type Criticality = "low" | "medium" | "high" | "critical";

export type TagStatus = "active" | "retired" | "draft";

export type ApprovalStatus = "none" | "pending" | "approved" | "rejected";

export interface Tag {
  id: string;
  name: string;
  description: string;
  unit: string;
  datatype: DataType;
  samplingFrequency: number;
  criticality: Criticality;
  status: TagStatus;
  assetId: string;
  sourceId: string | null;
  approvalStatus: ApprovalStatus;
  rejectionReason: string | null;
  createdAt: string;
  updatedAt: string;
}

/** Request body for POST /api/tags */
export interface CreateTag {
  name: string;
  description: string;
  unit: string;
  datatype: DataType;
  samplingFrequency: number;
  criticality: Criticality;
  assetId: string;
  sourceId?: string | null;
}

/** Request body for PUT /api/tags/:id — all fields optional for partial updates */
export interface UpdateTag {
  name?: string;
  description?: string;
  unit?: string;
  datatype?: DataType;
  samplingFrequency?: number;
  criticality?: Criticality;
  status?: TagStatus;
  sourceId?: string | null;
}

/** A single validation error from the naming validator */
export interface NameValidationError {
  segment: string;
  message: string;
  received: string;
  expected: string | null;
}

/** Response from POST /api/tags/validate-name */
export interface ValidateNameResponse {
  valid: boolean;
  errors: NameValidationError[];
}

/** Request body for POST /api/tags/auto-fill */
export interface AutoFillRequest {
  query: string;
}

/** A single search hit from the golden-tags index */
export interface AutoFillMatch {
  tagName: string;
  description: string;
  score: number;
  site: string;
  line: string;
  equipment: string;
  unit: string;
  datatype: string;
}

/** Response from POST /api/tags/auto-fill */
export interface AutoFillResult {
  site: string | null;
  line: string | null;
  equipment: string | null;
  unit: string | null;
  datatype: string | null;
  name: string | null;
  description: string | null;
  criticality: string | null;
  confidence: number;
  matches: AutoFillMatch[];
}
