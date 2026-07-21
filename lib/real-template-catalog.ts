export type TemplatePhoto = "with-photo" | "without-photo";
export type TemplateColumns = 1 | 2;
export type TemplateStyle = "classic" | "modern" | "executive" | "minimal" | "academic" | "technical" | "creative" | "corporate";
export type TemplateIndustry = "General" | "Engineering" | "Technology" | "Finance" | "Healthcare" | "Legal" | "Sales" | "Marketing" | "Education" | "Government" | "Graduate" | "Executive";
export type RealTemplate = {
  key: string; name: string; subtitle: string; photo: TemplatePhoto; columns: TemplateColumns;
  style: TemplateStyle; industry: TemplateIndustry; ats: 3 | 4 | 5; recommended?: boolean;
  layout: "sidebar-left" | "sidebar-right" | "top-band" | "centered" | "split-header" | "timeline" | "minimal-line" | "classic-serif";
  palette: string[]; font: string;
};

const names = [
"Apex Professional","Atlas Executive","Cambridge Classic","Oxford Formal","Harvard Prime","Geneva Corporate","Zurich Modern","London Executive","Berlin Minimal","Sydney Professional",
"Toronto Corporate","Singapore Elite","Tokyo Precision","Cape Town Professional","Pretoria Executive","Johannesburg Modern","Dublin Classic","Stockholm Minimal","Helsinki Clean","Monaco Prestige",
"Imperial Graduate","Stanford Academic","Princeton Formal","Kensington Executive","Westminster Classic","Sterling Corporate","Vanguard Professional","Titan Executive","Summit Modern","Zenith Elite",
"Momentum Professional","Legacy Classic","Prestige Executive","Nova Modern","Fusion Creative","Vertex Technical","Apollo Professional","Meridian Corporate","Regent Classic","Windsor Executive",
"Engineering Pro","Technology Prime","Finance Elite","Healthcare Professional","Legal Executive","Sales Impact","Marketing Modern","Graduate Launch","Government Standard","Academic Scholar"
];
const industries: TemplateIndustry[] = ["General","Executive","Education","General","Education","Finance","General","Executive","General","General","General","Executive","Technology","General","Government","General","General","General","General","Executive","Graduate","Education","Education","Executive","General","Finance","General","Executive","General","Executive","General","General","Executive","General","Marketing","Engineering","General","Finance","General","Executive","Engineering","Technology","Finance","Healthcare","Legal","Sales","Marketing","Graduate","Government","Education"];
const layouts: RealTemplate["layout"][] = ["sidebar-left","sidebar-left","classic-serif","classic-serif","centered","top-band","split-header","sidebar-right","minimal-line","top-band","sidebar-right","sidebar-left","split-header","sidebar-left","top-band","split-header","classic-serif","minimal-line","minimal-line","sidebar-right","sidebar-left","classic-serif","centered","top-band","classic-serif","top-band","split-header","sidebar-left","sidebar-right","top-band","timeline","classic-serif","sidebar-left","split-header","sidebar-right","sidebar-left","top-band","split-header","classic-serif","sidebar-right","sidebar-left","split-header","top-band","sidebar-left","classic-serif","timeline","split-header","sidebar-left","top-band","classic-serif"];
const styles: TemplateStyle[] = ["classic","executive","academic","classic","academic","corporate","modern","executive","minimal","modern","corporate","executive","technical","modern","executive","modern","classic","minimal","minimal","executive","academic","academic","academic","executive","classic","corporate","modern","executive","modern","executive","modern","classic","executive","modern","creative","technical","modern","corporate","classic","executive","technical","technical","corporate","corporate","classic","creative","modern","academic","corporate","academic"];
const palettes = [
["#f7d9d2","#9b4d3b","#3f3f46"],["#9fc9c2","#154c46","#2f2f2f"],["#ffffff","#2f2f2f","#777777"],["#ffffff","#1f2937","#a8a8a8"],["#ffffff","#0f172a","#888888"],
["#e7edf3","#1f4e79","#5a6f84"],["#dceff0","#1d6d80","#4f6470"],["#3f3f46","#0f766e","#f4f4f5"],["#ffffff","#111827","#777777"],["#eaf4ef","#006943","#5c6c62"],
["#e7ebf0","#334155","#64748b"],["#0f172a","#38bdf8","#f8fafc"],["#ffffff","#0f4c81","#90a8bb"],["#eef7f2","#006943","#53645a"],["#e9ecef","#495057","#212529"],
["#e8f1f7","#0f5f8f","#1f2937"],["#ffffff","#374151","#777777"],["#ffffff","#111827","#777777"],["#f7faf9","#2f5d62","#65756d"],["#f2eadf","#7a4b2a","#3e2f24"]
];

export const realTemplates: RealTemplate[] = names.map((name, i) => ({
 key:`real-${String(i+1).padStart(2,"0")}`, name, subtitle:`${styles[i][0].toUpperCase()+styles[i].slice(1)} ${industries[i]} CV`,
 photo: i%3===0 || i%7===0 ? "with-photo":"without-photo",
 columns: ["sidebar-left","sidebar-right","timeline"].includes(layouts[i]) ? 2:1,
 style:styles[i], industry:industries[i], ats:i%8===0?4:5, recommended:i<6, layout:layouts[i],
 palette:palettes[i%palettes.length], font:["Arial","Calibri","Cambria","Garamond","Georgia","Helvetica"][i%6]
}));
