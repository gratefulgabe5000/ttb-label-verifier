import { useCallback, useEffect, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, RotateCw } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useContainerWidth } from "@/hooks/useContainerWidth";
import { useWheelZoom } from "@/hooks/useWheelZoom";
import { ApiError, applicationsApi } from "@/lib/api-client";
import { comparisonFieldFor, isFieldHighlighted } from "@/lib/field-mappings";
import { cn } from "@/lib/utils";
import type { FormParameter } from "@/lib/types";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url
).toString();

interface FormBbox {
  page?: number;
  x: number;
  y: number;
  w: number;
  h: number;
}

interface PageSize {
  width: number;
  height: number;
  originalWidth: number;
  originalHeight: number;
}

interface FormPdfPanelProps {
  applicationId: number;
  formParameters: FormParameter[];
  hoveredField: string | null;
  onHoverField: (field: string | null) => void;
}

function parseBbox(bboxJson: string | null): FormBbox | null {
  if (!bboxJson) return null;
  try {
    return JSON.parse(bboxJson) as FormBbox;
  } catch {
    return null;
  }
}

export function FormPdfPanel({ applicationId, formParameters, hoveredField, onHoverField }: FormPdfPanelProps) {
  const [blob, setBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [numPages, setNumPages] = useState(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [pageSize, setPageSize] = useState<PageSize | null>(null);
  const { zoom, containerRef } = useWheelZoom();
  const containerWidth = useContainerWidth(containerRef, 520);
  const queryClient = useQueryClient();

  const reprocessMutation = useMutation({
    mutationFn: () => applicationsApi.reprocessForm(applicationId),
    onSuccess: (updated) => {
      queryClient.setQueryData(["application", applicationId], updated);
      queryClient.invalidateQueries({ queryKey: ["comparisons", applicationId] });
      toast.success("Form reprocessed.");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Failed to reprocess form.");
    },
  });

  const handleDocumentLoadSuccess = useCallback((pdf: { numPages: number }) => setNumPages(pdf.numPages), []);
  const handlePageLoadSuccess = useCallback(
    (page: { width: number; height: number; originalWidth: number; originalHeight: number }) =>
      setPageSize({
        width: page.width,
        height: page.height,
        originalWidth: page.originalWidth,
        originalHeight: page.originalHeight,
      }),
    []
  );

  useEffect(() => {
    let cancelled = false;

    applicationsApi
      .getFormBlob(applicationId)
      .then((result) => {
        if (!cancelled) setBlob(result);
      })
      .catch(() => {
        if (!cancelled) setError("Failed to load application form.");
      });

    return () => {
      cancelled = true;
    };
  }, [applicationId]);

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Application Form</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">{error}</p>
        </CardContent>
      </Card>
    );
  }
  if (!blob) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Application Form</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Loading form...</p>
        </CardContent>
      </Card>
    );
  }

  const overlays = formParameters
    .map((param) => ({ param, bbox: parseBbox(param.bbox_json) }))
    .filter((entry): entry is { param: FormParameter; bbox: FormBbox } => entry.bbox !== null)
    .filter((entry) => (entry.bbox.page ?? 0) === pageNumber - 1);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Application Form</CardTitle>
        <CardAction>
          <Button
            variant="secondary"
            size="icon"
            className="rounded-full"
            aria-label="Reprocess form"
            onClick={() => reprocessMutation.mutate()}
            disabled={reprocessMutation.isPending}
          >
            <RotateCw className={cn("size-4", reprocessMutation.isPending && "animate-spin")} />
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent className="space-y-2">
        <div ref={containerRef} className="overflow-auto">
          <Document
            file={blob}
            onLoadSuccess={handleDocumentLoadSuccess}
            onLoadError={() => setError("Failed to render application form.")}
            loading={<p className="text-sm text-muted-foreground">Rendering form...</p>}
          >
            <div className="relative inline-block">
              <Page
                pageNumber={pageNumber}
                width={Math.round(containerWidth * zoom)}
                renderTextLayer={false}
                renderAnnotationLayer={false}
                onLoadSuccess={handlePageLoadSuccess}
              />
              {pageSize && overlays.length > 0 && (
                <svg
                  className="pointer-events-none absolute left-0 top-0"
                  width={pageSize.width}
                  height={pageSize.height}
                  viewBox={`0 0 ${pageSize.originalWidth} ${pageSize.originalHeight}`}
                >
                  {overlays.map(({ param, bbox }) => {
                    const isHovered = isFieldHighlighted(hoveredField, param.field_name, "form");
                    return (
                      <g
                        key={param.id}
                        className="pointer-events-auto cursor-pointer"
                        onMouseEnter={() => onHoverField(comparisonFieldFor(param.field_name))}
                        onMouseLeave={() => onHoverField(null)}
                      >
                        <rect
                          x={bbox.x}
                          y={bbox.y}
                          width={bbox.w}
                          height={bbox.h}
                          fill={isHovered ? "rgba(37, 99, 235, 0.25)" : "transparent"}
                          stroke={isHovered ? "#2563eb" : "none"}
                          strokeWidth={isHovered ? 2.5 : 0}
                        />
                        <title>
                          {param.field_name}: {param.field_value ?? "(empty)"}
                        </title>
                      </g>
                    );
                  })}
                </svg>
              )}
            </div>
          </Document>
        </div>

        {formParameters.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No extracted form fields yet — annotations will appear here once form extraction has run.
          </p>
        )}

        {numPages > 1 && (
          <div className="flex items-center justify-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={pageNumber <= 1}
              onClick={() => setPageNumber((current) => current - 1)}
            >
              <ChevronLeft />
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {pageNumber} of {numPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={pageNumber >= numPages}
              onClick={() => setPageNumber((current) => current + 1)}
            >
              Next
              <ChevronRight />
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
