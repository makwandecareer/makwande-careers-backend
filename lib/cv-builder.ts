export type CVTemplateKey = "ats-standard" | "graduate" | "professional" | "executive" | "harvard" | "modern" | "minimal" | "engineering" | "technology" | "finance" | "academic" | "healthcare";
export type CVSectionKey = "summary" | "experience" | "education" | "skills" | "projects" | "certifications" | "languages" | "references";
export type CVSettings = { paperSize:"a4"|"letter"; margin:"narrow"|"standard"|"wide"; font:"Arial"|"Helvetica"|"Calibri"|"Cambria"|"Garamond"; fontSize:number; lineHeight:number; accent:string; showProjects:boolean; showCertifications:boolean; showLanguages:boolean; showReferences:boolean; };
export const defaultSectionOrder: CVSectionKey[]=["summary","experience","education","skills","projects","certifications","languages","references"];
export const defaultCVSettings:CVSettings={paperSize:"a4",margin:"standard",font:"Arial",fontSize:12,lineHeight:1.5,accent:"#006943",showProjects:true,showCertifications:true,showLanguages:true,showReferences:true};
export const templates=[
["ats-standard","ATS Standard"],["graduate","Graduate"],["professional","Professional"],["executive","Executive"],["harvard","Harvard"],["modern","Modern"],["minimal","Minimal"],["engineering","Engineering"],["technology","Technology"],["finance","Finance"],["academic","Academic"],["healthcare","Healthcare"]
] as const;
