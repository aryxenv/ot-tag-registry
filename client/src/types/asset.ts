/**
 * Asset-related type definitions.
 * Mirrors server/src/models/asset.py
 */

export interface Asset {
  id: string;
  site: string;
  line: string;
  equipment: string;
  hierarchy: string;
  description: string | null;
  createdAt: string;
  updatedAt: string;
}

/** Request body for POST /api/assets */
export interface CreateAsset {
  site: string;
  line: string;
  equipment: string;
  description?: string | null;
}
