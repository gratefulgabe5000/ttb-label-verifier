import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FormPdfPanel } from "@/components/applications/FormPdfPanel";
import { LabelImagesPanel } from "@/components/applications/LabelImagesPanel";
import { ParameterResultsTable } from "@/components/applications/ParameterResultsTable";
import { ResultsSidebar } from "@/components/applications/ResultsSidebar";
import { applicationsApi } from "@/lib/api-client";

export function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const applicationId = Number(id);

  const [hoveredField, setHoveredField] = useState<string | null>(null);
  const [pinnedField, setPinnedField] = useState<string | null>(null);
  const [activeLabelImageId, setActiveLabelImageId] = useState<number | null>(null);

  // 13.6/13.7/13.11: hovering wins while active, but clicking a results row
  // pins the cross-highlight so it persists after the mouse leaves (see
  // ResultsSidebar's onSelectField).
  const activeField = hoveredField ?? pinnedField;

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

  // 13.11: when a field is hovered or pinned (from the form, a label
  // annotation, or the results sidebar), auto-switch the label image tab to
  // the one it references.
  const activeComparison = comparisons.find(
    (c) => c.field_name === activeField && c.label_image_id !== null
  );
  const effectiveLabelImageId = activeComparison?.label_image_id ?? activeLabelImageId;

  if (applicationQuery.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading application...</p>;
  }
  if (applicationQuery.isError || !applicationQuery.data) {
    return <p className="text-sm text-destructive">Failed to load application.</p>;
  }

  const application = applicationQuery.data;

  const togglePin = (field: string) =>
    setPinnedField((current) => (current === field ? null : field));

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_1fr_320px]">
        <FormPdfPanel
          key={application.id}
          applicationId={application.id}
          formParameters={application.form_parameters}
          hoveredField={activeField}
          onHoverField={setHoveredField}
        />

        <LabelImagesPanel
          key={application.id}
          applicationId={application.id}
          labelImages={application.label_images}
          labelParameters={application.label_parameters}
          hoveredField={activeField}
          onHoverField={setHoveredField}
          activeLabelImageId={effectiveLabelImageId}
          onActiveLabelImageChange={setActiveLabelImageId}
        />

        <ResultsSidebar
          application={application}
          comparisons={comparisons}
          isLoading={comparisonsQuery.isLoading}
          hoveredField={activeField}
          onHoverField={setHoveredField}
          pinnedField={pinnedField}
          onSelectField={togglePin}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Parameter Results</CardTitle>
        </CardHeader>
        <CardContent>
          <ParameterResultsTable
            comparisons={comparisons}
            isLoading={comparisonsQuery.isLoading}
            hoveredField={activeField}
            onHoverField={setHoveredField}
            pinnedField={pinnedField}
            onSelectField={togglePin}
          />
        </CardContent>
      </Card>
    </div>
  );
}
