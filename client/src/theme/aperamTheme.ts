import {
  createLightTheme,
  type BrandVariants,
  type Theme,
} from "@fluentui/react-components";

// Aperam navy ramp. Anchored on #0F2A5C..#2150B0 to mirror the deep, premium
// blue from the Aperam x Microsoft AI Day brand deck. Stop 80 is what Fluent
// binds to colorBrandBackground (primary buttons, active accents, etc).
const aperamBrand: BrandVariants = {
  10: "#050B1A",
  20: "#0A1428",
  30: "#0E1D3D",
  40: "#0F2552",
  50: "#0F2A5C",
  60: "#143573",
  70: "#1A4291",
  80: "#2150B0",
  90: "#2E64C8",
  100: "#3F77D9",
  110: "#5589E0",
  120: "#6D9BE7",
  130: "#88AEEC",
  140: "#A4C0F1",
  150: "#C0D2F6",
  160: "#DBE5FA",
};

export const aperamLightTheme: Theme = createLightTheme(aperamBrand);

// Tokens that sit alongside Fluent's brand ramp: the Aperam orange accent and
// a warm steel neutral scale used for surfaces, hairlines, and subtle borders.
// Consume these via `aperamTokens.*` in makeStyles or as CSS variables (see
// index.css) so we never sprinkle hex values across components.
export const aperamTokens = {
  navy900: "#050B1A",
  navy800: "#0A1428",
  navy700: "#0F2A5C",
  navy600: "#143573",
  navy500: "#1A4291",
  navy400: "#2150B0",
  navy100: "#DBE5FA",

  orange600: "#C9410E",
  orange500: "#F1511B",
  orange400: "#FF7A3D",
  orange50: "#FFF1EA",

  microsoftBlueDark: "#005A9E",
  microsoftBlue: "#0078D4",
  microsoftBlueLight: "#2B88D8",
  azureCyan: "#50E6FF",
  azureCyanSoft: "#BDF2FF",
  azureSurface: "#EAF6FF",

  steel900: "#1F2937",
  steel700: "#374151",
  steel500: "#6B7280",
  steel300: "#D1D5DB",
  steel200: "#E5E7EB",
  steel100: "#F3F4F6",
  steel50: "#F8FAFC",

  white: "#FFFFFF",

  shadowSoft:
    "0 1px 2px rgba(15, 42, 92, 0.04), 0 12px 32px -22px rgba(15, 42, 92, 0.18)",
  shadowPanel:
    "0 1px 2px rgba(15, 42, 92, 0.04), 0 8px 24px -18px rgba(15, 42, 92, 0.18)",
  orangeGlow: "0 0 12px rgba(241, 81, 27, 0.45)",
  azureGlow: "0 0 16px rgba(80, 230, 255, 0.35)",

  // Display font stack — Sora variable is loaded via @fontsource-variable/sora
  // in main.tsx; this stack provides graceful fallbacks.
  displayFont:
    '"Sora Variable", "Sora", "Segoe UI Variable", "Segoe UI", system-ui, sans-serif',
} as const;

export type AperamTokens = typeof aperamTokens;
