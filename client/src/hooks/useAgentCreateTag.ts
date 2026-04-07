import { useState, useCallback, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { translateText, autoFillTag, fetchNextAvailableName, createTag } from "../api/mutations";
import { fetchApi } from "../api/client";
import { tagKeys, assetKeys } from "../api/queryKeys";
import type { Asset } from "../types/asset";
import type { Tag, CreateTag, Criticality, DataType } from "../types/tag";

export type StepStatus = "pending" | "running" | "done" | "error" | "skipped" | "awaiting-approval";

export interface AgentStep {
  id: string;
  label: string;
  status: StepStatus;
  detail?: string;
}

export interface PendingPayload {
  createTag: CreateTag;
  display: {
    tagName: string;
    description: string;
    site: string;
    line: string;
    equipment: string;
    unit: string;
    datatype: string;
    criticality: string;
    assetHierarchy: string;
  };
}

interface AgentState {
  steps: AgentStep[];
  pendingPayload: PendingPayload | null;
  result: { tag: Tag } | null;
  error: string | null;
  running: boolean;
}

const INITIAL_STEPS: AgentStep[] = [
  { id: "translate", label: "Translating to English", status: "pending" },
  { id: "autofill", label: "AI auto-fill", status: "pending" },
  { id: "asset", label: "Resolving asset", status: "pending" },
  { id: "name", label: "Resolving tag name", status: "pending" },
  { id: "approval", label: "Awaiting approval", status: "pending" },
  { id: "create", label: "Creating tag", status: "pending" },
];

export function useAgentCreateTag() {
  const queryClient = useQueryClient();
  const [state, setState] = useState<AgentState>({
    steps: [],
    pendingPayload: null,
    result: null,
    error: null,
    running: false,
  });

  // Refs for the approval gate
  const approveRef = useRef<(() => void) | null>(null);
  const rejectRef = useRef<(() => void) | null>(null);

  const updateStep = useCallback((id: string, update: Partial<AgentStep>) => {
    setState((prev) => ({
      ...prev,
      steps: prev.steps.map((s) => (s.id === id ? { ...s, ...update } : s)),
    }));
  }, []);

  const run = useCallback(async (query: string) => {
    setState({
      steps: INITIAL_STEPS.map((s) => ({ ...s })),
      pendingPayload: null,
      result: null,
      error: null,
      running: true,
    });

    let normalisedQuery = query;

    // Step 1: Translate
    updateStep("translate", { status: "running" });
    try {
      const tr = await translateText(query);
      if (tr.wasTranslated) {
        normalisedQuery = tr.text;
        updateStep("translate", { status: "done", detail: tr.text });
      } else {
        updateStep("translate", { status: "skipped", detail: "Already in English" });
      }
    } catch {
      updateStep("translate", { status: "skipped", detail: "Translation unavailable — using original text" });
    }

    // Step 2: Auto-fill
    updateStep("autofill", { status: "running" });
    let autoFillResult;
    try {
      autoFillResult = await autoFillTag(normalisedQuery);
      const fields = [
        autoFillResult.site && `Site: ${autoFillResult.site}`,
        autoFillResult.line && `Line: ${autoFillResult.line}`,
        autoFillResult.equipment && `Equipment: ${autoFillResult.equipment}`,
        autoFillResult.unit && `Unit: ${autoFillResult.unit}`,
        autoFillResult.name && `Name: ${autoFillResult.name}`,
      ].filter(Boolean).join(", ");
      updateStep("autofill", { status: "done", detail: fields || "No fields extracted" });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Auto-fill failed";
      updateStep("autofill", { status: "error", detail: msg });
      setState((prev) => ({ ...prev, error: msg, running: false }));
      return;
    }

    // Step 3: Resolve asset
    updateStep("asset", { status: "running" });
    const site = autoFillResult.site ?? "";
    const line = autoFillResult.line ?? "";
    const equipment = autoFillResult.equipment ?? "";

    let assets: Asset[];
    try {
      assets = await queryClient.fetchQuery({
        queryKey: assetKeys.list(),
        queryFn: () => fetchApi<Asset[]>("/api/assets"),
        staleTime: 5 * 60_000,
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to fetch assets";
      updateStep("asset", { status: "error", detail: msg });
      setState((prev) => ({ ...prev, error: msg, running: false }));
      return;
    }

    const asset = assets.find(
      (a) => a.site === site && a.line === line && a.equipment === equipment,
    );
    if (!asset) {
      const detail = `No asset found for ${site} > ${line} > ${equipment}`;
      updateStep("asset", { status: "error", detail });
      setState((prev) => ({ ...prev, error: detail, running: false }));
      return;
    }
    updateStep("asset", { status: "done", detail: asset.hierarchy });

    // Step 4: Resolve tag name
    updateStep("name", { status: "running" });
    const baseName = autoFillResult.name ?? "";
    if (!baseName) {
      const detail = "AI could not determine a tag name";
      updateStep("name", { status: "error", detail });
      setState((prev) => ({ ...prev, error: detail, running: false }));
      return;
    }
    let resolvedName: string;
    try {
      const nameResult = await fetchNextAvailableName(baseName);
      resolvedName = nameResult.name;
      updateStep("name", { status: "done", detail: resolvedName });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Name resolution failed";
      updateStep("name", { status: "error", detail: msg });
      setState((prev) => ({ ...prev, error: msg, running: false }));
      return;
    }

    // Step 5: Await approval
    const payload: CreateTag = {
      name: resolvedName,
      description: autoFillResult.description ?? normalisedQuery,
      unit: autoFillResult.unit ?? "",
      datatype: (autoFillResult.datatype as DataType) ?? "float",
      samplingFrequency: 1.0,
      criticality: (autoFillResult.criticality as Criticality) ?? "medium",
      assetId: asset.id,
      sourceId: null,
    };

    const pendingPayload: PendingPayload = {
      createTag: payload,
      display: {
        tagName: resolvedName,
        description: payload.description,
        site,
        line,
        equipment,
        unit: payload.unit,
        datatype: payload.datatype,
        criticality: payload.criticality,
        assetHierarchy: `${site} > ${line} > ${equipment}`,
      },
    };

    updateStep("approval", { status: "awaiting-approval" });
    setState((prev) => ({ ...prev, pendingPayload }));

    // Wait for user approval or rejection
    const approved = await new Promise<boolean>((resolve) => {
      approveRef.current = () => resolve(true);
      rejectRef.current = () => resolve(false);
    });

    if (!approved) {
      updateStep("approval", { status: "error", detail: "Cancelled by user" });
      setState((prev) => ({
        ...prev,
        pendingPayload: null,
        running: false,
      }));
      return;
    }

    updateStep("approval", { status: "done", detail: "Approved" });

    // Step 6: Create tag
    updateStep("create", { status: "running" });
    try {
      const tag = await createTag(payload);
      queryClient.invalidateQueries({ queryKey: tagKeys.lists() });
      updateStep("create", { status: "done", detail: tag.name });
      setState((prev) => ({
        ...prev,
        pendingPayload: null,
        result: { tag },
        running: false,
      }));
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Tag creation failed";
      updateStep("create", { status: "error", detail: msg });
      setState((prev) => ({
        ...prev,
        pendingPayload: null,
        error: msg,
        running: false,
      }));
    }
  }, [queryClient, updateStep]);

  const approve = useCallback(() => {
    approveRef.current?.();
    approveRef.current = null;
    rejectRef.current = null;
  }, []);

  const reject = useCallback(() => {
    rejectRef.current?.();
    approveRef.current = null;
    rejectRef.current = null;
  }, []);

  const reset = useCallback(() => {
    // Reject any pending approval before resetting
    rejectRef.current?.();
    approveRef.current = null;
    rejectRef.current = null;
    setState({
      steps: [],
      pendingPayload: null,
      result: null,
      error: null,
      running: false,
    });
  }, []);

  return {
    steps: state.steps,
    pendingPayload: state.pendingPayload,
    result: state.result,
    error: state.error,
    running: state.running,
    run,
    approve,
    reject,
    reset,
  };
}
