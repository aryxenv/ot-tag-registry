import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Title2,
  Subtitle2,
  Spinner,
  Text,
  Dialog,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogContent,
  DialogActions,
  Button,
  Divider,
  MessageBar,
  MessageBarBody,
  Textarea,
  makeStyles,
  tokens,
} from "@fluentui/react-components";
import TagForm from "../components/TagForm";
import L1RulePanel from "../components/L1RulePanel";
import L2RulePanel from "../components/L2RulePanel";
import ApprovalBadge from "../components/ApprovalBadge";
import { useTag } from "../hooks/useTag";
import type { CreateTag } from "../types/tag";

const useStyles = makeStyles({
  header: {
    marginBottom: tokens.spacingVerticalS,
  },
  center: {
    display: "flex",
    justifyContent: "center",
    paddingTop: tokens.spacingVerticalXXL,
  },
  errorText: {
    color: tokens.colorPaletteRedForeground1,
  },
  rulesSection: {
    maxWidth: "720px",
    display: "flex",
    flexDirection: "column",
    gap: tokens.spacingVerticalM,
    paddingTop: tokens.spacingVerticalXXL,
  },
  rulesSectionHeader: {
    marginBottom: tokens.spacingVerticalXS,
  },
  approvalRow: {
    display: "flex",
    alignItems: "center",
    gap: tokens.spacingHorizontalM,
    marginBottom: tokens.spacingVerticalM,
  },
});

export default function TagEditPage() {
  const styles = useStyles();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { tag, loading, error, refetch } = useTag(id);
  const [retireOpen, setRetireOpen] = useState(false);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  const handleSubmit = async (data: CreateTag) => {
    // Strip assetId — cannot change asset on update
    const updateData = {
      name: data.name,
      description: data.description,
      unit: data.unit,
      datatype: data.datatype,
      samplingFrequency: data.samplingFrequency,
      criticality: data.criticality,
      sourceId: data.sourceId,
    };
    const res = await fetch(`/api/tags/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updateData),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      let msg = "Failed to update tag";
      if (body?.detail) {
        if (typeof body.detail === "string") {
          msg = body.detail;
        } else if (body.detail.error) {
          msg = body.detail.error;
          if (body.detail.details?.length) {
            msg += ": " + body.detail.details.join(", ");
          }
        }
      }
      throw new Error(msg);
    }
    navigate("/tags");
  };

  const handleRetire = async () => {
    const res = await fetch(`/api/tags/${id}/retire`, { method: "PATCH" });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      let msg = "Failed to retire tag";
      if (body?.detail) {
        if (typeof body.detail === "string") {
          msg = body.detail;
        } else if (body.detail.error) {
          msg = body.detail.error;
        }
      }
      throw new Error(msg);
    }
    navigate("/tags");
  };

  const handleRequestApproval = async () => {
    const res = await fetch(`/api/tags/${id}/request-approval`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Failed to request approval");
    refetch();
  };

  const handleApprove = async () => {
    const res = await fetch(`/api/tags/${id}/approve`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to approve tag");
    refetch();
  };

  const handleReject = async () => {
    const res = await fetch(`/api/tags/${id}/reject`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rejectionReason: rejectReason || null }),
    });
    if (!res.ok) throw new Error("Failed to reject tag");
    setRejectOpen(false);
    setRejectReason("");
    refetch();
  };

  if (loading) {
    return (
      <div className={styles.center}>
        <Spinner label="Loading tag..." />
      </div>
    );
  }

  if (error || !tag) {
    return (
      <div className={styles.center}>
        <Text className={styles.errorText}>
          {error || "Tag not found."}
        </Text>
      </div>
    );
  }

  return (
    <div>
      <Title2 className={styles.header}>Edit Tag</Title2>

      <div className={styles.approvalRow}>
        <ApprovalBadge approvalStatus={tag.approvalStatus ?? "none"} />

        {tag.status === "draft" &&
          (!tag.approvalStatus ||
            tag.approvalStatus === "none" ||
            tag.approvalStatus === "rejected") && (
            <Button appearance="primary" onClick={handleRequestApproval}>
              Request Approval
            </Button>
          )}

        {tag.approvalStatus === "pending" && (
          <>
            <Button appearance="primary" onClick={handleApprove}>
              Approve
            </Button>
            <Button
              appearance="secondary"
              onClick={() => setRejectOpen(true)}
            >
              Reject
            </Button>
          </>
        )}
      </div>

      {tag.approvalStatus === "rejected" && tag.rejectionReason && (
        <MessageBar intent="warning">
          <MessageBarBody>
            <Text weight="semibold">Rejection reason: </Text>
            {tag.rejectionReason}
          </MessageBarBody>
        </MessageBar>
      )}

      <TagForm
        mode="edit"
        initialData={tag}
        onSubmit={handleSubmit}
        onCancel={() => navigate("/tags")}
        onRetire={() => setRetireOpen(true)}
      />

      <div className={styles.rulesSection}>
        <Divider />
        <Subtitle2 className={styles.rulesSectionHeader}>
          Rules Configuration
        </Subtitle2>
        <L1RulePanel tagId={id!} />
        <L2RulePanel tagId={id!} />
      </div>

      <Dialog
        open={retireOpen}
        onOpenChange={(_e, data) => setRetireOpen(data.open)}
      >
        <DialogSurface>
          <DialogBody>
            <DialogTitle>Retire Tag</DialogTitle>
            <DialogContent>
              Are you sure you want to retire &ldquo;{tag.name}&rdquo;? This
              tag will be marked as retired and hidden from the default list
              view.
            </DialogContent>
            <DialogActions>
              <Button
                appearance="secondary"
                onClick={() => setRetireOpen(false)}
              >
                Cancel
              </Button>
              <Button appearance="primary" onClick={handleRetire}>
                Retire
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>

      <Dialog
        open={rejectOpen}
        onOpenChange={(_e, data) => setRejectOpen(data.open)}
      >
        <DialogSurface>
          <DialogBody>
            <DialogTitle>Reject Tag</DialogTitle>
            <DialogContent>
              <Text>
                Optionally provide a reason for rejecting this tag.
              </Text>
              <Textarea
                placeholder="Rejection reason (optional)"
                value={rejectReason}
                onChange={(_e, data) => setRejectReason(data.value)}
                resize="vertical"
              />
            </DialogContent>
            <DialogActions>
              <Button
                appearance="secondary"
                onClick={() => setRejectOpen(false)}
              >
                Cancel
              </Button>
              <Button appearance="primary" onClick={handleReject}>
                Reject
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </div>
  );
}
