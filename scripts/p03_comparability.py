"""P03 guarded unit conversion, financial comparability, and YTD differencing.

Pure local operations. Results are derived/assessment records, never source facts.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, localcontext, ROUND_HALF_EVEN
from pathlib import Path

VERSION = "us-comparability-0.1.1"
UNKNOWN = {"unknown", "ambiguous", "not_yet_checked", "not_found", ""}
NUMBER = re.compile(r"^[+-]?\d+(?:\.\d+)?(?:[Ee][+-]?\d+)?$")


def numeric(value):
    if not isinstance(value, str) or not NUMBER.fullmatch(value):
        raise ValueError("numeric_value must be a finite Decimal string")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("invalid numeric_value") from exc
    if not result.is_finite():
        raise ValueError("numeric_value must be finite")
    return result


def decimal_text(value):
    return format(value, "f")


def known(value):
    return value is not None and not (isinstance(value, str) and value.lower() in UNKNOWN)


def claim_ref(claim):
    return claim.get("claim_id") or claim.get("observation_id") or claim.get("occurrence_id")


def normalized(record):
    # P02 layered records and already normalized P01 observations are accepted.
    if "normalized" not in record:
        n = dict(record)
        n.setdefault("definition_version", n.get("metric_definition_version"))
        return n
    n = dict(record["normalized"])
    n.setdefault("claim_id", record.get("claim_id"))
    temporal = n.get("temporal", {})
    period = temporal.get("reference_period", {})
    for key in ["period_start", "period_end", "period_kind", "duration_days", "period_basis"]:
        if key in period:
            n.setdefault("period_duration_days" if key == "duration_days" else key, period[key])
    for key in ["published_at", "published_date", "available_at"]:
        n.setdefault(key, temporal.get(key))
    context = n.get("financial_context", {})
    n.setdefault("balance_or_flow", context.get("balance_or_flow"))
    n.setdefault("statement_type", context.get("statement_type"))
    n.setdefault("definition_version", n.get("metric_definition_version"))
    return n


def normalize_amount(value, input_unit, currency, rules_csv):
    output = {"calculation_status": "incompatible_inputs", "output": None,
              "output_unit": None, "currency": currency, "input_value": value,
              "input_unit": input_unit, "rule_version": VERSION}
    if value is None:
        return dict(output, calculation_status="insufficient_inputs", reasons=["value_missing"])
    try:
        amount = numeric(value)
    except ValueError as exc:
        return dict(output, calculation_status="invalid_input", reasons=[str(exc)])
    if not known(currency) or not known(input_unit):
        return dict(output, reasons=["currency_or_unit_unknown"])
    with Path(rules_csv).open(encoding="utf-8-sig", newline="") as f:
        rules = list(csv.DictReader(f))
    candidates = [r for r in rules if r.get("input_unit") == input_unit
                  and r.get("rule_kind") == "scale"
                  and r.get("currency_condition") in {currency, "currency=" + currency, "same_currency", "any_same_currency"}]
    if len(candidates) != 1:
        return dict(output, reasons=["no_unambiguous_scale_rule"])
    rule = candidates[0]
    try:
        multiplier = numeric(rule["multiplier"])
        if multiplier <= 0:
            raise ValueError("scale_multiplier_must_be_positive")
        if rule.get("rounding") != "ROUND_HALF_EVEN":
            raise ValueError("unsupported_rounding_policy")
        precision = int(rule.get("precision", "28"))
        if not 1 <= precision <= 100:
            raise ValueError("unsupported_precision")
        with localcontext() as ctx:
            ctx.prec = precision
            ctx.rounding = ROUND_HALF_EVEN
            result = amount * multiplier
    except (ValueError, KeyError, InvalidOperation) as exc:
        return dict(output, calculation_status="invalid_rule", reasons=[str(exc)])
    return dict(output, calculation_status="computed", output=decimal_text(result),
                output_unit=rule["output_unit"], multiplier=rule["multiplier"],
                rule_id=rule["rule_id"], source_rule_version=rule["version"], reasons=[])


def period_data(claim):
    flow = claim.get("balance_or_flow")
    start, end = claim.get("period_start"), claim.get("period_end")
    if flow == "balance":
        instant = claim.get("as_of_date") or end
        if not instant:
            return None, "balance_date_missing"
        try:
            return {"start": None, "end": date.fromisoformat(instant), "days": None}, None
        except (TypeError, ValueError):
            return None, "invalid_balance_date"
    if flow != "flow" or not start or not end:
        return None, "flow_period_missing"
    try:
        a, b = date.fromisoformat(start), date.fromisoformat(end)
        days = (b - a).days + 1
        if days <= 0:
            return None, "period_reversed"
        provided = claim.get("period_duration_days")
        if provided is None or int(provided) != days:
            return None, "period_duration_missing_or_inconsistent"
        return {"start": a, "end": b, "days": days}, None
    except (TypeError, ValueError):
        return None, "invalid_period"


def _single_availability_errors(claim, as_of):
    if as_of is None:
        return []
    available = claim.get("available_at") or claim.get("published_at") or claim.get("published_date")
    if not available:
        return ["publication_availability_unknown"]
    try:
        if len(as_of) == 10:
            if date.fromisoformat(available[:10]) > date.fromisoformat(as_of):
                return ["future_information_after_cutoff"]
        else:
            if len(available) == 10:
                # A date cannot establish intraday availability on that date.
                if date.fromisoformat(available) >= date.fromisoformat(as_of[:10]):
                    return ["date_only_intraday_availability_unresolved"]
            else:
                cutoff = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
                moment = datetime.fromisoformat(available.replace("Z", "+00:00"))
                if cutoff.tzinfo is None or moment.tzinfo is None:
                    return ["timezone_missing"]
                if moment > cutoff:
                    return ["future_information_after_cutoff"]
    except (TypeError, ValueError):
        return ["invalid_publication_or_cutoff"]
    return []


def availability_errors(claim, as_of):
    errors = _single_availability_errors(claim, as_of)
    if as_of is None:
        return errors
    for dependency in claim.get("availability_dependencies", []):
        if not isinstance(dependency, dict):
            errors.append("invalid_availability_dependency")
            continue
        item = dict(dependency)
        if not (item.get("available_at") or item.get("published_at") or item.get("published_date")) and item.get("availability_basis") == "observed_conservative":
            item["available_at"] = item.get("observed_at")
        errors += ["dependency:" + e for e in _single_availability_errors(item, as_of)]
    return errors


def base_checks(new, prior):
    checks, failures, unknowns = {}, [], []
    required = ["company_id", "scope_id", "metric_id", "definition_version",
                "accounting_basis", "consolidation", "canonical_unit", "currency",
                "value_kind", "balance_or_flow", "period_basis", "period_kind", "modality", "scale"]
    for key in required:
        a, b = new.get(key), prior.get(key)
        if not known(a) or not known(b):
            checks[key + "_match"] = None
            unknowns.append(key + "_unknown")
        else:
            checks[key + "_match"] = a == b
            if a != b:
                failures.append(key + "_mismatch")
    if any(known(c.get("scale")) and str(c["scale"]) != "1" for c in [new, prior]):
        failures.append("explicit_base_unit_normalization_required")
    a, b = new.get("product_id"), prior.get("product_id")
    company_scope = all(c.get("scope_level") in {"company", "consolidated"}
                        or str(c.get("scope_id", "")).endswith("-CONSOLIDATED") for c in [new, prior])
    explicit_product_na = all(c.get("product_id_missing_reason") == "not_applicable" for c in [new, prior])
    checks["product_match"] = a == b if known(a) and known(b) else (True if a is None and b is None and (company_scope or explicit_product_na) else None)
    if checks["product_match"] is False:
        failures.append("product_mismatch")
    if checks["product_match"] is None:
        unknowns.append("product_unknown_for_noncompany_scope")
    for key in ["adjustment_definition", "denominator", "sign_convention"]:
        a, b = new.get(key), prior.get(key)
        checks[key + "_match"] = a == b
        if a != b:
            failures.append(key + "_mismatch")
    if any(str(c.get("accounting_basis", "")).lower().replace("-", "_").startswith("non_gaap") and not known(c.get("adjustment_definition")) for c in [new, prior]):
        unknowns.append("non_gaap_definition_missing")
    if any(c.get("value_kind") in {"share", "rate", "relative_change"} and not known(c.get("denominator")) for c in [new, prior]):
        unknowns.append("ratio_denominator_unknown")
    return checks, failures, unknowns


def compare_claims(new_record, prior_record, comparison_kind="same_period", as_of=None):
    new, prior = normalized(new_record), normalized(prior_record)
    checks, failures, unknowns = base_checks(new, prior)
    result = {"new_claim_id": claim_ref(new), "prior_claim_id": claim_ref(prior),
              "comparison_basis": comparison_kind, "checks": checks, "decision": "unknown",
              "reasons": [], "rule_version": VERSION,
              "delta": None, "relative_delta": None, "relative_delta_missing_reason": None,
              "calculation_layer": "derived"}
    result["delta_unit"] = "percent_point" if new.get("canonical_unit") == "percent" else new.get("canonical_unit")
    for c in [new, prior]:
        unknowns += availability_errors(c, as_of)
    np, ne = period_data(new)
    pp, pe = period_data(prior)
    if ne or pe:
        unknowns += [e for e in [ne, pe] if e]
        checks["period_match"] = None
    elif comparison_kind == "same_period":
        checks["period_match"] = np == pp
        checks["period_length_match"] = np["days"] == pp["days"]
        if not checks["period_match"]:
            failures.append("reference_period_mismatch")
        for key in ["fiscal_year", "fiscal_quarter"]:
            if known(new.get(key)) and known(prior.get(key)) and new[key] != prior[key]:
                failures.append(key + "_conflicts_with_same_period")
    elif comparison_kind == "yoy":
        endpoints = ["end"] if new.get("balance_or_flow") == "balance" else ["start", "end"]
        matched = all(np[k].year == pp[k].year + 1 and (np[k].month, np[k].day) == (pp[k].month, pp[k].day) for k in endpoints)
        length_match = np["days"] == pp["days"]
        # Calendar-anniversary periods explicitly explain a leap-day difference.
        calendar_anniversary = matched and np["days"] is not None and abs(np["days"] - pp["days"]) <= 1
        checks["period_match"] = matched
        checks["period_length_match"] = length_match
        checks["calendar_anniversary_length_guard"] = calendar_anniversary
        if not matched or not (length_match or calendar_anniversary):
            failures.append("yoy_actual_period_not_aligned")
        if known(new.get("fiscal_year")) and known(prior.get("fiscal_year")):
            try:
                if int(new["fiscal_year"]) != int(prior["fiscal_year"]) + 1:
                    failures.append("fiscal_year_labels_not_yoy")
            except (TypeError, ValueError):
                unknowns.append("fiscal_year_label_not_numeric")
        if known(new.get("fiscal_quarter")) and known(prior.get("fiscal_quarter")) and new["fiscal_quarter"] != prior["fiscal_quarter"]:
            failures.append("fiscal_quarter_labels_not_yoy")
    else:
        failures.append("unsupported_comparison_kind")
    amounts = []
    for c in [new, prior]:
        if c.get("numeric_value") is None:
            unknowns.append("numeric_value_missing:" + str(c.get("missing_reason", "reason_not_recorded")))
        else:
            try:
                amounts.append(numeric(c["numeric_value"]))
            except ValueError:
                failures.append("numeric_value_invalid")
    result["reasons"] = list(dict.fromkeys(failures + unknowns))
    result["decision"] = "not_comparable" if failures else ("unknown" if unknowns else "comparable")
    if result["decision"] == "comparable" and len(amounts) == 2:
        with localcontext() as ctx:
            ctx.prec = 28
            ctx.rounding = ROUND_HALF_EVEN
            result["delta"] = decimal_text(amounts[0] - amounts[1])
            if amounts[1] == 0:
                result["relative_delta_missing_reason"] = "zero_prior_denominator"
            else:
                result["relative_delta"] = decimal_text((amounts[0] - amounts[1]) / abs(amounts[1]))
                result["relative_delta_definition"] = "(new-prior)/abs(prior); fraction, not percent"
    return result


def difference_ytd(longer_record, shorter_record):
    longer, shorter = normalized(longer_record), normalized(shorter_record)
    checks, failures, unknowns = base_checks(longer, shorter)
    result = {"calculation_status": "incompatible_inputs", "output": None,
              "input_refs": [claim_ref(longer), claim_ref(shorter)], "formula_id": "compatible_ytd_difference",
              "rule_version": VERSION, "checks": checks, "layer": "derived"}
    if not all(result["input_refs"]):
        unknowns.append("input_record_identity_missing")
    if longer.get("balance_or_flow") != "flow" or shorter.get("balance_or_flow") != "flow":
        failures.append("ytd_difference_requires_flows")
    if longer.get("period_kind") != "ytd" or shorter.get("period_kind") != "ytd":
        failures.append("explicit_ytd_period_kind_required")
    if any(c.get("value_kind") != "point" or c.get("canonical_unit") in {"percent", "percent_point", "percentage_point", "fraction", "ratio"} for c in [longer, shorter]):
        failures.append("ytd_difference_requires_additive_point_amounts")
    if any(c.get("aggregation_behavior") != "additive_flow" for c in [longer, shorter]):
        failures.append("additive_flow_registry_definition_required")
    if known(longer.get("fiscal_year")) and known(shorter.get("fiscal_year")) and longer["fiscal_year"] != shorter["fiscal_year"]:
        failures.append("fiscal_year_mismatch")
    lp, le = period_data(longer)
    sp, se = period_data(shorter)
    if le or se:
        unknowns += [e for e in [le, se] if e]
    elif lp["start"] != sp["start"] or not sp["end"] < lp["end"] or not lp["start"] <= sp["end"]:
        failures.append("shorter_ytd_not_prefix_of_longer")
    if failures or unknowns:
        return dict(result, reasons=list(dict.fromkeys(failures + unknowns)),
                    calculation_status="incompatible_inputs" if failures else "insufficient_inputs")
    try:
        with localcontext() as ctx:
            ctx.prec = 28
            ctx.rounding = ROUND_HALF_EVEN
            output = numeric(longer.get("numeric_value")) - numeric(shorter.get("numeric_value"))
    except ValueError:
        return dict(result, calculation_status="insufficient_inputs", reasons=["numeric_input_missing_or_invalid"])
    start = sp["end"] + timedelta(days=1)
    return dict(result, calculation_status="computed", output=decimal_text(output),
                output_unit=longer["canonical_unit"], currency=longer["currency"],
                period_start=start.isoformat(), period_end=lp["end"].isoformat(),
                period_duration_days=(lp["end"] - start).days + 1, reasons=[])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=Path, required=True,
                        help="JSONL records with new/prior or longer/shorter and operation")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--as-of")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Output already exists; choose a new revision path.")
    results = []
    for line in args.pairs.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        pair = json.loads(line)
        if pair.get("operation") == "ytd_difference":
            result = difference_ytd(pair["longer"], pair["shorter"])
        else:
            result = compare_claims(pair["new"], pair["prior"], pair.get("comparison_kind", "same_period"), args.as_of)
        result["pair_id"] = pair["pair_id"]
        results.append(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in results), encoding="utf-8")
    print(json.dumps({"records": len(results), "output": args.output.as_posix(), "version": VERSION}))


if __name__ == "__main__":
    main()
