import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FormPdfPanel } from "@/components/applications/FormPdfPanel";
import { LabelImagesPanel } from "@/components/applications/LabelImagesPanel";
import { applicationsApi } from "@/lib/api-client";

export function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const applicationId = Number(id);

  const applicationQuery = useQuery({
    queryKey: ["application", applicationId],
    queryFn: () => applicationsApi.get(applicationId),
    enabled: Number.isFinite(applicationId),
    retry: false,
  });

  if (applicationQuery.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading application...</p>;
  }
  if (applicationQuery.isError || !applicationQuery.data) {
    return <p className="text-sm text-destructive">Failed to load application.</p>;
  }

  const application = applicationQuery.data;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>
            Application #{application.id}
            {application.applicant_name ? ` — ${application.applicant_name}` : ""}
          </CardTitle>
          <Badge variant="outline">{application.status}</Badge>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Application Form</CardTitle>
          </CardHeader>
          <CardContent>
            <FormPdfPanel
              key={application.id}
              applicationId={application.id}
              formParameters={application.form_parameters}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Label Images</CardTitle>
          </CardHeader>
          <CardContent>
            <LabelImagesPanel
              key={application.id}
              applicationId={application.id}
              labelImages={application.label_images}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
