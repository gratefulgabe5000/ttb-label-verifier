import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { RotateCw } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useWheelZoom } from "@/hooks/useWheelZoom";
import { ApiError, applicationsApi } from "@/lib/api-client";
import { comparisonFieldFor, isFieldHighlighted } from "@/lib/field-mappings";
import { cn } from "@/lib/utils";
import type { LabelImage, LabelParameter } from "@/lib/types";

interface LabelBbox {
  x: number;
  y: number;
  w: number;
  h: number;
}

interface ImageSize {
  width: number;
  height: number;
}

interface LabelImagesPanelProps {
  applicationId: number;
  labelImages: LabelImage[];
  labelParameters: LabelParameter[];
  hoveredField: string | null;
  onHoverField: (field: string | null) => void;
  activeLabelImageId: number | null;
  onActiveLabelImageChange: (id: number) => void;
}

function parseBbox(bboxJson: string | null): LabelBbox | null {
  if (!bboxJson) return null;
  try {
    return JSON.parse(bboxJson) as LabelBbox;
  } catch {
    return null;
  }
}

interface LabelImageContentProps {
  image: LabelImage;
  index: number;
  imageUrl?: string;
  overlays: { param: LabelParameter; bbox: LabelBbox }[];
  size?: ImageSize;
  hoveredField: string | null;
  onHoverField: (field: string | null) => void;
  onImageLoad: (id: number, size: ImageSize) => void;
}

// One instance per tab; base-ui's TabsContent unmounts inactive panels, so
// each mounted instance gets its own wheel listener via useWheelZoom.
function LabelImageContent({
  image,
  index,
  imageUrl,
  overlays,
  size,
  hoveredField,
  onHoverField,
  onImageLoad,
}: LabelImageContentProps) {
  const { zoom, containerRef } = useWheelZoom();

  if (!imageUrl) {
    return <p className="text-sm text-muted-foreground">Loading image...</p>;
  }

  return (
    <div ref={containerRef} className="overflow-auto">
      <div className="relative" style={{ width: `${zoom * 100}%` }}>
        <img
          src={imageUrl}
          alt={image.label_type ?? `Label image ${index + 1}`}
          className="block w-full rounded-md border"
          onLoad={(event) => {
            const { naturalWidth, naturalHeight } = event.currentTarget;
            onImageLoad(image.id, { width: naturalWidth, height: naturalHeight });
          }}
        />
        {size && overlays.length > 0 && (
          <svg
            className="pointer-events-none absolute inset-0 h-full w-full"
            viewBox={`0 0 ${size.width} ${size.height}`}
            preserveAspectRatio="none"
          >
            {overlays.map(({ param, bbox }) => {
              const isHovered = isFieldHighlighted(hoveredField, param.field_name, "label");
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
                  {isHovered && (
                    <ellipse
                      cx={bbox.x + bbox.w / 2}
                      cy={bbox.y + bbox.h / 2}
                      rx={bbox.w / 2 + 10}
                      ry={bbox.h / 2 + 10}
                      fill="none"
                      stroke="#dc2626"
                      strokeWidth={3}
                      pointerEvents="none"
                    />
                  )}
                  <title>
                    {param.field_name}: {param.field_value ?? "(empty)"}
                  </title>
                </g>
              );
            })}
          </svg>
        )}
      </div>
    </div>
  );
}

export function LabelImagesPanel({
  applicationId,
  labelImages,
  labelParameters,
  hoveredField,
  onHoverField,
  activeLabelImageId,
  onActiveLabelImageChange,
}: LabelImagesPanelProps) {
  const [imageUrls, setImageUrls] = useState<Record<number, string>>({});
  const [imageSizes, setImageSizes] = useState<Record<number, ImageSize>>({});
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const reprocessMutation = useMutation({
    mutationFn: () => applicationsApi.reprocessLabel(applicationId),
    onSuccess: (updated) => {
      queryClient.setQueryData(["application", applicationId], updated);
      queryClient.invalidateQueries({ queryKey: ["comparisons", applicationId] });
      toast.success("Label reprocessed.");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Failed to reprocess label.");
    },
  });

  useEffect(() => {
    let cancelled = false;
    const urls: Record<number, string> = {};

    Promise.all(
      labelImages.map((image) =>
        applicationsApi.getLabelImageBlob(applicationId, image.id).then((blob) => {
          urls[image.id] = URL.createObjectURL(blob);
        })
      )
    )
      .then(() => {
        if (!cancelled) setImageUrls({ ...urls });
      })
      .catch(() => {
        if (!cancelled) setError("Failed to load label images.");
      });

    return () => {
      cancelled = true;
      Object.values(urls).forEach((url) => URL.revokeObjectURL(url));
    };
  }, [applicationId, labelImages]);

  if (labelImages.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Label Images</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No label images uploaded for this application.</p>
        </CardContent>
      </Card>
    );
  }
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Label Images</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">{error}</p>
        </CardContent>
      </Card>
    );
  }

  const activeId = activeLabelImageId ?? labelImages[0].id;

  return (
    <Tabs value={String(activeId)} onValueChange={(value) => onActiveLabelImageChange(Number(value))}>
      <Card>
        <CardHeader className="grid-cols-[1fr_auto_1fr] items-center">
          <CardTitle className="text-base">Label Images</CardTitle>
          <TabsList>
            {labelImages.map((image, index) => (
              <TabsTrigger key={image.id} value={String(image.id)} className="gap-2">
                {imageUrls[image.id] && (
                  <img src={imageUrls[image.id]} alt="" className="size-6 rounded object-cover" />
                )}
                {image.label_type ?? `Image ${index + 1}`}
              </TabsTrigger>
            ))}
          </TabsList>
          <Button
            variant="secondary"
            size="icon"
            className="justify-self-end rounded-full"
            aria-label="Reprocess label"
            onClick={() => reprocessMutation.mutate()}
            disabled={reprocessMutation.isPending}
          >
            <RotateCw className={cn("size-4", reprocessMutation.isPending && "animate-spin")} />
          </Button>
        </CardHeader>
        <CardContent>
          {labelImages.map((image, index) => {
            const overlays = labelParameters
              .filter((param) => param.label_image_id === image.id)
              .map((param) => ({ param, bbox: parseBbox(param.bbox_json) }))
              .filter((entry): entry is { param: LabelParameter; bbox: LabelBbox } => entry.bbox !== null);

            return (
              <TabsContent key={image.id} value={String(image.id)}>
                <LabelImageContent
                  image={image}
                  index={index}
                  imageUrl={imageUrls[image.id]}
                  overlays={overlays}
                  size={imageSizes[image.id]}
                  hoveredField={hoveredField}
                  onHoverField={onHoverField}
                  onImageLoad={(id, size) => setImageSizes((sizes) => ({ ...sizes, [id]: size }))}
                />
              </TabsContent>
            );
          })}
        </CardContent>
      </Card>
    </Tabs>
  );
}
