// Reconciles the three field-name namespaces used across the Application
// Detail View (13.5/13.6/13.7/13.11): `comparisons[].field_name`,
// `form_parameters[].field_name`, and `label_parameters[].field_name`.
//
// Post-Session-22 these diverged for several fields (e.g. the Government
// Warning 3-way split, and bottler/importer vs. applicant_name on the
// label side), so cross-highlighting can no longer rely on exact string
// equality between the three sides. Each group below lists every name a
// single logical field is known by on each side; `===` is used wherever
// only one name has ever existed (e.g. brand_name).

export type FieldSide = "form" | "label" | "comparison";

export interface FieldGroup {
  comparisonFields: string[];
  formFields: string[];
  labelFields: string[];
}

export const FIELD_GROUPS: FieldGroup[] = [
  { comparisonFields: ["brand_name"], formFields: ["brand_name"], labelFields: ["brand_name"] },
  {
    comparisonFields: ["government_warning_text", "government_warning_caps", "government_warning_bold"],
    formFields: [],
    labelFields: ["government_warning"],
  },
  {
    comparisonFields: ["for_sale_in_state"],
    formFields: ["application_type"],
    labelFields: ["for_sale_in_state"],
  },
  {
    comparisonFields: ["country_of_origin"],
    formFields: ["source"],
    labelFields: ["country_of_origin"],
  },
  { comparisonFields: ["fanciful_name"], formFields: ["fanciful_name"], labelFields: ["fanciful_name"] },
  { comparisonFields: ["product_type"], formFields: ["product_type"], labelFields: ["class_type_designation"] },
  {
    comparisonFields: ["applicant_name"],
    formFields: ["applicant_name"],
    labelFields: ["bottler_name", "importer_name"],
  },
  {
    comparisonFields: ["applicant_address"],
    formFields: ["applicant_address"],
    labelFields: ["bottler_address", "importer_address"],
  },
  { comparisonFields: ["grape_varietals"], formFields: ["grape_varietals"], labelFields: ["grape_varietals"] },
  { comparisonFields: ["wine_appellation"], formFields: ["wine_appellation"], labelFields: ["wine_appellation"] },
  { comparisonFields: ["alcohol_content"], formFields: [], labelFields: ["alcohol_content"] },
  { comparisonFields: ["net_contents"], formFields: [], labelFields: ["net_contents"] },
];

export function groupForField(fieldName: string): FieldGroup | undefined {
  return FIELD_GROUPS.find(
    (group) =>
      group.comparisonFields.includes(fieldName) ||
      group.formFields.includes(fieldName) ||
      group.labelFields.includes(fieldName)
  );
}

// Normalizes a form- or label-side field name to the comparison-side field
// name used by `comparisons[].field_name` (and `ParameterResultsTable`/
// `effectiveLabelImageId`), so hovering a form or label annotation looks up
// the right table row and label image. Falls back to the input unchanged
// when the field isn't part of a known group (e.g. form-only fields with no
// comparison, such as `mailing_address`).
export function comparisonFieldFor(fieldName: string): string {
  return groupForField(fieldName)?.comparisonFields[0] ?? fieldName;
}

// True when `fieldName` (on `side`) should be highlighted because it's the
// same field as `activeField`, or belongs to the same field group (e.g. all
// three government_warning_* comparison rows highlight together when the
// label's single `government_warning` annotation is active).
export function isFieldHighlighted(activeField: string | null, fieldName: string, side: FieldSide): boolean {
  if (!activeField) return false;
  if (activeField === fieldName) return true;

  const group = groupForField(activeField);
  if (!group) return false;

  const fieldsOnSide = side === "form" ? group.formFields : side === "label" ? group.labelFields : group.comparisonFields;
  return fieldsOnSide.includes(fieldName);
}
