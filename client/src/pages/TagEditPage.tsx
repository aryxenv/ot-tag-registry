import {
  Button,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
  Divider,
  MessageBar,
  MessageBarBody,
  Spinner,
  Subtitle2,
  Text,
  Textarea,
  makeStyles,
  tokens,
} from "@fluentui/react-components";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ApprovalBadge from "../components/ApprovalBadge";
import L1RulePanel from "../components/L1RulePanel";
import L2RulePanel from "../components/L2RulePanel";
import TagForm from "../components/TagForm";
import PageHero from "../components/PageHero";
import { useRetireTag } from "../hooks/useRetireTag";
import { useTag } from "../hooks/useTag";
import {
  useApproveTag,
  useRejectTag,
  useRequestApproval,
} from "../hooks/useTagApproval";
import { useUpdateTag } from "../hooks/useUpdateTag";
import type { CreateTag } from "../types/tag";
import { aperamTokens } from "../theme/aperamTheme";

const useStyles = makeStyles({
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
    fontFamily: aperamTokens.displayFont,
    color: aperamTokens.navy700,
    letterSpacing: "0.02em",
  },
  approvalRow: {
    display: "flex",
    alignItems: "center",
    gap: tokens.spacingHorizontalM,
    marginBottom: tokens.spacingVerticalL,
  },
  dialogContentStack: {
    display: "flex",
    flexDirection: "column",
    gap: tokens.spacingVerticalM,
  },
});

export default function TagEditPage() {
  const styles = useStyles();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { tag, loading, error } = useTag(id);
  const [retireOpen, setRetireOpen] = useState(false);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  const updateTag = useUpdateTag();
  const retireTag = useRetireTag();
  const requestApproval = useRequestApproval();
  const approveTag = useApproveTag();
  const rejectTagMutation = useRejectTag();

  const handleSubmit = async (data: CreateTag) => {
    const updateData = {
      name: data.name,
      description: data.description,
      unit: data.unit,
      datatype: data.datatype,
      samplingFrequency: data.samplingFrequency,
      criticality: data.criticality,
      sourceId: data.sourceId,
      assetId: data.assetId,
    };
    await updateTag.mutateAsync({ id: id!, data: updateData });
    navigate("/tags");
  };

  const handleRetire = async () => {
    await retireTag.mutateAsync(id!);
    navigate("/tags");
  };

  const handleRequestApproval = async () => {
    await requestApproval.mutateAsync(id!);
  };

  const handleApprove = async () => {
    await approveTag.mutateAsync(id!);
  };

  const handleReject = async () => {
    await rejectTagMutation.mutateAsync({
      tagId: id!,
      rejectionReason: rejectReason || null,
    });
    setRejectOpen(false);
    setRejectReason("");
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
        <Text className={styles.errorText}>{error || "Tag not found."}</Text>
      </div>
    );
  }

  return (
    <div>
      <PageHero title="Edit tag" subtitle={tag.name} />

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
              Are you sure you want to retire &ldquo;{tag.name}&rdquo;? This tag
              will be marked as retired and hidden from the default list view.
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
            <DialogContent className={styles.dialogContentStack}>
              <Text>Optionally provide a reason for rejecting this tag.</Text>
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
