"use client";
import { ResourceManager } from "@/components/resource-manager";

export default function Page() {
  return <ResourceManager title="Education" description="Add and manage your education records." endpoint="/api/education" fields={[{"key": "institution", "label": "Institution", "type": "text", "required": true}, {"key": "qualification", "label": "Qualification", "type": "text", "required": true}, {"key": "field_of_study", "label": "Field of study", "type": "text", "required": false}, {"key": "start_date", "label": "Start date", "type": "date", "required": false}, {"key": "end_date", "label": "End date", "type": "date", "required": false}, {"key": "is_current", "label": "Currently studying", "type": "checkbox", "required": false}, {"key": "description", "label": "Description", "type": "textarea", "required": false}]} />;
}
