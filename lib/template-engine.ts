import type {
  StudioDraft,
  StudioHeaderStyle,
  StudioLayout,
  StudioMargin,
} from "@/lib/cv-studio";

export type TemplateCategory =
  | "ats"
  | "professional"
  | "executive"
  | "creative"
  | "photo";

export type TemplateIndustry =
  | "general"
  | "graduate"
  | "engineering"
  | "technology"
  | "finance"
  | "healthcare"
  | "legal"
  | "sales"
  | "education"
  | "hospitality";

export type TemplateDefinition = {
  key: string;
  name: string;
  description: string;
  category: TemplateCategory;
  industry: TemplateIndustry;
  atsFriendly: boolean;
  premium: boolean;
  photo: boolean;
  layout: StudioLayout;
  headerStyle: StudioHeaderStyle;
  margin: StudioMargin;
  accent: string;
  secondaryAccent: string;
  fontFamily: string;
  headingFont: string;
  fontSize: number;
  lineHeight: number;
  sectionSpacing: number;
  tags: string[];
};

const families = [
  {
    category: "ats" as const,
    names: [
      "ATS Standard",
      "ATS Modern",
      "ATS Executive",
      "ATS Professional",
      "ATS Minimal",
      "ATS Graduate",
      "ATS Technical",
      "ATS Healthcare",
      "ATS Finance",
      "ATS Legal",
    ],
    photo: false,
    atsFriendly: true,
  },
  {
    category: "professional" as const,
    names: [
      "Corporate Blue",
      "Emerald Professional",
      "Platinum",
      "Business Classic",
      "London",
      "New York",
      "Toronto",
      "Cape Town",
      "Sydney",
      "Berlin",
    ],
    photo: false,
    atsFriendly: true,
  },
  {
    category: "executive" as const,
    names: [
      "Gold Executive",
      "Boardroom",
      "Imperial",
      "Monarch",
      "Regent",
      "Sterling",
      "Vanguard",
      "Westminster",
      "Windsor",
      "Zenith",
    ],
    photo: false,
    atsFriendly: true,
  },
  {
    category: "creative" as const,
    names: [
      "Creative One",
      "Designer",
      "Marketing",
      "Digital",
      "Startup",
      "UX Portfolio",
      "Creative Bold",
      "Modern Blocks",
      "Studio",
      "Momentum",
    ],
    photo: false,
    atsFriendly: false,
  },
  {
    category: "photo" as const,
    names: [
      "Executive Photo",
      "Healthcare Photo",
      "Hospitality",
      "Teaching",
      "Customer Service",
      "Sales Professional",
      "Aviation",
      "Real Estate",
      "International",
      "Ambassador",
    ],
    photo: true,
    atsFriendly: false,
  },
];

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

const industries: TemplateIndustry[] = [
  "general",
  "graduate",
  "engineering",
  "technology",
  "finance",
  "healthcare",
  "legal",
  "sales",
  "education",
  "hospitality",
];

const fonts = ["Arial", "Calibri", "Cambria", "Garamond", "Georgia"];
const headingFonts = ["Arial", "Cambria", "Georgia", "Garamond"];

export const templateRegistry: TemplateDefinition[] = families.flatMap(
  (family, familyIndex) =>
    family.names.map((name, index) => {
      const globalIndex = familyIndex * 10 + index;
      const accent = accents[globalIndex % accents.length];
      const layout: StudioLayout =
        family.category === "creative" || globalIndex % 3 === 1
          ? "two-column"
          : "one-column";

      const headerStyle: StudioHeaderStyle =
        family.category === "executive"
          ? index % 2 === 0
            ? "centered"
            : "minimal"
          : family.category === "creative"
            ? index % 2 === 0
              ? "banded"
              : "centered"
            : family.category === "photo"
              ? "banded"
              : index % 4 === 0
                ? "minimal"
                : "classic";

      return {
        key: `template-${String(globalIndex + 1).padStart(2, "0")}`,
        name,
        description:
          family.category === "ats"
            ? "Clean, formal and applicant-tracking-system conscious."
            : family.category === "executive"
              ? "Refined leadership presentation for senior appointments."
              : family.category === "creative"
                ? "Distinctive professional design with modern visual hierarchy."
                : family.category === "photo"
                  ? "Formal photo-enabled layout for client-facing professions."
                  : "Balanced professional design for global applications.",
        category: family.category,
        industry: industries[globalIndex % industries.length],
        atsFriendly: family.atsFriendly,
        premium: globalIndex % 4 !== 0,
        photo: family.photo,
        layout,
        headerStyle,
        margin: globalIndex % 5 === 0 ? "wide" : "standard",
        accent,
        secondaryAccent: `${accent}18`,
        fontFamily: fonts[globalIndex % fonts.length],
        headingFont: headingFonts[globalIndex % headingFonts.length],
        fontSize: globalIndex % 5 === 0 ? 11 : 12,
        lineHeight: globalIndex % 4 === 0 ? 1.4 : 1.5,
        sectionSpacing: globalIndex % 3 === 0 ? 18 : 21,
        tags: [
          family.category,
          family.photo ? "photo" : "no-photo",
          layout,
          family.atsFriendly ? "ats-friendly" : "visual",
          industries[globalIndex % industries.length],
        ],
      };
    }),
);


export const TOTAL_TEMPLATE_COUNT = 50;

if (templateRegistry.length !== TOTAL_TEMPLATE_COUNT) {
  throw new Error(
    `Template registry integrity error: expected ${TOTAL_TEMPLATE_COUNT}, received ${templateRegistry.length}.`,
  );
}

export function getTemplate(key: string): TemplateDefinition {
  return templateRegistry.find((template) => template.key === key) ??
    templateRegistry[0];
}

export function applyTemplate(
  draft: StudioDraft,
  template: TemplateDefinition,
): StudioDraft {
  return {
    ...draft,
    templateKey: template.key,
    accent: template.accent,
    secondaryAccent: template.secondaryAccent,
    fontFamily: template.fontFamily,
    headingFont: template.headingFont,
    fontSize: template.fontSize,
    lineHeight: template.lineHeight,
    sectionSpacing: template.sectionSpacing,
    margin: template.margin,
    layout: template.layout,
    headerStyle: template.headerStyle,
    showPhoto: template.photo,
  };
}
