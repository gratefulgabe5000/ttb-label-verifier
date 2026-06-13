// Human-readable labels for `comparisons.field_name` values, mirroring
// `FIELD_LABELS` in app/services/determination_engine.py (FR-085, FR-097).

export const FIELD_LABELS: Record<string, string> = {
  brand_name: "Brand Name",
  government_warning: "Government Warning statement",
  government_warning_text: "Government Warning — statement text (27 CFR § 16.21)",
  government_warning_caps: "Government Warning — header in ALL CAPS",
  government_warning_bold: "Government Warning — header in bold type",
  for_sale_in_state: 'Type 14b "for sale in [STATE]" statement',
  country_of_origin: "Country of Origin",
  fanciful_name: "Fanciful Name",
  product_type: "Product/Class-Type designation",
  applicant_name: "Applicant Name",
  applicant_address: "Applicant Address",
  grape_varietals: "Grape Varietals",
  wine_appellation: "Wine Appellation",
  alcohol_content: "Alcohol Content (ABV)",
  net_contents: "Net Contents",
  label_field_of_vision: "Brand Name / Class-Type / ABV — same field of vision",
};

export function fieldLabel(fieldName: string): string {
  return FIELD_LABELS[fieldName] ?? fieldName;
}
