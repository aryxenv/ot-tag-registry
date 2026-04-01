import { fetchApi } from "./client";
import type { Tag, CreateTag, ValidateNameResponse } from "../types/tag";
import type { L1Rule, CreateL1Rule, L2Rule, CreateL2Rule } from "../types/rule";

export function createTag(data: CreateTag): Promise<Tag> {
  return fetchApi<Tag>("/api/tags", { method: "POST", body: data });
}

export interface UpdateTagParams {
  id: string;
  data: {
    name?: string;
    description?: string;
    unit?: string;
    datatype?: string;
    samplingFrequency?: number;
    criticality?: string;
    sourceId?: string | null;
  };
}

export function updateTag({ id, data }: UpdateTagParams): Promise<Tag> {
  return fetchApi<Tag>(`/api/tags/${id}`, { method: "PUT", body: data });
}

export function retireTag(id: string): Promise<Tag> {
  return fetchApi<Tag>(`/api/tags/${id}/retire`, { method: "PATCH" });
}

export function requestApproval(tagId: string): Promise<Tag> {
  return fetchApi<Tag>(`/api/tags/${tagId}/request-approval`, { method: "POST" });
}

export function approveTag(tagId: string): Promise<Tag> {
  return fetchApi<Tag>(`/api/tags/${tagId}/approve`, { method: "POST" });
}

export interface RejectTagParams {
  tagId: string;
  rejectionReason?: string | null;
}

export function rejectTag({ tagId, rejectionReason }: RejectTagParams): Promise<Tag> {
  return fetchApi<Tag>(`/api/tags/${tagId}/reject`, {
    method: "POST",
    body: { rejectionReason: rejectionReason || null },
  });
}

export function validateTagName(name: string): Promise<ValidateNameResponse> {
  return fetchApi<ValidateNameResponse>("/api/tags/validate-name", {
    method: "POST",
    body: { name },
  });
}

export interface SaveL1RuleParams {
  tagId: string;
  data: CreateL1Rule;
}

export function saveL1Rule({ tagId, data }: SaveL1RuleParams): Promise<L1Rule> {
  return fetchApi<L1Rule>(`/api/tags/${tagId}/rules/l1`, { method: "POST", body: data });
}

export function deleteL1Rule(tagId: string): Promise<void> {
  return fetchApi(`/api/tags/${tagId}/rules/l1`, { method: "DELETE" });
}

export interface SaveL2RuleParams {
  tagId: string;
  data: CreateL2Rule;
}

export function saveL2Rule({ tagId, data }: SaveL2RuleParams): Promise<L2Rule> {
  return fetchApi<L2Rule>(`/api/tags/${tagId}/rules/l2`, { method: "POST", body: data });
}

export function deleteL2Rule(tagId: string): Promise<void> {
  return fetchApi(`/api/tags/${tagId}/rules/l2`, { method: "DELETE" });
}

export interface NextAvailableNameResponse {
  name: string;
}

export function fetchNextAvailableName(baseName: string): Promise<NextAvailableNameResponse> {
  return fetchApi<NextAvailableNameResponse>("/api/tags/next-available-name", {
    method: "POST",
    body: { baseName },
  });
}
