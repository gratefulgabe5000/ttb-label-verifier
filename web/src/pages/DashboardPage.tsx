import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
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
import { applicationsApi } from "@/lib/api-client";

export function DashboardPage() {
  const navigate = useNavigate();
  const [applicantFilter, setApplicantFilter] = useState("");
  const [debouncedFilter, setDebouncedFilter] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    const handle = setTimeout(() => setDebouncedFilter(applicantFilter.trim()), 300);
    return () => clearTimeout(handle);
  }, [applicantFilter]);

  const applicationsQuery = useQuery({
    queryKey: ["applications", { applicantName: debouncedFilter }],
    queryFn: () => applicationsApi.list({ applicantName: debouncedFilter || undefined }),
    retry: false,
  });

  const applications = applicationsQuery.data ?? [];
  const allSelected = applications.length > 0 && applications.every((app) => selectedIds.has(app.id));
  const someSelected = applications.some((app) => selectedIds.has(app.id));

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
              <Button variant="outline" size="sm" onClick={() => setSelectedIds(new Set())}>
                Clear
              </Button>
            </div>
          )}
        </div>

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
                  <TableCell>{application.status}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
