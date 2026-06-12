import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ApiError, debugApi } from "@/lib/api-client";
import type { ApplicationDetail, ExtractionMethod, FormParameter, LabelParameter } from "@/lib/types";

interface DebugParametersDialogProps {
  application: ApplicationDetail;
}

const EXTRACTION_METHOD_LABEL: Record<ExtractionMethod, string> = {
  acroform: "Tier 1: AcroForm",
  pdftext: "Tier 2: PDF text",
  ai_vision: "Tier 3: Claude Vision",
};

function formatConfidence(confidence: number | null): string {
  return confidence === null ? "—" : `${Math.round(confidence * 100)}%`;
}

function formatBbox(bboxJson: string | null): string {
  if (!bboxJson) return "—";
  try {
    const box = JSON.parse(bboxJson) as Record<string, number>;
    return Object.entries(box)
      .map(([key, value]) => `${key}:${value}`)
      .join(" ");
  } catch {
    return bboxJson;
  }
}

function FormParametersTable({ params }: { params: FormParameter[] }) {
  if (params.length === 0) {
    return <p className="text-sm text-muted-foreground">No form parameters extracted yet.</p>;
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Field</TableHead>
          <TableHead>Value</TableHead>
          <TableHead>Confidence</TableHead>
          <TableHead>Source</TableHead>
          <TableHead>Location hint</TableHead>
          <TableHead>BBox</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {params.map((param) => (
          <TableRow key={param.id}>
            <TableCell className="font-medium whitespace-nowrap">{param.field_name}</TableCell>
            <TableCell className="max-w-xs whitespace-pre-wrap break-words">{param.field_value ?? "—"}</TableCell>
            <TableCell className="whitespace-nowrap">{formatConfidence(param.confidence)}</TableCell>
            <TableCell className="whitespace-nowrap">
              {param.extraction_method ? (
                <Badge variant="outline">{EXTRACTION_METHOD_LABEL[param.extraction_method]}</Badge>
              ) : (
                <span className="text-muted-foreground">unresolved</span>
              )}
            </TableCell>
            <TableCell className="text-muted-foreground">{param.location_hint ?? "—"}</TableCell>
            <TableCell className="text-muted-foreground whitespace-nowrap">{formatBbox(param.bbox_json)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function LabelParametersTable({
  params,
  labelImages,
}: {
  params: LabelParameter[];
  labelImages: ApplicationDetail["label_images"];
}) {
  if (params.length === 0) {
    return <p className="text-sm text-muted-foreground">No label parameters extracted yet.</p>;
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Image</TableHead>
          <TableHead>Field</TableHead>
          <TableHead>Value</TableHead>
          <TableHead>Confidence</TableHead>
          <TableHead>Location hint</TableHead>
          <TableHead>BBox (OCR)</TableHead>
          <TableHead>Header ratio</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {params.map((param) => {
          const image = labelImages.find((img) => img.id === param.label_image_id);
          return (
            <TableRow key={param.id}>
              <TableCell className="whitespace-nowrap">{image?.label_type ?? `#${param.label_image_id}`}</TableCell>
              <TableCell className="font-medium whitespace-nowrap">{param.field_name}</TableCell>
              <TableCell className="max-w-xs whitespace-pre-wrap break-words">{param.field_value ?? "—"}</TableCell>
              <TableCell className="whitespace-nowrap">{formatConfidence(param.confidence)}</TableCell>
              <TableCell className="text-muted-foreground">{param.location_hint ?? "—"}</TableCell>
              <TableCell className="text-muted-foreground whitespace-nowrap">{formatBbox(param.bbox_json)}</TableCell>
              <TableCell className="text-muted-foreground whitespace-nowrap">
                {param.header_height_ratio ?? "—"}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

export function DebugParametersDialog({ application }: DebugParametersDialogProps) {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();

  const extractMutation = useMutation({
    mutationFn: () => debugApi.runExtraction(application.id),
    onSuccess: (updated) => {
      queryClient.setQueryData(["application", application.id], updated);
      toast.success("Stage 3 + Stage 4 extraction complete.");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Extraction failed.");
    },
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button variant="outline">Debug Parameters</Button>} />
      <DialogContent className="sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>Extracted Parameters (debug)</DialogTitle>
          <DialogDescription>
            Raw form_parameters (Stage 3) and label_parameters (Stage 4) for this application,
            including each value&apos;s extraction source — for verifying the AI/OCR pipeline.
            Temporary tool, removed once WBS 9.0 wires the real pipeline.
          </DialogDescription>
        </DialogHeader>

        <div className="max-h-[65vh] overflow-y-auto">
          <Tabs defaultValue="form">
            <TabsList>
              <TabsTrigger value="form">Form (Stage 3) — {application.form_parameters.length}</TabsTrigger>
              <TabsTrigger value="label">Label (Stage 4) — {application.label_parameters.length}</TabsTrigger>
            </TabsList>
            <TabsContent value="form">
              <FormParametersTable params={application.form_parameters} />
            </TabsContent>
            <TabsContent value="label">
              <LabelParametersTable params={application.label_parameters} labelImages={application.label_images} />
            </TabsContent>
          </Tabs>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Close
          </Button>
          <Button onClick={() => extractMutation.mutate()} disabled={extractMutation.isPending}>
            {extractMutation.isPending ? <Loader2 className="animate-spin" /> : "Run Stage 3 + 4 Extraction"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
