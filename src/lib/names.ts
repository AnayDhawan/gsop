// Display names for targets, profiles and views. Targets follow the repo rule: Connecting Ridge C1, never C2.
const TARGET: Record<string, string> = {
  connecting_ridge_c1: "Connecting Ridge C1",
  shackleton_rim: "Shackleton rim",
  jezero: "Jezero",
};
const PROFILE: Record<string, string> = {
  base: "Base",
  landing_mobility: "Landing and mobility",
  power_night: "Power and night",
  ice_resources: "Ice resources",
};

export const targetName = (t: string) => TARGET[t] ?? t.replace(/_/g, " ");
export const profileName = (p: string) => PROFILE[p] ?? p.replace(/_/g, " ");

/** "shackleton_rim__base" -> "Shackleton rim, Base" */
export function viewName(view: string): string {
  const [t, p] = view.split("__");
  return p ? `${targetName(t)}, ${profileName(p)}` : targetName(t);
}

export const bodyOfTarget = (t: string): "Moon" | "Mars" => (t === "jezero" ? "Mars" : "Moon");
