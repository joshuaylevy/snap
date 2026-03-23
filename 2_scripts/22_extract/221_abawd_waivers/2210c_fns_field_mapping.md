# ABAWD Prompt Alignment to FNS Waiver Response Form

This note documents how the extraction schema aligns to the FNS Waiver Response form and where derived/non-form fields are kept for analysis.

## Canonical FNS fields (request_level)

| FNS item | Canonical key |
|---|---|
| Waiver Serial Number | `waiver_serial_number` |
| Type of Request | `type_of_request` |
| Primary regulation citation | `primary_regulation_citation` |
| State | `state` |
| Region | `fns_region` |
| Description of proposed alternative procedures | `alt_procedures_desc` |
| Action and reason for approval or denial | `action_reason_approval_denial` |
| Regulatory or legislative basis for action | `reg_leg_action_basis` |
| Conditions and reasons | `conditions_and_reasons` |
| Information required for extension | `info_required_for_extension` |
| Expiration date | `expiration_date` |
| Limitation on regional office approval of like requests | `limits_on_regional_office_approvals` |
| Quality control procedures | `quality_control_procedures` |
| Date of national office action | `date_national_office_action` |
| Date of State agency request | `date_state_request` |
| Date of regional office transmittal of request | `date_ro_transmittal_request` |
| Date of regional office transmittal of response to State agency | `date_ro_transmittal_response` |
| Actual implementation date | `implementation_date_actual` |

## Mapping from prior keys to aligned keys

| Previous key | New/aligned key | Notes |
|---|---|---|
| `application_date` | `date_state_request` | Better matches FNS field name with shorter key. |
| `waiver_serial_number` | `waiver_serial_number` | Unchanged. |
| `response_date` | `date_national_office_action` and `response_date` | Keep `response_date` as extra letter metadata. |
| `region` | `fns_region` | Renamed to make FNS context explicit. |
| `expiration_date_text` | `expiration_date` | Shortened key while retaining same concept. |
| `rule_cited` | `criterion_code_normalized` | Group-level derived field. |
| `rule_other_explanation` | `criterion_other_explanation` | Group-level derived field. |
| `status` | `group_action` | Group-level normalized action. |
| `waiver_expiry_date` | `waiver_expiry_date` | Unchanged. |
| `waiver_duration` | `waiver_duration_text` | Clarifies that value is text. |
| `applied_waiver_duration` | `applied_waiver_duration_text` | Clarifies that value is text. |

## Group-level schema details (as defined in prompt)

| Group key | Type | Notes |
|---|---|---|
| `geographic_units` | list[object] | Each object contains `name` and `area_type`. |
| `group_action` | string or null | Expected values: `approved`, `denied`, or null. |
| `criteria_summary_text` | string or null | Concise rationale summary for the group. |
| `criterion_code_normalized` | string or null | One of `percent_10`, `percent_20`, `LSA`, `trigger`, `federal_waiver`, `other`, or null. |
| `criterion_other_explanation` | string or null | Populated only when `criterion_code_normalized = other`. |
| `national_unemployment_rate_cited` | object or null | Nested object with fields shown below. |
| `local_unemployment_time_window` | object or null | Nested object with fields shown below. |
| `waiver_effective_date` | date string or null | `YYYY-MM-DD` if determinable. |
| `waiver_expiry_date` | date string or null | `YYYY-MM-DD` if determinable. |
| `waiver_duration_text` | string or null | Verbatim or normalized duration text. |
| `applied_waiver_start_date` | date string or null | `YYYY-MM-DD` if explicitly requested by state. |
| `applied_waiver_end_date` | date string or null | `YYYY-MM-DD` if explicitly requested by state. |
| `applied_waiver_duration_text` | string or null | Applied-for duration text when separately stated. |

### Nested object: `national_unemployment_rate_cited`

- object shape:
  - `national_unemployment_rate_cited` (numeric or null)
  - `national_unemployment_rate_cited_text` (string or null)
  - `vintage_or_date_of_data_cited` (`YYYY-MM` or null)
- null when not applicable or not provided

### Nested object: `local_unemployment_time_window`

- object shape:
  - `local_unemployment_rate_cited` (numeric or null)
  - `local_unemployment_data_source_cited` (string or null)
  - `window_type` (`24_month_moving_average` \| `12_consecutive_months` \| `other` \| null)
  - `start_date` (`YYYY-MM` or null)
  - `end_date` (`YYYY-MM` or null)
  - `description` (string or null)
  - `vintage_or_date_of_data_cited` (`YYYY-MM` or null)
- null when not applicable or not provided

## Overlap and differences

- Overlap preserved: serial number, state, action/approval status, expiry/effective timing, and geographic group structure.
- Newly explicit from FNS form: `fns_region`, `reg_leg_action_basis`, `quality_control_procedures`, and the three transmittal/implementation dates.
- Non-form fields intentionally retained: `document_type`, `non_conforming_*`, `state_official_name`, `fns_official_name`, `fns_official_title`, normalized criterion/time-window fields, and detailed unemployment evidence objects for analysis.

## Structure validation

- `request_level` is appropriate for form-wide fields (serial, type, citation, state, fns_region, dates, QA/limitations).
- `groups` is appropriate for geography-specific approvals/denials and parsed criterion/date windows.
- Edge case: some letters only provide one request-level expiration statement for all geography; in that case, propagate group date fields only when clearly attributable, otherwise keep group values null and retain request-level value in `expiration_date`.
