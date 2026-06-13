import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, ArrowUpDown, Loader2 } from "lucide-react";
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
import type { Application, Recommendation } from "@/lib/types";

function formatDate(value: string | null | undefined): string {
  return value ? new Date(value).toLocaleDateString() : "—";
}

type SortKey =
  | "ttb_id"
  | "permit_no"
  | "serial_number"
  | "created_at"
  | "finalized_at"
  | "fanciful_name"
  | "brand_name"
  | "origin_code"
  | "class_type_code"
  | "status";

type SortDirection = "asc" | "desc";

type RecommendationByAppId = Map<number, Recommendation | null | undefined>;

function getStatusValue(application: Application, recommendationByAppId: RecommendationByAppId): string {
  if (application.finalized_at) {
    return application.recommendation ?? application.status;
  }
  const batchRecommendation = recommendationByAppId.get(application.id);
  if (batchRecommendation !== undefined) {
    return batchRecommendation ?? application.status;
  }
  return application.status;
}

function getSortValue(
  application: Application,
  key: SortKey,
  recommendationByAppId: RecommendationByAppId
): string | number {
  switch (key) {
    case "created_at":
    case "finalized_at":
      return application[key] ? new Date(application[key] as string).getTime() : 0;
    case "status":
      return getStatusValue(application, recommendationByAppId);
    default:
      return application[key] ?? "";
  }
}

function compareValues(a: string | number, b: string | number): number {
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b));
}

// 12.2: "Filter by applicant" now matches any column — TTB ID, permit/serial
// numbers, brand/fanciful names, origin/class-type, status, and dates.
function matchesFilter(application: Application, filter: string, recommendationByAppId: RecommendationByAppId): boolean {
  if (!filter) return true;
  const needle = filter.toLowerCase();
  const values = [
    application.ttb_id,
    application.permit_no,
    application.serial_number,
    application.fanciful_name,
    application.brand_name,
    application.origin_code,
    application.class_type_code,
    application.applicant_name,
    getStatusValue(application, recommendationByAppId),
    formatDate(application.created_at),
    formatDate(application.finalized_at),
  ];
  return values.some((value) => value?.toLowerCase().includes(needle));
}

interface SortableHeadProps {
  label: string;
  sortKey: SortKey;
  activeSortKey: SortKey | null;
  direction: SortDirection;
  onSort: (key: SortKey) => void;
}

function SortableHead({ label, sortKey, activeSortKey, direction, onSort }: SortableHeadProps) {
  const isActive = activeSortKey === sortKey;
  const Icon = isActive ? (direction === "asc" ? ArrowUp : ArrowDown) : ArrowUpDown;
  return (
    <TableHead>
      <button
        type="button"
        className="flex items-center gap-1 text-muted-foreground hover:text-foreground"
        onClick={() => onSort(sortKey)}
      >
        {label}
        <Icon className="h-3.5 w-3.5" />
      </button>
    </TableHead>
  );
}

export function DashboardPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [applicantFilter, setApplicantFilter] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [activeBatchId, setActiveBatchId] = useState<number | null>(null);
  const [sortKey, setSortKey] = useState<SortKey | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  const applicationsQuery = useQuery({
    queryKey: ["applications"],
    queryFn: () => applicationsApi.list(),
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
  const batchStatus = batchStatusQuery.data;
  const isBatchProcessing = activeBatchId !== null && batchStatus?.status !== "COMPLETE";
  const recommendationByAppId: RecommendationByAppId = new Map(
    (batchStatus?.applications ?? []).map((entry) => [entry.id, entry.recommendation])
  );

  const filteredApplications = applications.filter((application) =>
    matchesFilter(application, applicantFilter.trim(), recommendationByAppId)
  );
  const sortedApplications = sortKey
    ? [...filteredApplications].sort((a, b) => {
        const result = compareValues(
          getSortValue(a, sortKey, recommendationByAppId),
          getSortValue(b, sortKey, recommendationByAppId)
        );
        return sortDirection === "asc" ? result : -result;
      })
    : filteredApplications;

  const allSelected = sortedApplications.length > 0 && sortedApplications.every((app) => selectedIds.has(app.id));
  const someSelected = sortedApplications.some((app) => selectedIds.has(app.id));

  const toggleAll = (checked: boolean) => {
    setSelectedIds(checked ? new Set(sortedApplications.map((app) => app.id)) : new Set());
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

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDirection((direction) => (direction === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
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
            placeholder="Filter applications..."
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

        {/* 15.5: batch status failed to load — let the agent retry or dismiss rather than
            leaving the batch silently stuck in a "processing" state. */}
        {batchStatusQuery.isError && (
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
            <span>
              Failed to load status for batch #{activeBatchId}. The batch may still be processing in the
              background.
            </span>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => batchStatusQuery.refetch()}>
                Retry
              </Button>
              <Button variant="outline" size="sm" onClick={() => setActiveBatchId(null)}>
                Dismiss
              </Button>
            </div>
          </div>
        )}

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
            No applications yet. Use &quot;New Upload&quot; to submit one.
          </p>
        )}
        {applicationsQuery.data && applications.length > 0 && sortedApplications.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No applications found for &quot;{applicantFilter.trim()}&quot;.
          </p>
        )}
        {sortedApplications.length > 0 && (
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
                <SortableHead label="TTB ID" sortKey="ttb_id" activeSortKey={sortKey} direction={sortDirection} onSort={handleSort} />
                <SortableHead label="Permit No." sortKey="permit_no" activeSortKey={sortKey} direction={sortDirection} onSort={handleSort} />
                <SortableHead label="Serial Number" sortKey="serial_number" activeSortKey={sortKey} direction={sortDirection} onSort={handleSort} />
                <SortableHead label="Upload Date" sortKey="created_at" activeSortKey={sortKey} direction={sortDirection} onSort={handleSort} />
                <SortableHead label="Completed Date" sortKey="finalized_at" activeSortKey={sortKey} direction={sortDirection} onSort={handleSort} />
                <SortableHead label="Fanciful Name" sortKey="fanciful_name" activeSortKey={sortKey} direction={sortDirection} onSort={handleSort} />
                <SortableHead label="Brand Name" sortKey="brand_name" activeSortKey={sortKey} direction={sortDirection} onSort={handleSort} />
                <SortableHead label="Origin Desc" sortKey="origin_code" activeSortKey={sortKey} direction={sortDirection} onSort={handleSort} />
                <SortableHead label="Class/Type Desc" sortKey="class_type_code" activeSortKey={sortKey} direction={sortDirection} onSort={handleSort} />
                <SortableHead label="Status" sortKey="status" activeSortKey={sortKey} direction={sortDirection} onSort={handleSort} />
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedApplications.map((application) => (
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
                  <TableCell>{application.ttb_id ?? "—"}</TableCell>
                  <TableCell>{application.permit_no ?? "—"}</TableCell>
                  <TableCell>{application.serial_number ?? "—"}</TableCell>
                  <TableCell>{formatDate(application.created_at)}</TableCell>
                  <TableCell>{formatDate(application.finalized_at)}</TableCell>
                  <TableCell>{application.fanciful_name ?? "—"}</TableCell>
                  <TableCell>{application.brand_name ?? "—"}</TableCell>
                  <TableCell>{application.origin_code ?? "—"}</TableCell>
                  <TableCell>{application.class_type_code ?? "—"}</TableCell>
                  <TableCell>
                    {application.finalized_at ? (
                      <RecommendationBadge recommendation={application.recommendation} />
                    ) : recommendationByAppId.has(application.id) ? (
                      <RecommendationBadge recommendation={recommendationByAppId.get(application.id)} />
                    ) : (
                      application.status
                    )}
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
