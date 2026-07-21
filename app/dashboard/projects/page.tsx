"use client";
import { ResourceManager } from "@/components/resource-manager";

export default function Page() {
  return <ResourceManager title="Projects" description="Add and manage your projects records." endpoint="/api/projects" fields={[{"key": "name", "label": "Project name", "type": "text", "required": true}, {"key": "description", "label": "Description", "type": "textarea", "required": false}, {"key": "project_url", "label": "Project URL", "type": "text", "required": false}, {"key": "start_date", "label": "Start date", "type": "date", "required": false}, {"key": "end_date", "label": "End date", "type": "date", "required": false}]} />;
}
