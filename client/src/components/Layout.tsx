import {
  Button,
  makeStyles,
  mergeClasses,
  Text,
  Tooltip,
  tokens,
} from "@fluentui/react-components";
import {
  ChevronLeftRegular,
  ChevronRightRegular,
  TagRegular,
} from "@fluentui/react-icons";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { aperamTokens } from "../theme/aperamTheme";
import PartnerLockup from "./PartnerLockup";
import SweepCurve from "./SweepCurve";

const SIDEBAR_WIDTH = "232px";
const SIDEBAR_COLLAPSED_WIDTH = "72px";
const TOPBAR_HEIGHT = "60px";

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    position: "relative",
    backgroundColor: aperamTokens.steel50,
    zIndex: 1,
  },
  topbar: {
    position: "relative",
    display: "flex",
    alignItems: "center",
    height: TOPBAR_HEIGHT,
    paddingLeft: tokens.spacingHorizontalXL,
    paddingRight: tokens.spacingHorizontalXL,
    backgroundImage: `linear-gradient(95deg, ${aperamTokens.navy900} 0%, ${aperamTokens.navy700} 55%, ${aperamTokens.navy600} 100%)`,
    color: aperamTokens.white,
    flexShrink: 0,
    borderBottom: `1px solid ${aperamTokens.navy900}`,
    boxShadow: "0 6px 18px -10px rgba(15, 42, 92, 0.55)",
    overflow: "hidden",
    zIndex: 2,
    "@media (max-width: 720px)": {
      height: "72px",
      alignItems: "flex-start",
      paddingTop: tokens.spacingVerticalS,
      paddingBottom: tokens.spacingVerticalS,
    },
  },
  topbarSweep: {
    position: "absolute",
    top: 0,
    right: 0,
    bottom: 0,
    width: "320px",
    opacity: 0.7,
    pointerEvents: "none",
    "@media (max-width: 720px)": {
      width: "220px",
      opacity: 0.45,
    },
  },
  topbarPulse: {
    position: "absolute",
    top: 0,
    right: "220px",
    width: "180px",
    height: "100%",
    background:
      "linear-gradient(90deg, transparent 0%, rgba(80, 230, 255, 0.18) 50%, transparent 100%)",
    filter: "blur(10px)",
    pointerEvents: "none",
  },
  brand: {
    display: "flex",
    alignItems: "center",
    gap: tokens.spacingHorizontalM,
    position: "relative",
    zIndex: 1,
    minWidth: 0,
    "@media (max-width: 720px)": {
      alignItems: "flex-start",
      flexDirection: "column",
      gap: "2px",
    },
  },
  brandTitle: {
    fontFamily: aperamTokens.displayFont,
    fontWeight: 500,
    fontSize: "15px",
    letterSpacing: "0.04em",
    color: "rgba(255, 255, 255, 0.92)",
    whiteSpace: "nowrap",
    "@media (max-width: 720px)": {
      fontSize: "12px",
      letterSpacing: "0.02em",
    },
  },
  brandDivider: {
    width: "1px",
    height: "20px",
    backgroundColor: "rgba(255, 255, 255, 0.22)",
    marginLeft: tokens.spacingHorizontalS,
    marginRight: tokens.spacingHorizontalS,
    transform: "translateY(2px)",
    "@media (max-width: 720px)": {
      display: "none",
    },
  },
  body: {
    display: "flex",
    flexDirection: "row",
    flexGrow: 1,
    overflow: "hidden",
    position: "relative",
    zIndex: 1,
  },
  sidebar: {
    display: "flex",
    flexDirection: "column",
    width: SIDEBAR_WIDTH,
    backgroundImage: `linear-gradient(180deg, ${aperamTokens.navy800} 0%, ${aperamTokens.navy900} 100%)`,
    color: "rgba(255, 255, 255, 0.78)",
    paddingTop: tokens.spacingVerticalL,
    paddingBottom: tokens.spacingVerticalL,
    flexShrink: 0,
    borderRight: `1px solid ${aperamTokens.navy900}`,
    position: "relative",
    overflow: "hidden",
    transitionProperty: "width",
    transitionDuration: "180ms",
    transitionTimingFunction: "ease-out",
    "@media (max-width: 720px)": {
      width: SIDEBAR_COLLAPSED_WIDTH,
    },
  },
  sidebarCollapsed: {
    width: SIDEBAR_COLLAPSED_WIDTH,
  },
  sidebarHalo: {
    position: "absolute",
    bottom: "-160px",
    left: "-80px",
    width: "320px",
    height: "320px",
    borderRadius: "50%",
    background:
      "radial-gradient(circle, rgba(241, 81, 27, 0.18) 0%, transparent 70%)",
    pointerEvents: "none",
  },
  sidebarHeader: {
    position: "relative",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: tokens.spacingHorizontalS,
    paddingLeft: tokens.spacingHorizontalL,
    paddingRight: tokens.spacingHorizontalL,
    paddingBottom: tokens.spacingVerticalM,
    "@media (max-width: 720px)": {
      justifyContent: "center",
      paddingLeft: tokens.spacingHorizontalS,
      paddingRight: tokens.spacingHorizontalS,
    },
  },
  sidebarHeaderCollapsed: {
    justifyContent: "center",
    paddingLeft: tokens.spacingHorizontalS,
    paddingRight: tokens.spacingHorizontalS,
  },
  sidebarLabel: {
    color: "rgba(255, 255, 255, 0.45)",
    fontFamily: aperamTokens.displayFont,
    fontSize: "11px",
    fontWeight: 600,
    letterSpacing: "0.22em",
    textTransform: "uppercase",
    "@media (max-width: 720px)": {
      display: "none",
    },
  },
  sidebarLabelHidden: {
    display: "none",
  },
  collapseButton: {
    width: "28px",
    minWidth: "28px",
    height: "28px",
    color: "rgba(255, 255, 255, 0.62)",
    ":hover": {
      color: aperamTokens.white,
      backgroundColor: "rgba(255, 255, 255, 0.06)",
    },
  },
  navList: {
    position: "relative",
    display: "flex",
    flexDirection: "column",
    gap: "2px",
    paddingLeft: tokens.spacingHorizontalS,
    paddingRight: tokens.spacingHorizontalS,
  },
  navLink: {
    position: "relative",
    display: "flex",
    alignItems: "center",
    gap: tokens.spacingHorizontalS,
    paddingTop: "10px",
    paddingBottom: "10px",
    paddingLeft: tokens.spacingHorizontalL,
    paddingRight: tokens.spacingHorizontalM,
    textDecorationLine: "none",
    color: "rgba(255, 255, 255, 0.78)",
    borderRadius: tokens.borderRadiusMedium,
    fontWeight: 500,
    "::before": {
      content: '""',
      position: "absolute",
      left: "4px",
      top: "10px",
      bottom: "10px",
      width: "3px",
      borderRadius: "2px",
      backgroundColor: "transparent",
    },
    ":hover": {
      backgroundColor: "rgba(255, 255, 255, 0.06)",
      color: aperamTokens.white,
      boxShadow: "inset 0 0 0 1px rgba(80, 230, 255, 0.12)",
    },
    ":focus-visible": {
      outlineStyle: "solid",
      outlineWidth: "2px",
      outlineColor: aperamTokens.azureCyan,
      outlineOffset: "2px",
    },
    ":hover::before": {
      backgroundColor: aperamTokens.orange400,
    },
    "@media (max-width: 720px)": {
      justifyContent: "center",
      paddingLeft: tokens.spacingHorizontalS,
      paddingRight: tokens.spacingHorizontalS,
    },
  },
  navLinkCollapsed: {
    justifyContent: "center",
    paddingLeft: tokens.spacingHorizontalS,
    paddingRight: tokens.spacingHorizontalS,
  },
  navLinkActive: {
    backgroundColor: "rgba(241, 81, 27, 0.10)",
    color: aperamTokens.white,
    "::before": {
      backgroundColor: aperamTokens.orange500,
      boxShadow: "0 0 10px rgba(241, 81, 27, 0.6)",
    },
    ":hover": {
      backgroundColor: "rgba(241, 81, 27, 0.14)",
      color: aperamTokens.white,
    },
  },
  navLinkText: {
    color: "inherit",
    fontWeight: 500,
    "@media (max-width: 720px)": {
      display: "none",
    },
  },
  navLinkTextHidden: {
    display: "none",
  },
  sidebarFooter: {
    position: "relative",
    marginTop: "auto",
    paddingLeft: tokens.spacingHorizontalL,
    paddingRight: tokens.spacingHorizontalL,
    paddingTop: tokens.spacingVerticalM,
    color: "rgba(255, 255, 255, 0.42)",
    fontSize: "11px",
    letterSpacing: "0.06em",
    fontFamily: aperamTokens.displayFont,
    borderTop: "1px solid rgba(255, 255, 255, 0.06)",
    "@media (max-width: 720px)": {
      display: "none",
    },
  },
  content: {
    flexGrow: 1,
    overflow: "auto",
    paddingTop: tokens.spacingVerticalXL,
    paddingBottom: tokens.spacingVerticalXXXL,
    paddingLeft: tokens.spacingHorizontalXXXL,
    paddingRight: tokens.spacingHorizontalXXXL,
    backgroundColor: "transparent",
    position: "relative",
    "@media (max-width: 720px)": {
      paddingLeft: tokens.spacingHorizontalM,
      paddingRight: tokens.spacingHorizontalM,
    },
  },
  contentInner: {
    maxWidth: "1280px",
    marginLeft: "auto",
    marginRight: "auto",
    position: "relative",
    zIndex: 1,
  },
});

export default function Layout() {
  const styles = useStyles();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const collapseLabel = sidebarCollapsed ? "Expand navigation" : "Collapse navigation";

  return (
    <div className={styles.root}>
      <header className={styles.topbar}>
        <div className={styles.brand}>
          <PartnerLockup variant="topbar" />
          <span className={styles.brandDivider} />
          <span className={styles.brandTitle}>OT Tag Registry</span>
        </div>
        <div className={styles.topbarPulse} />
        <SweepCurve variant="topbar" className={styles.topbarSweep} />
      </header>
      <div className={styles.body}>
        <nav className={mergeClasses(styles.sidebar, sidebarCollapsed && styles.sidebarCollapsed)}>
          <div className={styles.sidebarHalo} />
          <div
            className={mergeClasses(
              styles.sidebarHeader,
              sidebarCollapsed && styles.sidebarHeaderCollapsed,
            )}
          >
            <div
              className={mergeClasses(
                styles.sidebarLabel,
                sidebarCollapsed && styles.sidebarLabelHidden,
              )}
            >
              Workspace
            </div>
            <Tooltip content={collapseLabel} relationship="label">
              <Button
                appearance="transparent"
                aria-label={collapseLabel}
                className={styles.collapseButton}
                icon={
                  sidebarCollapsed ? (
                    <ChevronRightRegular />
                  ) : (
                    <ChevronLeftRegular />
                  )
                }
                onClick={() => setSidebarCollapsed((value) => !value)}
              />
            </Tooltip>
          </div>
          <div className={styles.navList}>
            <NavLink
              to="/tags"
              className={({ isActive }) =>
                mergeClasses(
                  styles.navLink,
                  sidebarCollapsed && styles.navLinkCollapsed,
                  isActive && styles.navLinkActive,
                )
              }
            >
              <TagRegular />
              <Text
                className={mergeClasses(
                  styles.navLinkText,
                  sidebarCollapsed && styles.navLinkTextHidden,
                )}
              >
                Tags
              </Text>
            </NavLink>
          </div>
        </nav>
        <main className={styles.content}>
          <div className={styles.contentInner}>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
