import { makeStyles, mergeClasses } from "@fluentui/react-components";
import { aperamTokens } from "../theme/aperamTheme";

interface SweepCurveProps {
  variant?: "topbar" | "hero";
  flip?: boolean;
  className?: string;
}

const useStyles = makeStyles({
  root: {
    display: "block",
    pointerEvents: "none",
  },
  flip: {
    transform: "scaleX(-1)",
  },
});

/**
 * Signature co-brand sweep: Aperam's orange industrial curve layered with a
 * restrained Microsoft/Azure data pulse. Decorative only.
 */
export default function SweepCurve({
  variant = "hero",
  flip = false,
  className,
}: SweepCurveProps) {
  const styles = useStyles();
  const isTopbar = variant === "topbar";
  const width = isTopbar ? 480 : 1600;
  const height = isTopbar ? 64 : 220;
  const viewBox = isTopbar ? "0 0 480 64" : "0 0 1600 220";

  const navyPath = isTopbar
    ? "M0,0 L380,0 C300,30 280,55 480,64 L0,64 Z"
    : "M0,0 L1100,0 C900,90 760,180 1600,220 L0,220 Z";

  const orangePath = isTopbar
    ? "M380,0 C300,30 280,55 480,64"
    : "M1100,0 C900,90 760,180 1600,220";

  return (
    <svg
      className={mergeClasses(styles.root, flip && styles.flip, className)}
      width={width}
      height={height}
      viewBox={viewBox}
      preserveAspectRatio="none"
      aria-hidden="true"
      focusable="false"
    >
      <defs>
        <linearGradient id={`sweep-navy-${variant}`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={aperamTokens.navy600} />
          <stop offset="100%" stopColor={aperamTokens.navy800} />
        </linearGradient>
      </defs>
      <path d={navyPath} fill={`url(#sweep-navy-${variant})`} opacity={0.85} />
      {!isTopbar && (
        <>
          <path
            d="M1180,34 C1030,76 930,130 865,190"
            fill="none"
            stroke={aperamTokens.microsoftBlueLight}
            strokeWidth={1.5}
            strokeLinecap="round"
            strokeDasharray="6 12"
            opacity={0.6}
          />
          <path
            d="M1290,82 C1160,110 1085,146 1010,207"
            fill="none"
            stroke={aperamTokens.azureCyan}
            strokeWidth={1.2}
            strokeLinecap="round"
            strokeDasharray="2 14"
            opacity={0.72}
          />
          <circle cx="1120" cy="66" r="4" fill={aperamTokens.azureCyan} opacity={0.8} />
          <circle
            cx="1030"
            cy="142"
            r="3"
            fill={aperamTokens.microsoftBlueLight}
            opacity={0.72}
          />
        </>
      )}
      <path
        d={orangePath}
        fill="none"
        stroke={aperamTokens.orange500}
        strokeWidth={isTopbar ? 2 : 3}
        strokeLinecap="round"
      />
    </svg>
  );
}
