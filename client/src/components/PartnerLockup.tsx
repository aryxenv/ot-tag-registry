import {
  makeStyles,
  mergeClasses,
  tokens,
} from "@fluentui/react-components";
import { aperamTokens } from "../theme/aperamTheme";
import microsoftLogo from "../assets/img/microsoft_logo.png";
import aperamLogo from "../assets/img/aperam_logo.png";

interface PartnerLockupProps {
  variant?: "topbar" | "hero";
  className?: string;
}

const useStyles = makeStyles({
  root: {
    display: "inline-flex",
    alignItems: "center",
    gap: tokens.spacingHorizontalS,
    minWidth: 0,
    color: aperamTokens.white,
  },
  topbar: {
    gap: tokens.spacingHorizontalM,
  },
  hero: {
    gap: tokens.spacingHorizontalS,
  },
  logo: {
    display: "block",
    objectFit: "contain",
    objectPosition: "center",
    flexShrink: 0,
  },
  topbarLogo: {
    height: "22px",
    maxWidth: "128px",
  },
  topbarAperamLogo: {
    height: "22px",
    position: "relative",
    top: "5px",
  },
  heroLogo: {
    height: "18px",
    maxWidth: "108px",
  },
  heroAperamLogo: {
    height: "18px",
    position: "relative",
    top: "4px",
  },
  connector: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    color: "rgba(255, 255, 255, 0.48)",
    fontFamily: '"Segoe UI Variable", "Segoe UI", system-ui, sans-serif',
    fontSize: "16px",
    fontWeight: 300,
    lineHeight: 1,
    marginLeft: "-2px",
    marginRight: "-2px",
  },
  heroConnector: {
    fontSize: "13px",
  },
  "@media (max-width: 720px)": {
    topbarLogo: {
      height: "18px",
      maxWidth: "108px",
    },
    topbarAperamLogo: {
      height: "18px",
      top: "4px",
    },
  },
});

export default function PartnerLockup({
  variant = "topbar",
  className,
}: PartnerLockupProps) {
  const styles = useStyles();
  const isHero = variant === "hero";

  return (
    <span
      className={mergeClasses(
        styles.root,
        isHero ? styles.hero : styles.topbar,
        className,
      )}
      aria-label="Microsoft x Aperam"
    >
      <img
        src={microsoftLogo}
        alt=""
        aria-hidden="true"
        className={mergeClasses(
          styles.logo,
          isHero ? styles.heroLogo : styles.topbarLogo,
        )}
      />
      <span
        aria-hidden="true"
        className={mergeClasses(styles.connector, isHero && styles.heroConnector)}
      >
        ×
      </span>
      <img
        src={aperamLogo}
        alt=""
        aria-hidden="true"
        className={mergeClasses(
          styles.logo,
          isHero ? styles.heroLogo : styles.topbarLogo,
          isHero ? styles.heroAperamLogo : styles.topbarAperamLogo,
        )}
      />
    </span>
  );
}
