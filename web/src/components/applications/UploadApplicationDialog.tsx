import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, X } from "lucide-react";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, applicationsApi } from "@/lib/api-client";
import type { LabelType } from "@/lib/types";

const LABEL_TYPES: LabelType[] = ["brand", "back", "neck", "other"];

interface LabelImageEntry {
  id: number;
  file: File | null;
  labelType: LabelType;
}

let nextEntryId = 0;

function emptyEntry(): LabelImageEntry {
  nextEntryId += 1;
  return { id: nextEntryId, file: null, labelType: "brand" };
}

export function UploadApplicationDialog() {
  const [open, setOpen] = useState(false);
  const [applicantName, setApplicantName] = useState("");
  const [serialNumber, setSerialNumber] = useState("");
  const [formFile, setFormFile] = useState<File | null>(null);
  const [labelImages, setLabelImages] = useState<LabelImageEntry[]>([emptyEntry()]);
  const queryClient = useQueryClient();

  const reset = () => {
    setApplicantName("");
    setSerialNumber("");
    setFormFile(null);
    setLabelImages([emptyEntry()]);
  };

  const uploadMutation = useMutation({
    mutationFn: applicationsApi.upload,
    onSuccess: (application) => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      toast.success(`Application #${application.id} uploaded.`);
      reset();
      setOpen(false);
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Upload failed.");
    },
  });

  const handleOpenChange = (next: boolean) => {
    if (!next) {
      reset();
      uploadMutation.reset();
    }
    setOpen(next);
  };

  const updateLabelImage = (id: number, patch: Partial<LabelImageEntry>) => {
    setLabelImages((entries) => entries.map((entry) => (entry.id === id ? { ...entry, ...patch } : entry)));
  };

  const removeLabelImage = (id: number) => {
    setLabelImages((entries) => entries.filter((entry) => entry.id !== id));
  };

  const handleSubmit = () => {
    if (!formFile) return;

    const formData = new FormData();
    formData.append("form_file", formFile);
    if (applicantName.trim()) formData.append("applicant_name", applicantName.trim());
    if (serialNumber.trim()) formData.append("serial_number", serialNumber.trim());

    for (const entry of labelImages) {
      if (!entry.file) continue;
      formData.append("label_images", entry.file);
      formData.append("label_types", entry.labelType);
    }

    uploadMutation.mutate(formData);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger render={<Button>New Upload</Button>} />
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>New Application</DialogTitle>
          <DialogDescription>
            Upload an application form (PDF) and any label images for review.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="applicant-name">Applicant name</Label>
            <Input
              id="applicant-name"
              value={applicantName}
              onChange={(event) => setApplicantName(event.target.value)}
              placeholder="Stoll & Wolfe Distillery"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="serial-number">Serial number</Label>
            <Input
              id="serial-number"
              value={serialNumber}
              onChange={(event) => setSerialNumber(event.target.value)}
              placeholder="25304001000123"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="form-file">Application form (PDF)</Label>
            <Input
              id="form-file"
              type="file"
              accept="application/pdf"
              onChange={(event) => setFormFile(event.target.files?.[0] ?? null)}
            />
          </div>

          <div className="space-y-2">
            <Label>Label images</Label>
            {labelImages.map((entry) => (
              <div key={entry.id} className="flex items-center gap-2">
                <Input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="flex-1"
                  onChange={(event) => updateLabelImage(entry.id, { file: event.target.files?.[0] ?? null })}
                />
                <select
                  className="h-8 rounded-lg border border-input bg-transparent px-2 text-sm"
                  value={entry.labelType}
                  onChange={(event) => updateLabelImage(entry.id, { labelType: event.target.value as LabelType })}
                >
                  {LABEL_TYPES.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
                <Button type="button" variant="outline" size="icon" onClick={() => removeLabelImage(entry.id)}>
                  <X />
                </Button>
              </div>
            ))}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setLabelImages((entries) => [...entries, emptyEntry()])}
            >
              <Plus />
              Add another label image
            </Button>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!formFile || uploadMutation.isPending}>
            {uploadMutation.isPending ? <Loader2 className="animate-spin" /> : "Upload"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
