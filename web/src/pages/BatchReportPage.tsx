import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { RecommendationBadge } from "@/components/applications/RecommendationBadge";
import { applicationsApi, batchApi } from "@/lib/api-client";
import { downloadCsv, toCsv } from "@/lib/csv";
import { cn } from "@/lib/utils";
import type { Application, BatchReport } from "@/lib/types";

export function BatchReportPage() {
  const { id } = useParams<{ id: string }>();
  const batchId = Number(id);

  const reportQuery = useQuery({
    queryKey: ["batch-report", batchId],
    queryFn: () => batchApi.report(batchId),
    enabled: Number.isFinite(batchId),
    retry: false,
    refetchInterval: (query) => (query.state.data?.status === "COMPLETE" ? false : 1000),
  });

  const applicationsQuery = useQuery({
    queryKey: ["applications"],
    queryFn: () => applicationsApi.list(),
    retry: false,
  });

  if (reportQuery.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading batch report...</p>;
  }
  if (reportQuery.isError || !reportQuery.data) {
    return <p className="text-sm text-destructive">Failed to load batch report.</p>;
  }

  const report = reportQuery.data;
  const applicationsById = new Map((applicationsQuery.data ?? []).map((app) => [app.id, app]));

  const handleExportCsv = () => downloadCsv(`batch-${report.id}-report.csv`, toCsv(buildCsvRows(report, applicationsById)));

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Batch #{report.id} Report</CardTitle>
          <div className="flex items-center gap-2 print:hidden">
            <Button variant="outline" size="sm" onClick={handleExportCsv}>
              Export CSV
            </Button>
            <Button variant="outline" size="sm" onClick={() => window.print()}>
              Print / Save as PDF
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {report.status !== "COMPLETE" ? (
            <div className="flex items-center gap-2 text-sm">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>
                Processing: {report.completed} of {report.total} complete...
              </span>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <SummaryStat label="Total Processed" value={report.total} />
              <SummaryStat
                label="Approved"
                value={report.approved_count}
                className="text-emerald-700 dark:text-emerald-400"
              />
              <SummaryStat label="Denied" value={report.denied_count} className="text-destructive" />
              <SummaryStat
                label="Exemption Review"
                value={report.exemption_count}
                className="text-amber-700 dark:text-amber-400"
              />
            </div>
          )}

          <p className="text-sm">
            <span className="font-medium">Most common failure type: </span>
            {report.most_common_failure ?? "None"}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Application Results</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Applicant</TableHead>
                <TableHead>Serial #</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Result</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {report.applications.map((entry) => {
                const application = applicationsById.get(entry.id);
                return (
                  <TableRow key={entry.id}>
                    <TableCell className="font-medium">
                      <Link to={`/applications/${entry.id}`} className="hover:underline">
                        {application?.applicant_name ?? `Application #${entry.id}`}
                      </Link>
                    </TableCell>
                    <TableCell>{application?.serial_number ?? "—"}</TableCell>
                    <TableCell>{entry.status}</TableCell>
                    <TableCell>
                      <RecommendationBadge recommendation={entry.recommendation} />
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function SummaryStat({ label, value, className }: { label: string; value: number; className?: string }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={cn("text-2xl font-semibold", className)}>{value}</p>
    </div>
  );
}

// 14.3/FR-096: one row per application, plus a header row.
function buildCsvRows(report: BatchReport, applicationsById: Map<number, Application>): string[][] {
  return [
    ["Application ID", "Applicant", "Serial Number", "Status", "Recommendation"],
    ...report.applications.map((entry) => {
      const application = applicationsById.get(entry.id);
      return [
        String(entry.id),
        application?.applicant_name ?? "",
        application?.serial_number ?? "",
        entry.status,
        entry.recommendation ?? "",
      ];
    }),
  ];
}
