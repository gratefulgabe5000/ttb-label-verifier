import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { UploadApplicationDialog } from "@/components/applications/UploadApplicationDialog";
import { RecommendationBadge } from "@/components/applications/RecommendationBadge";
import { ApiError, applicationsApi, batchApi } from "@/lib/api-client";

export function DashboardPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [applicantFilter, setApplicantFilter] = useState("");
  const [debouncedFilter, setDebouncedFilter] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [activeBatchId, setActiveBatchId] = useState<number | null>(null);

  useEffect(() => {
    const handle = setTimeout(() => setDebouncedFilter(applicantFilter.trim()), 300);
    return () => clearTimeout(handle);
  }, [applicantFilter]);

  const applicationsQuery = useQuery({
    queryKey: ["applications", { applicantName: debouncedFilter }],
    queryFn: () => applicationsApi.list({ applicantName: debouncedFilter || undefined }),
    retry: false,
  });

  // 12.4: poll batch status (against 9.5's GET /batch/{id}/status) until complete.
  const batchStatusQuery = useQuery({
    queryKey: ["batch-status", activeBatchId],
    queryFn: () => batchApi.status(activeBatchId as number),
    enabled: activeBatchId !== null,
    retry: false,
    refetchInterval: (query) => (query.state.data?.status === "COMPLETE" ? false : 1000),
  });

  const processMutation = useMutation({
    mutationFn: (applicationIds: number[]) => batchApi.process({ application_ids: applicationIds }),
    onSuccess: (batch) => {
      setActiveBatchId(batch.id);
      queryClient.setQueryData(["batch-status", batch.id], batch);
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      setSelectedIds(new Set());
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Failed to process batch.");
    },
  });

  const applications = applicationsQuery.data ?? [];
  const allSelected = applications.length > 0 && applications.every((app) => selectedIds.has(app.id));
  const someSelected = applications.some((app) => selectedIds.has(app.id));
  const batchStatus = batchStatusQuery.data;
  const isBatchProcessing = activeBatchId !== null && batchStatus?.status !== "COMPLETE";
  const recommendationByAppId = new Map(
    (batchStatus?.applications ?? []).map((entry) => [entry.id, entry.recommendation])
  );

  const toggleAll = (checked: boolean) => {
    setSelectedIds(checked ? new Set(applications.map((app) => app.id)) : new Set());
  };

  const toggleOne = (id: number, checked: boolean) => {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (checked) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Pending Applications</CardTitle>
        <UploadApplicationDialog />
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-3">
          <Input
            placeholder="Filter by applicant..."
            value={applicantFilter}
            onChange={(event) => setApplicantFilter(event.target.value)}
            className="max-w-xs"
          />
          {selectedIds.size > 0 && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>{selectedIds.size} selected</span>
              <Button
                size="sm"
                onClick={() => processMutation.mutate(Array.from(selectedIds))}
                disabled={processMutation.isPending || isBatchProcessing}
              >
                {processMutation.isPending || isBatchProcessing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : null}
                Process Selected
              </Button>
              <Button variant="outline" size="sm" onClick={() => setSelectedIds(new Set())}>
                Clear
              </Button>
            </div>
          )}
        </div>

        {/* 12.6: batch summary header — progress while processing, counts once complete */}
        {batchStatus && (
          <div className="rounded-md border bg-muted/50 p-3 text-sm">
            {batchStatus.status === "COMPLETE" ? (
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
                <span className="font-medium">
                  Batch #{batchStatus.id}: {batchStatus.completed} of {batchStatus.total} processed
                </span>
                <span className="text-emerald-700 dark:text-emerald-400">
                  {batchStatus.approved_count} approved
                </span>
                <span className="text-destructive">{batchStatus.denied_count} denied</span>
                <span className="text-amber-700 dark:text-amber-400">
                  {batchStatus.exemption_count} exemption review
                </span>
                <Button variant="outline" size="sm" onClick={() => navigate(`/batches/${batchStatus.id}`)}>
                  View Report
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>
                  Processing batch #{batchStatus.id}: {batchStatus.completed} of {batchStatus.total}...
                </span>
              </div>
            )}
          </div>
        )}

        {applicationsQuery.isLoading && (
          <p className="text-sm text-muted-foreground">Loading applications...</p>
        )}
        {applicationsQuery.isError && (
          <p className="text-sm text-destructive">Failed to load applications. Please try again.</p>
        )}
        {applicationsQuery.data && applications.length === 0 && (
          <p className="text-sm text-muted-foreground">
            {debouncedFilter
              ? `No applications found for "${debouncedFilter}".`
              : 'No applications yet. Use "New Upload" to submit one.'}
          </p>
        )}
        {applications.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">
                  <Checkbox
                    checked={allSelected}
                    indeterminate={someSelected && !allSelected}
                    onCheckedChange={toggleAll}
                    aria-label="Select all applications"
                  />
                </TableHead>
                <TableHead>Applicant</TableHead>
                <TableHead>Serial #</TableHead>
                <TableHead>Product Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Result</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {applications.map((application) => (
                <TableRow
                  key={application.id}
                  className="cursor-pointer"
                  onClick={() => navigate(`/applications/${application.id}`)}
                >
                  <TableCell onClick={(event) => event.stopPropagation()}>
                    <Checkbox
                      checked={selectedIds.has(application.id)}
                      onCheckedChange={(checked) => toggleOne(application.id, checked)}
                      aria-label={`Select application ${application.id}`}
                    />
                  </TableCell>
                  <TableCell>{application.applicant_name}</TableCell>
                  <TableCell>{application.serial_number}</TableCell>
                  <TableCell>{application.product_type}</TableCell>
                  <TableCell>
                    {application.finalized_at ? (
                      <RecommendationBadge recommendation={application.recommendation} />
                    ) : (
                      application.status
                    )}
                  </TableCell>
                  <TableCell>
                    <RecommendationBadge recommendation={recommendationByAppId.get(application.id)} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
