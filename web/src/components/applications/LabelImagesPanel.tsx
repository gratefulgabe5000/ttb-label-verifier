import { useEffect, useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { applicationsApi } from "@/lib/api-client";
import type { LabelImage } from "@/lib/types";

interface LabelImagesPanelProps {
  applicationId: number;
  labelImages: LabelImage[];
}

export function LabelImagesPanel({ applicationId, labelImages }: LabelImagesPanelProps) {
  const [imageUrls, setImageUrls] = useState<Record<number, string>>({});
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

  return (
    <Tabs defaultValue={String(labelImages[0].id)}>
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
      {labelImages.map((image, index) => (
        <TabsContent key={image.id} value={String(image.id)}>
          {imageUrls[image.id] ? (
            <img
              src={imageUrls[image.id]}
              alt={image.label_type ?? `Label image ${index + 1}`}
              className="max-h-[600px] w-full rounded-md border object-contain"
            />
          ) : (
            <p className="text-sm text-muted-foreground">Loading image...</p>
          )}
        </TabsContent>
      ))}
    </Tabs>
  );
}
