/**
 * Tag-related type definitions.
 * Mirrors server/src/models/tag.py
 */

export type DataType = "float" | "int" | "bool" | "string";

export type Criticality = "low" | "medium" | "high" | "critical";

export type TagStatus = "active" | "retired" | "draft";

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

/** Response from POST /api/tags/validate-name */
export interface ValidateNameResponse {
  valid: boolean;
  reason?: string;
}

/** Response from POST /api/tags/suggest-name */
export interface SuggestNameResponse {
  suggestions: string[];
}
