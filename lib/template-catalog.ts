export type TemplateColumns = 1 | 2;
export type TemplatePhoto = "with-photo" | "without-photo";
export type TemplateFamily =
  | "classic"
  | "modern"
  | "executive"
  | "academic"
  | "technical"
  | "corporate";

export type FormalTemplate = {
  key: string;
  name: string;
  description: string;
  photo: TemplatePhoto;
  columns: TemplateColumns;
  family: TemplateFamily;
  accent: string;
  recommended?: boolean;
};

const accents = [
  "#006943",
  "#1f4e79",
  "#7a3e3e",
  "#5a4a78",
  "#2f5d62",
  "#3f3f46",
  "#7a5c1e",
  "#305f72",
  "#6b4f4f",
  "#2f6b4f",
];

const names = [
  "Apex",
  "Atlas",
  "Cambridge",
  "Carlton",
  "Cedar",
  "Clarendon",
  "Crest",
  "Diplomat",
  "Dominion",
  "Echelon",
  "Elm",
  "Executive",
  "Foundry",
  "Franklin",
  "Geneva",
  "Harvard",
  "Heritage",
  "Imperial",
  "Kensington",
  "Kingston",
  "Lancaster",
  "Lexington",
  "Manhattan",
  "Meridian",
  "Monarch",
  "Oxford",
  "Park Avenue",
  "Princeton",
  "Regent",
  "Richmond",
  "Riviera",
  "Savoy",
  "Sterling",
  "Stratford",
  "Summit",
  "Sydney",
  "Titan",
  "Trinity",
  "Vanguard",
  "Victoria",
  "Westminster",
  "Windsor",
  "York",
  "Zenith",
  "Corporate",
  "Professional",
  "Graduate",
  "Engineering",
  "Finance",
  "Healthcare",
];

const families: TemplateFamily[] = [
  "classic",
  "modern",
  "executive",
  "academic",
  "technical",
  "corporate",
];

export const formalTemplates: FormalTemplate[] = names.map((name, index) => ({
  key: `formal-${String(index + 1).padStart(2, "0")}`,
  name,
  description:
    index % 3 === 0
      ? "Formal one-column ATS-friendly professional layout."
      : index % 3 === 1
        ? "Structured two-column professional presentation."
        : "Refined formal template for global applications.",
  photo: index % 2 === 0 ? "without-photo" : "with-photo",
  columns: index % 3 === 1 ? 2 : 1,
  family: families[index % families.length],
  accent: accents[index % accents.length],
  recommended: index < 4,
}));
