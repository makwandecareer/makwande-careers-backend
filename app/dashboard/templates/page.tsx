"use client";
import {useEffect,useMemo,useState} from "react";
import {useRouter} from "next/navigation";
import {RealTemplatePreview} from "@/components/templates/RealTemplatePreview";
import {realTemplates,type RealTemplate,type TemplateIndustry,type TemplateStyle} from "@/lib/real-template-catalog";
import {saveSelectedTemplate,SELECTED_TEMPLATE_KEY} from "@/lib/template-process";
type PhotoFilter="all"|"with-photo"|"without-photo"; type ColumnFilter="all"|1|2;
const colours=[["All",""],["Emerald","#006943"],["Navy","#1f4e79"],["Black","#2f2f2f"],["Burgundy","#7a3e3e"],["Purple","#5a4a78"],["Blue","#0f5f8f"],["Teal","#1d6d80"]];

export default function TemplatesPage(){
 const router=useRouter(); const [selected,setSelected]=useState("real-01"); const [photo,setPhoto]=useState<PhotoFilter>("all"); const [columns,setColumns]=useState<ColumnFilter>("all"); const [industry,setIndustry]=useState<TemplateIndustry|"all">("all"); const [style,setStyle]=useState<TemplateStyle|"all">("all"); const [colour,setColour]=useState(""); const [search,setSearch]=useState("");
 useEffect(()=>{
  const raw=localStorage.getItem(SELECTED_TEMPLATE_KEY);
  if(!raw)return;
  try{
   const saved=JSON.parse(raw) as RealTemplate;
   if(realTemplates.some(item=>item.key===saved.key))setSelected(saved.key);
  }catch{
   localStorage.removeItem(SELECTED_TEMPLATE_KEY);
  }
 },[]);
 const filtered=useMemo(()=>realTemplates.filter(t=>{const q=search.trim().toLowerCase();return(photo==="all"||t.photo===photo)&&(columns==="all"||t.columns===columns)&&(industry==="all"||t.industry===industry)&&(style==="all"||t.style===style)&&(!colour||t.palette.includes(colour))&&(!q||`${t.name} ${t.subtitle} ${t.industry} ${t.style}`.toLowerCase().includes(q))}),[photo,columns,industry,style,colour,search]);
 const choose=(t:RealTemplate)=>{setSelected(t.key);saveSelectedTemplate(t)}; const chosen=realTemplates.find(t=>t.key===selected)||realTemplates[0];
 return <div className="world-template-page">
  <header className="world-template-header"><span>World-class template library</span><h1>Choose from 50 real professional CV templates</h1><p>Every design uses real HTML, CSS, colours, typography and visible CV content.</p></header>
  <div className="world-template-layout">
   <aside className="world-filters">
    <div className="filter-title"><h3>Filters</h3><button onClick={()=>{setPhoto("all");setColumns("all");setIndustry("all");setStyle("all");setColour("");setSearch("")}}>Clear filters</button></div>
    <label className="filter-search"><span>Search</span><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search templates"/></label>
    <Filter title="Headshot"><Check label="With photo" checked={photo==="with-photo"} onClick={()=>setPhoto(photo==="with-photo"?"all":"with-photo")}/><Check label="Without photo" checked={photo==="without-photo"} onClick={()=>setPhoto(photo==="without-photo"?"all":"without-photo")}/></Filter>
    <Filter title="Columns"><Check label="1 column" checked={columns===1} onClick={()=>setColumns(columns===1?"all":1)}/><Check label="2 columns" checked={columns===2} onClick={()=>setColumns(columns===2?"all":2)}/></Filter>
    <Filter title="Industry"><select value={industry} onChange={e=>setIndustry(e.target.value as TemplateIndustry|"all")}><option value="all">All industries</option>{[...new Set(realTemplates.map(t=>t.industry))].map(x=><option key={x}>{x}</option>)}</select></Filter>
    <Filter title="Style"><select value={style} onChange={e=>setStyle(e.target.value as TemplateStyle|"all")}><option value="all">All styles</option>{[...new Set(realTemplates.map(t=>t.style))].map(x=><option key={x}>{x}</option>)}</select></Filter>
    <Filter title="Colour"><div className="filter-colours">{colours.map(([n,h])=><button key={n} title={n} className={colour===h?"active":""} style={{background:h||"#fff"}} onClick={()=>setColour(h)}/>)}</div></Filter>
    <div className="filter-result-count"><strong>{filtered.length}</strong><span>templates found</span></div>
   </aside>
   <main><div className="world-grid">{filtered.map(t=><article key={t.key} className={`world-template-card ${selected===t.key?"selected":""}`}>
    <button className="template-preview-button" onClick={()=>choose(t)}><RealTemplatePreview template={t}/>{t.recommended&&<span className="world-recommended">Recommended</span>}</button>
    <div className="world-template-info"><div><h3>{t.name}</h3><p>{t.subtitle}</p></div><div className="world-meta"><span>{t.photo==="with-photo"?"With photo":"No photo"}</span><span>{t.columns} column{t.columns===2?"s":""}</span><span>{t.ats}★ ATS</span></div><div className="world-palettes">{t.palette.map(c=><span key={c} style={{background:c}}/>)}</div><button className={selected===t.key?"selected-button":""} onClick={()=>choose(t)}>{selected===t.key?"Selected":"Use this template"}</button></div>
   </article>)}</div></main>
  </div>
  <footer className="world-template-footer"><button className="choose-later" onClick={()=>router.push("/dashboard/cv-studio")}>Choose later</button><div><span>Selected template</span><strong>{chosen.name}</strong></div><button className="use-template" onClick={()=>router.push("/dashboard/cv-studio")}>Use this template</button></footer>
 </div>
}
function Filter({title,children}:{title:string;children:React.ReactNode}){return <section className="filter-group"><h4>{title}</h4>{children}</section>}
function Check({label,checked,onClick}:{label:string;checked:boolean;onClick:()=>void}){return <button className={`filter-check ${checked?"active":""}`} onClick={onClick}><span/>{label}</button>}
