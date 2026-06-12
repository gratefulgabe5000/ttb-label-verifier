import { useEffect, useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { applicationsApi } from "@/lib/api-client";
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
    return <p className="text-sm text-muted-foreground">No label images uploaded for this application.</p>;
  }
  if (error) {
    return <p className="text-sm text-destructive">{error}</p>;
  }

  const activeId = activeLabelImageId ?? labelImages[0].id;

  return (
    <Tabs
      value={String(activeId)}
      onValueChange={(value) => onActiveLabelImageChange(Number(value))}
    >
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
      {labelImages.map((image, index) => {
        const overlays = labelParameters
          .filter((param) => param.label_image_id === image.id)
          .map((param) => ({ param, bbox: parseBbox(param.bbox_json) }))
          .filter((entry): entry is { param: LabelParameter; bbox: LabelBbox } => entry.bbox !== null);
        const size = imageSizes[image.id];

        return (
          <TabsContent key={image.id} value={String(image.id)}>
            {imageUrls[image.id] ? (
              <div className="relative">
                <img
                  src={imageUrls[image.id]}
                  alt={image.label_type ?? `Label image ${index + 1}`}
                  className="block w-full rounded-md border"
                  onLoad={(event) => {
                    const { naturalWidth, naturalHeight } = event.currentTarget;
                    setImageSizes((sizes) => ({
                      ...sizes,
                      [image.id]: { width: naturalWidth, height: naturalHeight },
                    }));
                  }}
                />
                {size && overlays.length > 0 && (
                  <svg
                    className="pointer-events-none absolute inset-0 h-full w-full"
                    viewBox={`0 0 ${size.width} ${size.height}`}
                    preserveAspectRatio="none"
                  >
                    {overlays.map(({ param, bbox }) => {
                      const isHovered = hoveredField === param.field_name;
                      return (
                        <g
                          key={param.id}
                          className="pointer-events-auto cursor-pointer"
                          onMouseEnter={() => onHoverField(param.field_name)}
                          onMouseLeave={() => onHoverField(null)}
                        >
                          <rect
                            x={bbox.x}
                            y={bbox.y}
                            width={bbox.w}
                            height={bbox.h}
                            fill={isHovered ? "rgba(37, 99, 235, 0.25)" : "rgba(250, 204, 21, 0.2)"}
                            stroke={isHovered ? "#2563eb" : "#d97706"}
                            strokeWidth={isHovered ? 2.5 : 1.5}
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
            ) : (
              <p className="text-sm text-muted-foreground">Loading image...</p>
            )}
          </TabsContent>
        );
      })}
    </Tabs>
  );
}
