import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Title2,
  Spinner,
  Text,
  Dialog,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogContent,
  DialogActions,
  Button,
  makeStyles,
  tokens,
} from "@fluentui/react-components";
import TagForm from "../components/TagForm";
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
});

export default function TagEditPage() {
  const styles = useStyles();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { tag, loading, error } = useTag(id);
  const [retireOpen, setRetireOpen] = useState(false);

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
      <TagForm
        mode="edit"
        initialData={tag}
        onSubmit={handleSubmit}
        onCancel={() => navigate("/tags")}
        onRetire={() => setRetireOpen(true)}
      />

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
    </div>
  );
}
