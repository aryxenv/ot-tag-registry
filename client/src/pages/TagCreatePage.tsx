import { useNavigate } from "react-router-dom";
import { Title2, makeStyles, tokens } from "@fluentui/react-components";
import TagForm from "../components/TagForm";
import type { CreateTag } from "../types/tag";

const useStyles = makeStyles({
  header: {
    marginBottom: tokens.spacingVerticalS,
  },
});

export default function TagCreatePage() {
  const styles = useStyles();
  const navigate = useNavigate();

  const handleSubmit = async (data: CreateTag) => {
    const res = await fetch("/api/tags", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      let msg = "Failed to create tag";
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

  return (
    <div>
      <Title2 className={styles.header}>Create Tag</Title2>
      <TagForm
        mode="create"
        onSubmit={handleSubmit}
        onCancel={() => navigate("/tags")}
      />
    </div>
  );
}
