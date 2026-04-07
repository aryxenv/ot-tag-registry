import { useState } from "react";
import {
  makeStyles,
  mergeClasses,
  tokens,
  Subtitle1,
  Text,
  Button,
} from "@fluentui/react-components";
import { TagRegular, SparkleRegular } from "@fluentui/react-icons";
import { NavLink, Outlet } from "react-router-dom";
import AgentPanel from "./AgentPanel";

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    position: "relative" as const,
    "::after": {
      content: '""',
      position: "fixed",
      bottom: "-400px",
      right: "-400px",
      width: "800px",
      height: "800px",
      borderRadius: "50%",
      background:
        "radial-gradient(circle, #d0672a 0%, #4e1045 40%, transparent 70%)",
      pointerEvents: "none",
      opacity: 0.3,
      zIndex: 0,
    },
  },
  topbar: {
    display: "flex",
    alignItems: "center",
    height: "48px",
    paddingLeft: tokens.spacingHorizontalL,
    paddingRight: tokens.spacingHorizontalL,
    backgroundColor: tokens.colorBrandBackground,
    flexShrink: "0",
  },
  topbarTitle: {
    color: tokens.colorNeutralForegroundOnBrand,
  },
  topbarSpacer: {
    flexGrow: 1,
  },
  topbarButton: {
    color: tokens.colorNeutralForegroundOnBrand,
  },
  body: {
    display: "flex",
    flexDirection: "row",
    flexGrow: "1",
    overflow: "hidden",
  },
  sidebar: {
    display: "flex",
    flexDirection: "column",
    width: "220px",
    backgroundColor: tokens.colorNeutralBackground2,
    borderRight: `1px solid ${tokens.colorNeutralStroke1}`,
    paddingTop: tokens.spacingVerticalS,
    flexShrink: "0",
  },
  navLink: {
    display: "flex",
    alignItems: "center",
    gap: tokens.spacingHorizontalS,
    paddingTop: tokens.spacingVerticalS,
    paddingBottom: tokens.spacingVerticalS,
    paddingLeft: tokens.spacingHorizontalM,
    paddingRight: tokens.spacingHorizontalM,
    marginLeft: tokens.spacingHorizontalS,
    marginRight: tokens.spacingHorizontalS,
    textDecorationLine: "none",
    color: tokens.colorNeutralForeground2,
    borderRadius: tokens.borderRadiusMedium,
    ":hover": {
      backgroundColor: tokens.colorNeutralBackground3,
      color: tokens.colorNeutralForeground1,
    },
  },
  navLinkActive: {
    backgroundColor: tokens.colorBrandBackground2,
    color: tokens.colorBrandForeground1,
    ":hover": {
      backgroundColor: tokens.colorBrandBackground2,
      color: tokens.colorBrandForeground1,
    },
  },
  content: {
    flexGrow: "1",
    overflow: "auto",
    padding: tokens.spacingHorizontalXXL,
    backgroundColor: tokens.colorNeutralBackground1,
  },
});

export default function Layout() {
  const styles = useStyles();
  const [agentOpen, setAgentOpen] = useState(false);

  return (
    <div className={styles.root}>
      <header className={styles.topbar}>
        <Subtitle1 className={styles.topbarTitle}>OT Tag Registry</Subtitle1>
        <div className={styles.topbarSpacer} />
        <Button
          className={styles.topbarButton}
          appearance="subtle"
          icon={<SparkleRegular />}
          onClick={() => setAgentOpen(true)}
        >
          AI Agent
        </Button>
      </header>
      <div className={styles.body}>
        <nav className={styles.sidebar}>
          <NavLink
            to="/tags"
            className={({ isActive }) =>
              mergeClasses(styles.navLink, isActive && styles.navLinkActive)
            }
          >
            <TagRegular />
            <Text>Tags</Text>
          </NavLink>
        </nav>
        <main className={styles.content}>
          <Outlet />
        </main>
      </div>
      <AgentPanel open={agentOpen} onClose={() => setAgentOpen(false)} />
    </div>
  );
}
