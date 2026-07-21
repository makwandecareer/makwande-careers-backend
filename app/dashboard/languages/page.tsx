"use client";
import { ResourceManager } from "@/components/resource-manager";

export default function Page() {
  return <ResourceManager title="Languages" description="Add and manage your languages records." endpoint="/api/languages" fields={[{"key": "name", "label": "Language", "type": "text", "required": true}, {"key": "proficiency", "label": "Proficiency", "type": "text", "required": false}]} />;
}
