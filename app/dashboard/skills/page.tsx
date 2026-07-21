"use client";
import { ResourceManager } from "@/components/resource-manager";

export default function Page() {
  return <ResourceManager title="Skills" description="Add and manage your skills records." endpoint="/api/skills" fields={[{"key": "name", "label": "Skill", "type": "text", "required": true}, {"key": "proficiency", "label": "Proficiency", "type": "text", "required": false}, {"key": "years_experience", "label": "Years of experience", "type": "number", "required": false}]} />;
}
