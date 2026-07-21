"use client";
import type {CSSProperties,ReactNode} from "react";
import type {RealTemplate} from "@/lib/real-template-catalog";

export function RealTemplatePreview({template}:{template:RealTemplate}) {
 const style={"--tpl-primary":template.palette[0],"--tpl-accent":template.palette[1],"--tpl-text":template.palette[2],fontFamily:template.font} as CSSProperties;
 return <div className={`real-cv-sheet layout-${template.layout}`} style={style}>
  <header className="real-cv-header">
   {template.photo==="with-photo"&&<div className="real-photo"><span/></div>}
   <div className="real-name-block"><h3>LERATO MASEKO</h3><p>Professional Title</p><small>lerato.maseko@email.com · +27 12 456 7890 · Pretoria, South Africa</small></div>
  </header>
  <div className="real-cv-body">
   <aside className="real-side">
    <Section title="Contact"><p>+27 12 456 7890</p><p>lerato.maseko@email.com</p><p>Pretoria, South Africa</p></Section>
    <Section title="Skills"><ul><li>Stakeholder management</li><li>Project coordination</li><li>Data analysis</li><li>Communication</li></ul></Section>
    <Section title="Education"><strong>National Diploma</strong><p>University of Pretoria</p><small>2017</small></Section>
   </aside>
   <main className="real-main">
    <Section title="Professional Summary"><p>Results-driven professional with strong experience in customer service, operations and stakeholder support. Recognised for reliability, communication and consistent delivery.</p></Section>
    <Section title="Work History"><Entry title="Sales Manager" company="Pretoria Government Services" date="2022 – Current"/><Entry title="Barista" company="Starbucks, Durban" date="2021 – 2022"/></Section>
    <Section title="Education"><Entry title="National Diploma: Business" company="University of Pretoria" date="2017"/></Section>
   </main>
  </div>
 </div>
}
function Section({title,children}:{title:string;children:ReactNode}){return <section className="real-section"><h4>{title}</h4>{children}</section>}
function Entry({title,company,date}:{title:string;company:string;date:string}){return <div className="real-entry"><div><strong>{title}</strong><p>{company}</p></div><small>{date}</small><ul><li>Delivered measurable improvements across daily operations.</li><li>Supported customers and stakeholders professionally.</li></ul></div>}
