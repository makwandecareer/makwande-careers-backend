"use client";
import { ResourceManager } from "@/components/resource-manager";

export default function Page() {
  return <ResourceManager title="Certifications" description="Add and manage your certifications records." endpoint="/api/certifications" fields={[{"key": "name", "label": "Certification name", "type": "text", "required": true}, {"key": "issuer", "label": "Issuer", "type": "text", "required": false}, {"key": "issue_date", "label": "Issue date", "type": "date", "required": false}, {"key": "expiry_date", "label": "Expiry date", "type": "date", "required": false}, {"key": "credential_id", "label": "Credential ID", "type": "text", "required": false}, {"key": "credential_url", "label": "Credential URL", "type": "text", "required": false}]} />;
}
