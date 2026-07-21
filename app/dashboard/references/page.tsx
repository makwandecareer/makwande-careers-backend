"use client";
import { ResourceManager } from "@/components/resource-manager";

export default function Page() {
  return <ResourceManager title="References" description="Add and manage your references records." endpoint="/api/references" fields={[{"key": "full_name", "label": "Full name", "type": "text", "required": true}, {"key": "relationship", "label": "Relationship", "type": "text", "required": false}, {"key": "company", "label": "Company", "type": "text", "required": false}, {"key": "email", "label": "Email", "type": "text", "required": false}, {"key": "phone", "label": "Phone", "type": "text", "required": false}]} />;
}
