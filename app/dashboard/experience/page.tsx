"use client";
import { ResourceManager } from "@/components/resource-manager";

export default function Page() {
  return <ResourceManager title="Experience" description="Add and manage your experience records." endpoint="/api/experience" fields={[{"key": "company", "label": "Company", "type": "text", "required": true}, {"key": "job_title", "label": "Job title", "type": "text", "required": true}, {"key": "location", "label": "Location", "type": "text", "required": false}, {"key": "start_date", "label": "Start date", "type": "date", "required": false}, {"key": "end_date", "label": "End date", "type": "date", "required": false}, {"key": "is_current", "label": "Current role", "type": "checkbox", "required": false}, {"key": "description", "label": "Description", "type": "textarea", "required": false}]} />;
}
