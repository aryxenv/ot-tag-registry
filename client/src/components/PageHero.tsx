import {
  Body1,
  makeStyles,
  mergeClasses,
  shorthands,
  Title1,
  tokens,
} from "@fluentui/react-components";
import type { ReactNode } from "react";
import { aperamTokens } from "../theme/aperamTheme";
import SweepCurve from "./SweepCurve";

interface PageHeroProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  className?: string;
}

const useStyles = makeStyles({
  root: {
    position: "relative",
    overflow: "hidden",
    color: aperamTokens.white,
    backgroundImage: `linear-gradient(125deg, ${aperamTokens.navy900} 0%, ${aperamTokens.navy700} 46%, ${aperamTokens.navy600} 100%)`,
    ...shorthands.borderRadius(tokens.borderRadiusXLarge),
    paddingTop: tokens.spacingVerticalXXL,
    paddingBottom: tokens.spacingVerticalXXL,
    paddingLeft: tokens.spacingHorizontalXXL,
    paddingRight: tokens.spacingHorizontalXXL,
    marginBottom: tokens.spacingVerticalXXL,
    boxShadow:
      "0 18px 40px -22px rgba(15, 42, 92, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.06)",
    isolation: "isolate",
    "@media (max-width: 720px)": {
      paddingTop: tokens.spacingVerticalXL,
      paddingBottom: tokens.spacingVerticalXL,
      paddingLeft: tokens.spacingHorizontalL,
      paddingRight: tokens.spacingHorizontalL,
    },
  },
  sweep: {
    position: "absolute",
    top: 0,
    right: 0,
    bottom: 0,
    width: "62%",
    opacity: 0.62,
    zIndex: 0,
    "@media (max-width: 720px)": {
      width: "100%",
      opacity: 0.34,
    },
  },
  glow: {
    position: "absolute",
    top: "-40%",
    right: "-10%",
    width: "55%",
    height: "180%",
    background:
      "radial-gradient(circle, rgba(33, 80, 176, 0.55) 0%, transparent 65%)",
    pointerEvents: "none",
    zIndex: 0,
  },
  dataGlow: {
    position: "absolute",
    right: "12%",
    top: "18px",
    width: "220px",
    height: "78px",
    borderRadius: "999px",
    background:
      "linear-gradient(90deg, transparent 0%, rgba(80, 230, 255, 0.22) 50%, transparent 100%)",
    filter: "blur(18px)",
    opacity: 0.75,
    pointerEvents: "none",
    zIndex: 0,
  },
  inner: {
    position: "relative",
    zIndex: 1,
    display: "flex",
    alignItems: "flex-end",
    justifyContent: "space-between",
    gap: tokens.spacingHorizontalXL,
    flexWrap: "wrap",
    "@media (max-width: 720px)": {
      alignItems: "stretch",
    },
  },
  textBlock: {
    display: "flex",
    flexDirection: "column",
    gap: tokens.spacingVerticalS,
    minWidth: 0,
  },
  lockup: {
    marginBottom: tokens.spacingVerticalXS,
  },
  eyebrow: {
    display: "inline-flex",
    alignItems: "center",
    gap: tokens.spacingHorizontalXS,
    color: aperamTokens.azureCyan,
    fontFamily: aperamTokens.displayFont,
    fontSize: tokens.fontSizeBase200,
    fontWeight: 600,
    letterSpacing: "0.18em",
    textTransform: "uppercase",
  },
  eyebrowDot: {
    width: "6px",
    height: "6px",
    borderRadius: "50%",
    backgroundColor: aperamTokens.microsoftBlueLight,
    boxShadow: "0 0 0 4px rgba(80, 230, 255, 0.18)",
  },
  title: {
    color: aperamTokens.white,
    fontFamily: aperamTokens.displayFont,
    fontWeight: 600,
    letterSpacing: "-0.015em",
    lineHeight: 1.1,
  },
  subtitle: {
    color: "rgba(255, 255, 255, 0.78)",
    maxWidth: "640px",
  },
  chips: {
    display: "flex",
    alignItems: "center",
    gap: tokens.spacingHorizontalXS,
    flexWrap: "wrap",
    marginTop: tokens.spacingVerticalXS,
  },
  chip: {
    display: "inline-flex",
    alignItems: "center",
    borderRadius: "999px",
    paddingTop: "3px",
    paddingBottom: "3px",
    paddingLeft: tokens.spacingHorizontalS,
    paddingRight: tokens.spacingHorizontalS,
    backgroundColor: "rgba(0, 120, 212, 0.18)",
    border: "1px solid rgba(80, 230, 255, 0.26)",
    color: "rgba(255, 255, 255, 0.82)",
    fontFamily: aperamTokens.displayFont,
    fontSize: "11px",
    fontWeight: 600,
    letterSpacing: "0.04em",
  },
  rule: {
    width: "56px",
    height: "3px",
    backgroundColor: aperamTokens.orange500,
    borderRadius: "2px",
    marginTop: tokens.spacingVerticalS,
    boxShadow: aperamTokens.orangeGlow,
  },
  actions: {
    display: "flex",
    alignItems: "center",
    gap: tokens.spacingHorizontalS,
    flexShrink: 0,
    "@media (max-width: 720px)": {
      width: "100%",
      justifyContent: "flex-start",
    },
  },
});

export default function PageHero({
  title,
  subtitle,
  actions,
  className,
}: PageHeroProps) {
  const styles = useStyles();

  return (
    <section className={mergeClasses(styles.root, className)}>
      <div className={styles.glow} />
      <div className={styles.dataGlow} />
      <SweepCurve variant="hero" className={styles.sweep} />
      <div className={styles.inner}>
        <div className={styles.textBlock}>
          <Title1 as="h1" className={styles.title}>
            {title}
          </Title1>
          {subtitle && <Body1 className={styles.subtitle}>{subtitle}</Body1>}
          <div className={styles.rule} />
        </div>
        {actions && <div className={styles.actions}>{actions}</div>}
      </div>
    </section>
  );
}
