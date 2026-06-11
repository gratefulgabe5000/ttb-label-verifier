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
import { UploadApplicationDialog } from "@/components/applications/UploadApplicationDialog";
import { applicationsApi } from "@/lib/api-client";

export function DashboardPage() {
  const applicationsQuery = useQuery({
    queryKey: ["applications"],
    queryFn: () => applicationsApi.list(),
    retry: false,
  });

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Pending Applications</CardTitle>
        <UploadApplicationDialog />
      </CardHeader>
      <CardContent>
        {applicationsQuery.isLoading && (
          <p className="text-sm text-muted-foreground">Loading applications...</p>
        )}
        {applicationsQuery.isError && (
          <p className="text-sm text-destructive">Failed to load applications. Please try again.</p>
        )}
        {applicationsQuery.data && applicationsQuery.data.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No applications yet. Use "New Upload" to submit one.
          </p>
        )}
        {applicationsQuery.data && applicationsQuery.data.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Applicant</TableHead>
                <TableHead>Serial #</TableHead>
                <TableHead>Product Type</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {applicationsQuery.data.map((application) => (
                <TableRow key={application.id}>
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
