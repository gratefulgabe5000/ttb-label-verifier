import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FormPdfPanel } from "@/components/applications/FormPdfPanel";
import { LabelImagesPanel } from "@/components/applications/LabelImagesPanel";
import { ParameterResultsTable } from "@/components/applications/ParameterResultsTable";
import { DeterminationPanel } from "@/components/applications/DeterminationPanel";
import { applicationsApi } from "@/lib/api-client";

export function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const applicationId = Number(id);

  const [hoveredField, setHoveredField] = useState<string | null>(null);
  const [activeLabelImageId, setActiveLabelImageId] = useState<number | null>(null);

  const applicationQuery = useQuery({
    queryKey: ["application", applicationId],
    queryFn: () => applicationsApi.get(applicationId),
    enabled: Number.isFinite(applicationId),
    retry: false,
  });

  const comparisonsQuery = useQuery({
    queryKey: ["comparisons", applicationId],
    queryFn: () => applicationsApi.comparisons(applicationId),
    enabled: Number.isFinite(applicationId),
    retry: false,
  });

  const comparisons = comparisonsQuery.data ?? [];

  // 13.11: when a field is hovered (from the form, a label annotation, or the
  // results table), auto-switch the label image tab to the one it references.
  const hoveredComparison = comparisons.find(
    (c) => c.field_name === hoveredField && c.label_image_id !== null
  );
  const effectiveLabelImageId = hoveredComparison?.label_image_id ?? activeLabelImageId;

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
          <div className="flex items-center gap-2">
            <Badge variant="outline">{application.status}</Badge>
            <DeterminationPanel application={application} />
          </div>
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
              hoveredField={hoveredField}
              onHoverField={setHoveredField}
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
              labelParameters={application.label_parameters}
              hoveredField={hoveredField}
              onHoverField={setHoveredField}
              activeLabelImageId={effectiveLabelImageId}
              onActiveLabelImageChange={setActiveLabelImageId}
            />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Parameter Results</CardTitle>
        </CardHeader>
        <CardContent>
          <ParameterResultsTable
            comparisons={comparisons}
            isLoading={comparisonsQuery.isLoading}
            applicationId={application.id}
            determinationId={application.determination?.id ?? null}
            finalized={application.determination?.finalized_at != null}
            hoveredField={hoveredField}
            onHoverField={setHoveredField}
          />
        </CardContent>
      </Card>
    </div>
  );
}
