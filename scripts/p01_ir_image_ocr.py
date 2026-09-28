"""Offline OCR of existing SK IR pages lacking text; original PDFs stay unchanged.

All rendered pages, OCR words and transcripts remain under NEW output/raw.
Public outputs contain page locations, hashes, counts and uncalibrated OCR scores.
"""
import argparse
import csv
import hashlib
import json
import re
import statistics
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import fitz
import pytesseract
from PIL import Image, ImageChops, ImageOps

ROOT = Path(__file__).resolve().parents[1]
VERSION = "p01-ir-image-ocr/0.1"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, data):
    fields = list(dict.fromkeys(key for row in data for key in row))
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fields or ["status"])
        writer.writeheader()
        writer.writerows(data)


def recognize(item):
    """Tesseract subprocesses may run concurrently; PDF rendering is sequential."""
    source = item["png_path"]
    attempts = []
    for psm in (11, 6):
        with Image.open(source) as image:
            data = pytesseract.image_to_data(image, lang="eng", config=f"--oem 3 --psm {psm}", output_type=pytesseract.Output.DICT, timeout=45)
        words, lines = [], {}
        for i, token in enumerate(data["text"]):
            if not token.strip():
                continue
            confidence = float(data["conf"][i])
            word = {"text": token, "confidence": confidence,
                    "pixel_bbox": [data["left"][i], data["top"][i], data["width"][i], data["height"][i]],
                    "block_number": data["block_num"][i], "paragraph_number": data["par_num"][i], "line_number": data["line_num"][i]}
            words.append(word)
            key = (word["block_number"], word["paragraph_number"], word["line_number"])
            lines.setdefault(key, []).append(token)
        text = "\n".join(" ".join(tokens) for tokens in lines.values())
        confidence = statistics.mean(w["confidence"] for w in words) if words else None
        attempts.append({"psm": psm, "words": words, "text": text, "mean_confidence": confidence})
        if words and confidence >= 40:
            break
    chosen = max(attempts, key=lambda result: (result["mean_confidence"] or -1, len(result["words"])))
    name = item["stem"] + ".ocr.json"
    private = {"doc_id": item["doc_id"], "revision_id": item["revision_id"], "pdf_page_number": item["pdf_page_number"],
               "dpi": item["dpi"], "offset_unit": "unicode_codepoint", "engine": VERSION,
               "selected_psm": chosen["psm"], "selection_basis": "first_sparse_attempt_unless_empty_or_mean_confidence_under_40_then_compare_mean_scores",
               "attempts": attempts, "text": chosen["text"], "status": "automatic_ocr_not_human_transcription"}
    with (source.parent / name).open("x", encoding="utf-8") as stream:
        json.dump(private, stream, ensure_ascii=False, indent=2)
    confidences = [word["confidence"] for word in chosen["words"]]
    result = {key: value for key, value in item.items() if key not in ("png_path", "stem")}
    result.update(ocr_status="recognized_pending_review" if chosen["words"] else "no_text_recognized_pending_review",
                  ocr_private_uri="raw/" + name, ocr_text_sha256=digest(chosen["text"].encode()),
                  ocr_chars=len(chosen["text"]), ocr_word_count=len(chosen["words"]), selected_psm=chosen["psm"], attempt_count=len(attempts),
                  mean_word_confidence=chosen["mean_confidence"], min_word_confidence=min(confidences) if confidences else None,
                  below_80_confidence_words=sum(value < 80 for value in confidences),
                  numeric_token_candidates=sum(bool(re.search(r"\d", word["text"])) for word in chosen["words"]),
                  bbox_within_render=all(0 <= w["pixel_bbox"][0] <= w["pixel_bbox"][0] + w["pixel_bbox"][2] <= item["render_width"] and 0 <= w["pixel_bbox"][1] <= w["pixel_bbox"][1] + w["pixel_bbox"][3] <= item["render_height"] for w in chosen["words"]),
                  human_transcription_status="pending", semantic_completeness="not_established")
    return result


def run(manifest_path, parser_path, output, executable, dpi=200, workers=2):
    if output.exists():
        raise ValueError("output_directory_must_be_new")
    if not executable.is_file():
        raise ValueError("tesseract_executable_missing")
    pytesseract.pytesseract.tesseract_cmd = str(executable)
    engine_version = str(pytesseract.get_tesseract_version())
    languages = pytesseract.get_languages(config="")
    if "eng" not in languages:
        raise ValueError("English_OCR_model_missing")
    records = [row for row in read_csv(manifest_path) if row["source_id"] == "SKH_IR"]
    expected = {row["doc_id"]: int(row["image_only_pages"]) for row in read_csv(parser_path)}
    output.mkdir(parents=True)
    (output / "raw").mkdir()
    (output / "raw/.gitignore").write_text("*\n", encoding="utf-8")
    jobs, preservation, documents = [], [], []
    for row in records:
        path = (ROOT / row["storage_uri"]).resolve()
        initial = digest(path.read_bytes())
        if initial != row["sha256"]:
            raise ValueError("input_PDF_hash_mismatch")
        selected = []
        with fitz.open(path) as document:
            for index, page in enumerate(document):
                native = page.get_text().strip()
                if native:
                    continue
                stem = row["doc_id"] + f"-p{index+1:03d}"
                target = output / "raw" / (stem + ".png")
                pixmap = page.get_pixmap(dpi=dpi, alpha=False)
                pixmap.save(target)
                selected.append(index + 1)
                jobs.append({"doc_id": row["doc_id"], "revision_id": row["revision_id"], "source_pdf_uri": row["storage_uri"],
                             "source_pdf_sha256": initial, "pdf_page_index": index, "pdf_page_number": index + 1,
                             "native_text_chars": len(native), "image_objects": len(page.get_images()),
                             "vector_drawings": len(page.get_drawings()), "pdf_page_width_points": page.rect.width,
                             "pdf_page_height_points": page.rect.height, "dpi": dpi, "render_width": pixmap.width,
                             "render_height": pixmap.height, "render_png_sha256": digest(target.read_bytes()),
                             "render_private_uri": "raw/" + target.name, "png_path": target, "stem": stem,
                             "page_kind_assessment": "unknown_not_assumed_divider"})
            documents.append({"doc_id": row["doc_id"], "total_pdf_pages": len(document), "existing_image_only_page_count": expected[row["doc_id"]],
                              "current_no_text_page_count": len(selected), "page_numbers": "|".join(map(str, selected)),
                              "count_agrees_with_existing_record": len(selected) == expected[row["doc_id"]]})
        preservation.append({"doc_id": row["doc_id"], "source_pdf_uri": row["storage_uri"], "sha256_before": initial})
    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = [(job, executor.submit(recognize, job)) for job in jobs]
        for job, future in future_map:
            try:
                results.append(future.result())
            except Exception as exc:
                failed = {key: value for key, value in job.items() if key not in ("png_path", "stem")}
                failed.update(ocr_status="ocr_failed", error_type=type(exc).__name__, human_transcription_status="pending", semantic_completeness="not_established")
                results.append(failed)
    for row in preservation:
        row["sha256_after"] = digest((ROOT / row["source_pdf_uri"]).read_bytes())
        row["unchanged"] = row["sha256_before"] == row["sha256_after"]
    write_csv(output / "page_manifest.csv", results)
    write_csv(output / "document_page_check.csv", documents)
    write_csv(output / "source_preservation.csv", preservation)
    summary = {"version": VERSION, "completed_at": datetime.now(timezone.utc).isoformat(), "script_sha256": digest(Path(__file__).read_bytes()),
               "engine": engine_version, "engine_executable_sha256": digest(executable.read_bytes()),
               "ocr_language": "eng", "available_languages": languages, "renderer": "PyMuPDF/" + fitz.VersionBind,
               "python_wrapper": "pytesseract/" + version("pytesseract"), "dpi": dpi,
               "input_PDF_documents": len(records), "expected_image_only_pages": sum(expected[r["doc_id"]] for r in records),
               "discovered_no_text_pages": len(jobs), "OCR_attempted_pages": len(results),
               "pages_with_OCR_words": sum(r["ocr_status"] == "recognized_pending_review" for r in results),
               "pages_without_OCR_words": sum(r["ocr_status"] == "no_text_recognized_pending_review" for r in results),
               "failed_pages": sum(r["ocr_status"] == "ocr_failed" for r in results),
               "OCR_word_candidates": sum(r.get("ocr_word_count", 0) for r in results),
               "original_PDFs_unchanged": all(r["unchanged"] for r in preservation),
               "human_transcription_verified_pages": 0, "semantic_completeness": "not_established",
               "no_external_document_transmission": True, "installed_new_dependencies": False,
               "limits": ["English model may miss non-English labels, logos, small print or low-contrast text.", "OCR confidence is uncalibrated and not a probability of transcription correctness.", "Only pages with zero native text were processed; other pages may contain unexamined raster details.", "Original PDF bytes and existing text blocks were not replaced."],
               "documentation": ["https://pymupdf.readthedocs.io/en/latest/recipes-images.html", "https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html"]}
    with (output / "summary.json").open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
    return summary


def comparative_run(baseline, output, executable):
    """Fixed preprocessing chosen on explicit sample tokens, never max confidence."""
    if output.exists():
        raise ValueError("output_directory_must_be_new")
    pytesseract.pytesseract.tesseract_cmd = str(executable)
    output.mkdir(parents=True)
    (output / "raw").mkdir()
    (output / "raw/.gitignore").write_text("*\n", encoding="utf-8")
    original_rows = read_csv(baseline / "page_manifest.csv")
    samples = {("SKH-2024Q1-IR", 3): (["financial", "results"], ["fy2024", "q1"]),
               ("SKH-2024Q4-IR", 15): (["new", "shareholder", "return", "policy"], ["fy25", "fy27"]),
               ("SKH-2026Q2-IR", 13): (["appendix"], ["fy2026", "q2"])}
    # Criteria are confined to private output; public records only boolean matches.
    (output / "raw/sample_criteria.json").write_text(json.dumps({f"{doc}:{page}": value for (doc, page), value in samples.items()}), encoding="utf-8")
    all_rows, private_results, checks = [], {}, []
    variants = ("original_sparse", "gray_half_sparse", "red_orange_mask_half_sparse")

    def process(row):
        key = (row["doc_id"], int(row["pdf_page_number"]))
        source_image = baseline / row["render_private_uri"]
        with Image.open(source_image) as source:
            half = source.convert("RGB").resize((source.width // 2, source.height // 2), Image.Resampling.LANCZOS)
            gray = ImageOps.autocontrast(ImageOps.grayscale(half), cutoff=1)
            red, green, blue = half.split()
            rg = ImageChops.subtract(red, green).point(lambda value: 255 if value >= 35 else 0)
            rb = ImageChops.subtract(red, blue).point(lambda value: 255 if value >= 40 else 0)
            bright_red = red.point(lambda value: 255 if value >= 90 else 0)
            mask = ImageOps.invert(ImageChops.multiply(ImageChops.multiply(rg, rb), bright_red))
            images = {"gray_half_sparse": gray, "red_orange_mask_half_sparse": mask}
            for variant in variants:
                stem = f"{key[0]}-p{key[1]:03d}-{variant}"
                if variant == "original_sparse":
                    old = json.loads((baseline / row["ocr_private_uri"]).read_text(encoding="utf-8"))
                    result = next(attempt for attempt in old["attempts"] if attempt["psm"] == 11)
                    image_uri, image_hash = str(source_image.relative_to(ROOT)) if source_image.is_absolute() else source_image.as_posix(), row["render_png_sha256"]
                    width, height = int(row["render_width"]), int(row["render_height"])
                else:
                    target = output / "raw" / (stem + ".png")
                    prepared = images[variant]
                    prepared.save(target)
                    data = pytesseract.image_to_data(prepared, lang="eng", config="--oem 3 --psm 11", output_type=pytesseract.Output.DICT, timeout=45)
                    words, lines = [], {}
                    for i, token in enumerate(data["text"]):
                        if not token.strip():
                            continue
                        word = {"text": token, "confidence": float(data["conf"][i]), "pixel_bbox": [data["left"][i], data["top"][i], data["width"][i], data["height"][i]], "block_number": data["block_num"][i], "paragraph_number": data["par_num"][i], "line_number": data["line_num"][i]}
                        words.append(word)
                        lines.setdefault((word["block_number"], word["paragraph_number"], word["line_number"]), []).append(token)
                    result = {"psm": 11, "words": words, "text": "\n".join(" ".join(tokens) for tokens in lines.values()), "mean_confidence": statistics.mean(w["confidence"] for w in words) if words else None}
                    image_uri, image_hash = "raw/" + target.name, digest(target.read_bytes())
                    width, height = prepared.size
                private = {"doc_id": key[0], "pdf_page_number": key[1], "variant": variant, "source_pdf_sha256": row["source_pdf_sha256"], "result": result, "status": "automatic_ocr_not_human_transcription"}
                private_path = output / "raw" / (stem + ".ocr.json")
                private_path.write_text(json.dumps(private, ensure_ascii=False, indent=2), encoding="utf-8")
                record = {"doc_id": key[0], "revision_id": row["revision_id"], "pdf_page_number": key[1], "source_pdf_uri": row["source_pdf_uri"], "source_pdf_sha256": row["source_pdf_sha256"], "variant": variant, "render_private_uri": image_uri, "render_uri_base": "repository" if variant == "original_sparse" else "output_directory", "render_sha256": image_hash, "render_width": width, "render_height": height, "ocr_private_uri": "raw/" + private_path.name, "ocr_text_sha256": digest(result["text"].encode()), "ocr_word_count": len(result["words"]), "ocr_chars": len(result["text"]), "mean_word_confidence": result["mean_confidence"], "below_80_confidence_words": sum(w["confidence"] < 80 for w in result["words"]), "below_40_confidence_words": sum(w["confidence"] < 40 for w in result["words"]), "bbox_within_render": all(0 <= w["pixel_bbox"][0] <= w["pixel_bbox"][0]+w["pixel_bbox"][2] <= width and 0 <= w["pixel_bbox"][1] <= w["pixel_bbox"][1]+w["pixel_bbox"][3] <= height for w in result["words"]), "human_transcription_status": "pending", "semantic_completeness": "not_established"}
                all_rows.append(record)
                private_results[(key, variant)] = result
                if key in samples:
                    normalized = re.sub(r"[^a-z0-9]", "", result["text"].lower())
                    title, period = samples[key]
                    checks.append({"doc_id": key[0], "pdf_page_number": key[1], "variant": variant, "major_title_matches_sample": all(token in normalized for token in title), "period_matches_sample": all(token in normalized for token in period), "assessment_basis": "explicit_visual_sample_token_checks_not_confidence", "review_actor": "AI_agent_not_human"})

    for row in original_rows:
        if (row["doc_id"], int(row["pdf_page_number"])) in samples:
            process(row)
    write_csv(output / "preview_checks.csv", checks)
    eligible = [variant for variant in variants[1:] if all(check["major_title_matches_sample"] and check["period_matches_sample"] for check in checks if check["variant"] == variant)]
    selected = eligible[-1] if eligible else None
    if selected:
        for row in original_rows:
            if (row["doc_id"], int(row["pdf_page_number"])) not in samples:
                process(row)
    write_csv(output / "variant_page_manifest.csv", all_rows)
    chosen = [row for row in all_rows if row["variant"] == selected]
    write_csv(output / "page_manifest.csv", chosen)
    preserved = [{"doc_id": row["doc_id"], "source_pdf_uri": row["source_pdf_uri"], "sha256_before": row["source_pdf_sha256"], "sha256_after": digest((ROOT / row["source_pdf_uri"]).read_bytes())} for row in {x["doc_id"]: x for x in original_rows}.values()]
    for row in preserved:
        row["unchanged"] = row["sha256_before"] == row["sha256_after"]
    write_csv(output / "source_preservation.csv", preserved)
    summary = {"version": VERSION + "/comparative", "completed_at": datetime.now(timezone.utc).isoformat(), "script_sha256": digest(Path(__file__).read_bytes()), "baseline_output": baseline.as_posix(), "engine": str(pytesseract.get_tesseract_version()), "ocr_language": "eng", "variants": list(variants), "visual_sample_pages": 3, "sample_all_title_and_period_matches": {variant: sum(check["major_title_matches_sample"] and check["period_matches_sample"] for check in checks if check["variant"] == variant) for variant in variants}, "selected_fixed_variant": selected, "selection_basis": "all_three_visual_sample_titles_and_period_tokens_must_match;prefer_color_isolation_if_both_new_variants_pass;not_max_confidence", "pages_processed": len({(row["doc_id"], row["pdf_page_number"]) for row in all_rows}), "variant_page_records": len(all_rows), "selected_variant_pages": len(chosen), "OCR_word_candidates": sum(row["ocr_word_count"] for row in chosen), "below_80_confidence_words": sum(row["below_80_confidence_words"] for row in chosen), "below_40_confidence_words": sum(row["below_40_confidence_words"] for row in chosen), "original_PDFs_unchanged": all(row["unchanged"] for row in preserved), "human_verified_pages": 0, "semantic_completeness": "not_established", "limits": ["Color isolation can delete non-red text, black labels and small Korean slogans; all variants are retained.", "Three sample token checks do not establish exact transcription or correctness of all 31 pages.", "Confidence is not a probability of correctness; numeric-looking tokens are not verified numerical evidence.", "Only pages with zero native text were processed."], "no_external_OCR_service": True}
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "artifacts/p0/document_manifest.csv")
    parser.add_argument("--parser-trials", type=Path, default=ROOT / "artifacts/p0/parser_trials.csv")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--tesseract", type=Path, default=Path("C:/Program Files/Tesseract-OCR/tesseract.exe"))
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--baseline-output", type=Path, help="Run fixed preprocessing comparison against preserved baseline output")
    args = parser.parse_args()
    if args.baseline_output:
        result = comparative_run(args.baseline_output, args.output_dir, args.tesseract)
        print(json.dumps({key: result[key] for key in ("pages_processed", "selected_fixed_variant", "sample_all_title_and_period_matches", "OCR_word_candidates", "original_PDFs_unchanged")}))
    else:
        result = run(args.manifest, args.parser_trials, args.output_dir, args.tesseract, args.dpi)
        print(json.dumps({key: result[key] for key in ("input_PDF_documents", "discovered_no_text_pages", "OCR_attempted_pages", "pages_with_OCR_words", "failed_pages", "OCR_word_candidates", "original_PDFs_unchanged")}))
