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
import { applicationsApi } from "@/lib/api-client";

export function DashboardPage() {
  const applicationsQuery = useQuery({
    queryKey: ["applications"],
    queryFn: () => applicationsApi.list(),
    retry: false,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pending Applications</CardTitle>
      </CardHeader>
      <CardContent>
        {applicationsQuery.isLoading && (
          <p className="text-sm text-muted-foreground">Loading applications...</p>
        )}
        {applicationsQuery.isError && (
          <p className="text-sm text-muted-foreground">
            Application list is not available yet (WBS 4.0+).
          </p>
        )}
        {applicationsQuery.data && (
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
